from __future__ import annotations

import fnmatch
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Literal, Optional, Union

import httpx

from .errors import QueryLakeAPIError, QueryLakeHTTPStatusError, QueryLakeTransportError
from .models import (
    BackendConnectivitySummary,
    CapabilitiesSummary,
    HybridSearchOptions,
    ProfileBringupSummary,
    ReadyzSummary,
    ProfileDiagnosticsSummary,
    ProjectionDiagnosticsSummary,
    ProjectionPlanExplainSummary,
    ProjectionRefreshExecutionReportSummary,
    RetrievalPlanExplainSummary,
    SearchResultChunk,
    UploadDirectoryOptions,
    parse_capabilities_summary,
    parse_profile_bringup_summary,
    parse_profile_diagnostics_summary,
    parse_readyz_summary,
    parse_projection_diagnostics_summary,
    parse_projection_plan_explain_summary,
    parse_projection_refresh_execution_report_summary,
    parse_retrieval_plan_explain_summary,
)

AuthOverride = Union[Dict[str, str], Literal[False], None]


def _normalize_base_url(base_url: str) -> str:
    value = (base_url or "").strip()
    if not value:
        raise ValueError("base_url must be a non-empty URL")
    return value.rstrip("/")


def _api_function_path(function_name: str) -> str:
    cleaned = (function_name or "").strip().strip("/")
    if not cleaned:
        raise ValueError("function_name must be non-empty")
    if cleaned.startswith("api/"):
        return f"/{cleaned}"
    return f"/api/{cleaned}"


def _ensure_http_success(response: httpx.Response) -> None:
    if 200 <= response.status_code < 300:
        return
    body = response.text
    raise QueryLakeHTTPStatusError(
        status_code=response.status_code,
        url=str(response.request.url),
        body=body[:2000],
    )


def _extract_api_result(function_name: str, payload: Any) -> Any:
    if not isinstance(payload, dict) or "success" not in payload:
        return payload

    if payload.get("success") is False:
        raise QueryLakeAPIError(
            function_name=function_name,
            message=str(payload.get("error") or payload.get("note") or "Unknown API error"),
            trace=(payload.get("trace") if isinstance(payload.get("trace"), str) else None),
            payload=payload,
        )

    if "result" in payload:
        return payload["result"]

    remainder = {k: v for k, v in payload.items() if k != "success"}
    if remainder:
        return remainder
    return None


def _selection_sha256(paths: Iterable[Union[str, Path]]) -> str:
    normalized = [str(Path(value).expanduser().resolve()) for value in paths]
    normalized.sort()
    blob = "\n".join(normalized).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _file_sha256(path: Union[str, Path]) -> str:
    resolved = Path(path).expanduser().resolve()
    hasher = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class QueryLakeClient:
    """Synchronous QueryLake SDK client."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 60.0,
        auth: Optional[Dict[str, str]] = None,
        oauth2: Optional[str] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self._auth: Dict[str, str] = {}
        self.set_auth(auth=auth, oauth2=oauth2, api_key=api_key)
        self._client = httpx.Client(
            base_url=self.base_url,
            timeout=float(timeout_seconds),
            headers=headers or {},
        )

    @classmethod
    def from_env(cls) -> "QueryLakeClient":
        return cls(
            base_url=os.getenv("QUERYLAKE_BASE_URL", "http://127.0.0.1:8000"),
            oauth2=os.getenv("QUERYLAKE_OAUTH2"),
            api_key=os.getenv("QUERYLAKE_API_KEY"),
            timeout_seconds=float(os.getenv("QUERYLAKE_TIMEOUT_SECONDS", "60")),
        )

    def set_auth(
        self,
        *,
        auth: Optional[Dict[str, str]] = None,
        oauth2: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        if auth is not None:
            self._auth = dict(auth)
            return
        if oauth2:
            self._auth = {"oauth2": oauth2}
            return
        if api_key:
            self._auth = {"api_key": api_key}
            return
        self._auth = {}

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "QueryLakeClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def _resolve_auth(self, auth_override: AuthOverride) -> Optional[Dict[str, str]]:
        if auth_override is False:
            return None
        if isinstance(auth_override, dict):
            return auth_override
        if self._auth:
            return self._auth
        return None

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise QueryLakeTransportError(str(exc)) from exc
        _ensure_http_success(response)
        return response

    def api(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        method: Literal["POST", "GET"] = "POST",
        auth: AuthOverride = None,
    ) -> Any:
        body = dict(payload or {})
        resolved_auth = self._resolve_auth(auth)
        if resolved_auth and "auth" not in body:
            body["auth"] = resolved_auth
        response = self._request(method, _api_function_path(function_name), json=body)
        return _extract_api_result(function_name, response.json())

    def healthz(self) -> Dict[str, Any]:
        return self._request("GET", "/healthz").json()

    def readyz(self) -> Dict[str, Any]:
        return self._request("GET", "/readyz").json()

    def readyz_summary(self) -> ReadyzSummary:
        return parse_readyz_summary(self.readyz())

    def capabilities(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/capabilities").json()

    def kernel_capabilities(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/kernel/capabilities").json()

    def capabilities_summary(self) -> CapabilitiesSummary:
        return parse_capabilities_summary(self.capabilities())

    def support_state(self, capability_id: str) -> Optional[str]:
        return self.capabilities_summary().support_state(capability_id)

    def supports(self, capability_id: str, *, allow_degraded: bool = True) -> bool:
        return self.capabilities_summary().is_available(capability_id, allow_degraded=allow_degraded)

    def representation_scopes(self) -> Dict[str, Any]:
        summary = self.capabilities_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    def route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = self.capabilities_summary()
        payload: Dict[str, Any] = {}
        for entry in summary.route_support_v2:
            payload[entry.route_id] = {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
        return payload

    def route_representation_scope_id_from_capabilities(self, route_id: str) -> Optional[str]:
        return self.capabilities_summary().route_representation_scope_id(route_id)

    def route_capability_dependencies_from_capabilities(self, route_id: str) -> List[str]:
        return self.capabilities_summary().route_capability_dependencies(route_id)

    def route_declared_executable_from_capabilities(self, route_id: str) -> bool:
        entry = self.capabilities_summary().route_support_manifest_v2_entry(route_id)
        return bool(entry is not None and entry.declared_executable)

    def route_declared_optional_from_capabilities(self, route_id: str) -> bool:
        entry = self.capabilities_summary().route_support_manifest_v2_entry(route_id)
        return bool(entry is not None and entry.declared_optional)

    def diagnostics_representation_scopes(self) -> Dict[str, Any]:
        summary = self.profile_diagnostics_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    def diagnostics_route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = self.profile_diagnostics_summary()
        return {
            entry.route_id: {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope_id": entry.representation_scope_id(),
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
            for entry in summary.route_support_v2
        }

    def route_planning_v2(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_diagnostics_summary().route_executor(route_id)
        if entry is None:
            return {}
        return dict(entry.planning_v2)

    def route_query_ir_v2_template(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_diagnostics_summary().route_executor(route_id)
        if entry is None:
            return {}
        return entry.query_ir_v2_template()

    def route_projection_ir_v2(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_diagnostics_summary().route_executor(route_id)
        if entry is None:
            return {}
        return entry.projection_ir_v2()

    def profile_diagnostics(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/profile-diagnostics").json()

    def kernel_profile_diagnostics(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/kernel/profile-diagnostics").json()

    def projection_diagnostics(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/projection-diagnostics").json()

    def kernel_projection_diagnostics(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/kernel/projection-diagnostics").json()

    def profile_bringup(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/profile-bringup").json()

    def kernel_profile_bringup(self) -> Dict[str, Any]:
        return self._request("GET", "/v2/kernel/profile-bringup").json()

    def projection_diagnostics_summary(self) -> ProjectionDiagnosticsSummary:
        return parse_projection_diagnostics_summary(self.projection_diagnostics())

    def profile_bringup_summary(self) -> ProfileBringupSummary:
        return parse_profile_bringup_summary(self.profile_bringup())

    def kernel_profile_bringup_summary(self) -> ProfileBringupSummary:
        return parse_profile_bringup_summary(self.kernel_profile_bringup())

    def bringup_representation_scopes(self) -> Dict[str, Any]:
        summary = self.profile_bringup_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    def bringup_route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = self.profile_bringup_summary()
        return {
            entry.route_id: {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope_id": entry.representation_scope_id(),
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
            for entry in summary.route_support_v2
        }

    def bringup_bootstrap_command(self) -> Optional[str]:
        return self.profile_bringup_summary().bootstrap_command()

    def bringup_next_actions(self) -> List[Dict[str, Any]]:
        return [
            {
                "kind": action.kind,
                "priority": action.priority,
                "summary": action.summary,
                "details": action.details,
                "command": action.command,
                "docs_ref": action.docs_ref,
                "plane": action.plane,
                "route_id": action.route_id,
                "backend": action.backend,
                "blocker_kinds": list(action.blocker_kinds),
                "projection_ids": list(action.projection_ids),
            }
            for action in self.profile_bringup_summary().highest_priority_actions()
        ]

    def bringup_backend_targets(self) -> List[Dict[str, Any]]:
        return [
            {
                "plane": entry.plane,
                "backend": entry.backend,
                "status": entry.status,
                "checked": entry.checked,
                "checked_at": entry.checked_at,
                "required": entry.required,
                "database_url_env": entry.database_url_env,
                "env_var": entry.env_var,
                "endpoint": entry.endpoint,
                "status_code": entry.status_code,
                "detail": entry.detail,
            }
            for entry in self.profile_bringup_summary().backend_targets
        ]

    def bringup_lexical_degraded_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().lexical_degraded_route_ids)

    def bringup_lexical_gold_recommended_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().lexical_gold_recommended_route_ids)

    def bringup_declared_route_support(self) -> Dict[str, str]:
        return dict(self.profile_bringup_summary().declared_route_support)

    def bringup_route_declared_executable(self, route_id: str) -> bool:
        return self.profile_bringup_summary().route_declared_executable(route_id)

    def bringup_route_declared_optional(self, route_id: str) -> bool:
        return self.profile_bringup_summary().route_declared_optional(route_id)

    def bringup_route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().route_required_projection_descriptor_ids(route_id)

    def bringup_declared_executable_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().declared_executable_route_ids)

    def bringup_declared_optional_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().declared_optional_route_ids)

    def bringup_declared_runtime_ready_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().declared_executable_runtime_ready_ids)

    def bringup_declared_runtime_blocked_routes(self) -> List[str]:
        return list(self.profile_bringup_summary().declared_executable_runtime_blocked_ids)

    def bringup_declared_routes_runtime_ready(self) -> bool:
        return self.profile_bringup_summary().declared_routes_runtime_ready()

    def bringup_route_recovery(self) -> List[Dict[str, Any]]:
        return [
            {
                "route_id": entry.route_id,
                "implemented": entry.implemented,
                "support_state": entry.support_state,
                "runtime_ready": entry.runtime_ready,
                "projection_ready": entry.projection_ready,
                "planning_v2": dict(entry.planning_v2),
                "query_ir_v2": entry.query_ir_v2_template(),
                "projection_ir_v2": entry.projection_ir_v2(),
                "blocker_kinds": list(entry.blocker_kinds),
                "bootstrapable_blocking_projection_ids": list(entry.bootstrapable_blocking_projection_ids),
                "nonbootstrapable_blocking_projection_ids": list(entry.nonbootstrapable_blocking_projection_ids),
                "bootstrap_command": entry.bootstrap_command,
                "lexical_support_class": entry.lexical_support_class,
                "gold_recommended_for_exact_constraints": entry.gold_recommended_for_exact_constraints,
                "exact_constraint_degraded_capabilities": list(entry.exact_constraint_degraded_capabilities),
                "exact_constraint_unsupported_capabilities": list(entry.exact_constraint_unsupported_capabilities),
            }
            for entry in self.profile_bringup_summary().route_recovery
        ]

    def bringup_route_recovery_entry(self, route_id: str) -> Optional[Dict[str, Any]]:
        entry = self.profile_bringup_summary().route_recovery_entry(route_id)
        if entry is None:
            return None
        return {
            "route_id": entry.route_id,
            "implemented": entry.implemented,
            "support_state": entry.support_state,
            "runtime_ready": entry.runtime_ready,
            "projection_ready": entry.projection_ready,
            "planning_v2": dict(entry.planning_v2),
            "query_ir_v2": entry.query_ir_v2_template(),
            "projection_ir_v2": entry.projection_ir_v2(),
            "blocker_kinds": list(entry.blocker_kinds),
            "bootstrapable_blocking_projection_ids": list(entry.bootstrapable_blocking_projection_ids),
            "nonbootstrapable_blocking_projection_ids": list(entry.nonbootstrapable_blocking_projection_ids),
            "bootstrap_command": entry.bootstrap_command,
            "lexical_support_class": entry.lexical_support_class,
            "gold_recommended_for_exact_constraints": entry.gold_recommended_for_exact_constraints,
            "exact_constraint_degraded_capabilities": list(entry.exact_constraint_degraded_capabilities),
            "exact_constraint_unsupported_capabilities": list(entry.exact_constraint_unsupported_capabilities),
        }

    def bringup_route_planning_v2(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_bringup_summary().route_recovery_entry(route_id)
        if entry is None:
            return {}
        return dict(entry.planning_v2)

    def bringup_route_query_ir_v2_template(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_bringup_summary().route_recovery_entry(route_id)
        if entry is None:
            return {}
        return entry.query_ir_v2_template()

    def bringup_route_projection_ir_v2(self, route_id: str) -> Dict[str, Any]:
        entry = self.profile_bringup_summary().route_recovery_entry(route_id)
        if entry is None:
            return {}
        return entry.projection_ir_v2()

    def local_support_matrix(self) -> List[Dict[str, Any]]:
        return self.profile_diagnostics_summary().local_support_matrix()

    def local_profile_maturity(self) -> Optional[str]:
        return self.profile_bringup_summary().local_profile_maturity()

    def local_promotion_status(self) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_promotion_status()

    def local_scope_expansion_status(self) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_scope_expansion_status()

    def local_scope_expansion_contract(self) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_scope_expansion_contract()

    def local_route_support_entry(self, route_id: str) -> Dict[str, Any]:
        return self.profile_diagnostics_summary().local_route_support_entry(route_id)

    def local_route_representation_scope_id(self, route_id: str) -> Optional[str]:
        return self.profile_diagnostics_summary().local_route_representation_scope_id(route_id)

    def local_route_declared_executable(self, route_id: str) -> bool:
        return self.profile_diagnostics_summary().local_route_declared_executable(route_id)

    def local_dense_sidecar(self) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_dense_sidecar()

    def local_dense_sidecar_contract(self) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_dense_sidecar_contract()

    def local_dense_sidecar_contract_version(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_contract_version()

    def local_dense_sidecar_lifecycle_contract_version(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_lifecycle_contract_version()

    def local_dense_sidecar_ready(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_ready()

    def local_dense_sidecar_ready_state_source(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_ready_state_source()

    def local_dense_sidecar_stats_source(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_stats_source()

    def local_dense_sidecar_cache_lifecycle_state(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_cache_lifecycle_state()

    def local_dense_sidecar_rebuildable_from_projection_records(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_rebuildable_from_projection_records()

    def local_dense_sidecar_requires_process_warmup(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_requires_process_warmup()

    def local_dense_sidecar_warmup_recommended(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_warmup_recommended()

    def local_dense_sidecar_warmup_required_for_peak_performance(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_warmup_required_for_peak_performance()

    def local_dense_sidecar_cold_start_recoverable(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_cold_start_recoverable()

    def local_dense_sidecar_cache_persistence_mode(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_cache_persistence_mode()

    def local_dense_sidecar_lifecycle_recovery_mode(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_lifecycle_recovery_mode()

    def local_dense_sidecar_lifecycle_recovery_hints(self) -> List[str]:
        return self.profile_bringup_summary().local_dense_sidecar_lifecycle_recovery_hints()

    def local_dense_sidecar_warmup_target_route_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_dense_sidecar_warmup_target_route_ids()

    def local_dense_sidecar_warmup_command_hint(self) -> Optional[str]:
        return self.profile_bringup_summary().local_dense_sidecar_warmup_command_hint()

    def local_dense_sidecar_persisted_projection_state_available(self) -> bool:
        return self.profile_bringup_summary().local_dense_sidecar_persisted_projection_state_available()

    def local_projection_plan_v2_registry(self) -> List[Dict[str, Any]]:
        return self.profile_bringup_summary().local_projection_plan_v2_registry()

    def local_projection_plan_v2(self, projection_id: str) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_projection_plan_v2(projection_id)

    def local_route_runtime_contract(self, route_id: str) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_route_runtime_contract(route_id)

    def local_route_runtime_ready(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_runtime_ready(route_id)

    def local_route_required_projection_ids(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().local_route_required_projection_ids(route_id)

    def local_route_capability_dependencies(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().local_route_capability_dependencies(route_id)

    def local_route_representation_scope(self, route_id: str) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_route_representation_scope(route_id)

    def local_route_lexical_support_class(self, route_id: str) -> Optional[str]:
        return self.profile_bringup_summary().local_route_lexical_support_class(route_id)

    def local_route_requires_dense_sidecar(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_requires_dense_sidecar(route_id)

    def local_route_dense_sidecar_ready(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_ready(route_id)

    def local_route_dense_sidecar_cache_warmed(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_cache_warmed(route_id)

    def local_route_dense_sidecar_indexed_record_count(self, route_id: str) -> int:
        return self.profile_bringup_summary().local_route_dense_sidecar_indexed_record_count(route_id)

    def local_route_dense_sidecar_contract(self, route_id: str) -> Dict[str, Any]:
        return self.profile_bringup_summary().local_route_dense_sidecar_contract(route_id)

    def local_route_dense_sidecar_ready_state_source(self, route_id: str) -> Optional[str]:
        return self.profile_bringup_summary().local_route_dense_sidecar_ready_state_source(route_id)

    def local_route_dense_sidecar_stats_source(self, route_id: str) -> Optional[str]:
        return self.profile_bringup_summary().local_route_dense_sidecar_stats_source(route_id)

    def local_route_dense_sidecar_cache_lifecycle_state(self, route_id: str) -> Optional[str]:
        return self.profile_bringup_summary().local_route_dense_sidecar_cache_lifecycle_state(route_id)

    def local_route_dense_sidecar_rebuildable_from_projection_records(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_rebuildable_from_projection_records(route_id)

    def local_route_dense_sidecar_requires_process_warmup(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_requires_process_warmup(route_id)

    def local_route_dense_sidecar_warmup_recommended(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_warmup_recommended(route_id)

    def local_route_dense_sidecar_warmup_required_for_peak_performance(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_warmup_required_for_peak_performance(route_id)

    def local_route_dense_sidecar_lifecycle_recovery_mode(self, route_id: str) -> Optional[str]:
        return self.profile_bringup_summary().local_route_dense_sidecar_lifecycle_recovery_mode(route_id)

    def local_route_dense_sidecar_lifecycle_recovery_hints(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().local_route_dense_sidecar_lifecycle_recovery_hints(route_id)

    def local_route_dense_sidecar_persisted_projection_state_available(self, route_id: str) -> bool:
        return self.profile_bringup_summary().local_route_dense_sidecar_persisted_projection_state_available(route_id)

    def local_declared_executable_route_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_declared_executable_route_ids()

    def local_declared_runtime_ready_route_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_declared_runtime_ready_route_ids()

    def local_declared_runtime_blocked_route_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_declared_runtime_blocked_route_ids()

    def local_required_projection_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_required_projection_ids()

    def local_representation_scope_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_representation_scope_ids()

    def local_current_supported_slice_frozen(self) -> bool:
        return self.profile_bringup_summary().local_current_supported_slice_frozen()

    def local_scope_expansion_pending_for_wider_scope(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_pending_for_wider_scope()

    def local_scope_expansion_required_now(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_required_now()

    def local_scope_expansion_satisfied_now(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_satisfied_now()

    def local_scope_expansion_future_scope_candidates(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_future_scope_candidates()

    def local_scope_expansion_docs_ref(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_docs_ref()

    def local_scope_expansion_contract_docs_ref(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_contract_docs_ref()

    def local_scope_expansion_contract_version(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_contract_version()

    def local_scope_expansion_lifecycle_contract_version(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_lifecycle_contract_version()

    def local_scope_expansion_lifecycle_state(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_lifecycle_state()

    def local_scope_expansion_cache_lifecycle_state(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_cache_lifecycle_state()

    def local_scope_expansion_dense_sidecar_promotion_contract_ready(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_dense_sidecar_promotion_contract_ready()

    def local_scope_expansion_required_before_widening(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_required_before_widening()

    def local_scope_expansion_rebuildable_from_projection_records(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_rebuildable_from_projection_records()

    def local_scope_expansion_requires_process_warmup(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_requires_process_warmup()

    def local_scope_expansion_warmup_recommended(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_warmup_recommended()

    def local_scope_expansion_warmup_required_for_peak_performance(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_warmup_required_for_peak_performance()

    def local_scope_expansion_cold_start_recoverable(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_cold_start_recoverable()

    def local_scope_expansion_cache_persistence_mode(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_cache_persistence_mode()

    def local_scope_expansion_lifecycle_recovery_mode(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_lifecycle_recovery_mode()

    def local_scope_expansion_lifecycle_recovery_hints(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_lifecycle_recovery_hints()

    def local_scope_expansion_warmup_target_route_ids(self) -> List[str]:
        return self.profile_bringup_summary().local_scope_expansion_warmup_target_route_ids()

    def local_scope_expansion_warmup_command_hint(self) -> Optional[str]:
        return self.profile_bringup_summary().local_scope_expansion_warmup_command_hint()

    def local_scope_expansion_persisted_projection_state_available(self) -> bool:
        return self.profile_bringup_summary().local_scope_expansion_persisted_projection_state_available()

    def route_prefers_gold_for_exact_constraints(self, route_id: str) -> bool:
        return self.profile_bringup_summary().route_prefers_gold_for_exact_constraints(route_id)

    def route_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().route_exact_constraint_degraded_capabilities(route_id)

    def route_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        return self.profile_bringup_summary().route_exact_constraint_unsupported_capabilities(route_id)

    def bringup_projection_status_buckets(self) -> Dict[str, List[str]]:
        summary = self.profile_bringup_summary()
        return {
            "ready": list(summary.ready_projection_ids),
            "building": list(summary.projection_building_ids),
            "failed": list(summary.projection_failed_ids),
            "stale": list(summary.projection_stale_ids),
            "absent": list(summary.projection_absent_ids),
        }

    def bringup_recommended_projection_status_buckets(self) -> Dict[str, List[str]]:
        summary = self.profile_bringup_summary()
        return {
            "ready": list(summary.recommended_ready_projection_ids),
            "needs_build": list(summary.recommended_projection_ids_needing_build),
            "all": list(summary.recommended_projection_ids),
        }

    def projection_plan_explain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/projection-plan/explain", json=payload).json()

    def kernel_projection_plan_explain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v2/kernel/projection-plan/explain", json=payload).json()

    def projection_plan_explain_summary(self, payload: Dict[str, Any]) -> ProjectionPlanExplainSummary:
        return parse_projection_plan_explain_summary(self.projection_plan_explain(payload))

    def projection_refresh_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v1/projection-refresh/run", json=payload).json()

    def kernel_projection_refresh_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("POST", "/v2/kernel/projection-refresh/run", json=payload).json()

    def projection_refresh_run_summary(self, payload: Dict[str, Any]) -> ProjectionRefreshExecutionReportSummary:
        return parse_projection_refresh_execution_report_summary(self.projection_refresh_run(payload))

    def projection_ids_needing_build(self, *, allow_degraded: bool = True) -> List[str]:
        return self.projection_diagnostics_summary().projection_ids_needing_build(allow_degraded=allow_degraded)

    def profile_diagnostics_summary(self) -> ProfileDiagnosticsSummary:
        return parse_profile_diagnostics_summary(self.profile_diagnostics())

    def kernel_profile_diagnostics_summary(self) -> ProfileDiagnosticsSummary:
        return parse_profile_diagnostics_summary(self.kernel_profile_diagnostics())

    def route_support_state(self, route_id: str) -> Optional[str]:
        return self.profile_diagnostics_summary().route_support_state(route_id)

    def route_executable(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return self.profile_diagnostics_summary().route_executable(route_id, allow_degraded=allow_degraded)

    def route_projection_ready(self, route_id: str) -> bool:
        return self.profile_diagnostics_summary().route_projection_ready(route_id)

    def route_projection_missing_descriptors(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_projection_missing_descriptors(route_id)

    def route_runtime_ready(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return self.profile_diagnostics_summary().route_runtime_ready(route_id, allow_degraded=allow_degraded)

    def route_state(self, route_id: str, *, allow_degraded: bool = True) -> str:
        return self.profile_diagnostics_summary().route_state(route_id, allow_degraded=allow_degraded)

    def route_is_degraded(self, route_id: str) -> bool:
        return self.profile_diagnostics_summary().route_is_degraded(route_id)

    def route_blocked_by_projection(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return self.profile_diagnostics_summary().route_blocked_by_projection(route_id, allow_degraded=allow_degraded)

    def route_blocked_by_backend_connectivity(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return self.profile_diagnostics_summary().route_blocked_by_backend_connectivity(route_id, allow_degraded=allow_degraded)

    def route_blocker_kinds(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_blocker_kinds(route_id)

    def route_blocking_projection_ids(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_blocking_projection_ids(route_id)

    def route_lane_backends(self, route_id: str) -> Dict[str, str]:
        return self.profile_diagnostics_summary().route_lane_backends(route_id)

    def route_adapter_ids(self, route_id: str) -> Dict[str, str]:
        return self.profile_diagnostics_summary().route_adapter_ids(route_id)

    def route_projection_targets(self, route_id: str) -> List[Dict[str, Any]]:
        return self.profile_diagnostics_summary().route_projection_targets(route_id)

    def route_projection_target_backend_names(self, route_id: str) -> Dict[str, str]:
        return self.profile_diagnostics_summary().route_projection_target_backend_names(route_id)

    def route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_required_projection_descriptor_ids(route_id)

    def route_declared_executable(self, route_id: str) -> bool:
        return self.profile_diagnostics_summary().route_declared_executable(route_id)

    def route_declared_optional(self, route_id: str) -> bool:
        return self.profile_diagnostics_summary().route_declared_optional(route_id)

    def route_lexical_semantics(self, route_id: str) -> Dict[str, Any]:
        return self.profile_diagnostics_summary().route_lexical_semantics(route_id)

    def route_lexical_support_class(self, route_id: str) -> Optional[str]:
        return self.profile_diagnostics_summary().route_lexical_support_class(route_id)

    def route_lexical_capability_states(self, route_id: str) -> Dict[str, str]:
        return self.profile_diagnostics_summary().route_lexical_capability_states(route_id)

    def route_lexical_degraded_capabilities(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_lexical_degraded_capabilities(route_id)

    def route_lexical_unsupported_capabilities(self, route_id: str) -> List[str]:
        return self.profile_diagnostics_summary().route_lexical_unsupported_capabilities(route_id)

    def route_gold_recommended_for_exact_constraints(self, route_id: str) -> bool:
        route = self.profile_diagnostics_summary().route_executor(route_id)
        if route is None:
            return False
        return route.gold_recommended_for_exact_constraints()

    def route_lexical_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        route = self.profile_diagnostics_summary().route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_degraded_capabilities()

    def route_lexical_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        route = self.profile_diagnostics_summary().route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_unsupported_capabilities()

    def route_summary(self) -> Dict[str, Any]:
        summary = self.profile_diagnostics_summary().route_summary_payload()
        return {
            "inspected_route_count": summary.inspected_route_count,
            "executable_route_count": summary.executable_route_count,
            "runtime_ready_route_count": summary.runtime_ready_route_count,
            "projection_blocked_route_count": summary.projection_blocked_route_count,
            "runtime_blocked_route_count": summary.runtime_blocked_route_count,
            "compatibility_projection_route_count": summary.compatibility_projection_route_count,
            "canonical_projection_route_count": summary.canonical_projection_route_count,
            "support_state_counts": dict(summary.support_state_counts),
            "blocker_kind_counts": dict(summary.blocker_kind_counts),
            "executable_route_ids": list(summary.executable_route_ids),
            "runtime_ready_route_ids": list(summary.runtime_ready_route_ids),
            "projection_blocked_route_ids": list(summary.projection_blocked_route_ids),
            "runtime_blocked_route_ids": list(summary.runtime_blocked_route_ids),
            "compatibility_projection_route_ids": list(summary.compatibility_projection_route_ids),
            "canonical_projection_route_ids": list(summary.canonical_projection_route_ids),
        }

    def runtime_blocker_summary(self) -> Dict[str, int]:
        return self.profile_diagnostics_summary().runtime_blocker_summary()

    def projection_blocked_routes(self, *, allow_degraded: bool = True) -> List[str]:
        return [
            entry.route_id
            for entry in self.profile_diagnostics_summary().projection_blocked_routes(allow_degraded=allow_degraded)
        ]

    def runtime_blocked_routes(self, *, allow_degraded: bool = True) -> List[str]:
        return [
            entry.route_id
            for entry in self.profile_diagnostics_summary().runtime_blocked_routes(allow_degraded=allow_degraded)
        ]

    def backend_connectivity_status(self, plane: str) -> Optional[str]:
        return self.profile_diagnostics_summary().backend_connectivity_status(plane)

    def backend_connectivity_entry(self, plane: str) -> Optional[BackendConnectivitySummary]:
        return self.profile_diagnostics_summary().backend_connectivity_entry(plane)

    def backend_connectivity_entries(self) -> Dict[str, BackendConnectivitySummary]:
        return self.profile_diagnostics_summary().backend_connectivity_entries()

    def ping(self) -> Any:
        return self.api("ping", method="GET", auth=False)

    def list_models(self) -> Dict[str, Any]:
        return self._request("GET", "/v1/models").json()

    def chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._request("POST", "/v1/chat/completions", json=payload)
        return response.json()

    def embeddings(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = self._request("POST", "/v1/embeddings", json=payload)
        return response.json()

    def login(self, *, username: str, password: str) -> Dict[str, Any]:
        result = self.api(
            "login",
            {"auth": {"username": username, "password": password}},
            auth=False,
        )
        if isinstance(result, dict) and isinstance(result.get("auth"), str):
            self.set_auth(oauth2=result["auth"])
        return result

    def add_user(self, *, username: str, password: str) -> Dict[str, Any]:
        result = self.api("add_user", {"username": username, "password": password}, auth=False)
        if isinstance(result, dict) and isinstance(result.get("auth"), str):
            self.set_auth(oauth2=result["auth"])
        return result

    def create_collection(
        self,
        *,
        name: str,
        description: Optional[str] = None,
        public: bool = False,
        organization_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "name": name,
            "public": bool(public),
        }
        if description is not None:
            payload["description"] = description
        if organization_id is not None:
            payload["organization_id"] = int(organization_id)
        return self.api("create_document_collection", payload)

    def list_collections(
        self,
        *,
        organization_id: Optional[int] = None,
        global_collections: bool = False,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"global_collections": bool(global_collections)}
        if organization_id is not None:
            payload["organization_id"] = int(organization_id)
        return self.api("fetch_document_collections_belonging_to", payload)

    def fetch_collection(self, *, collection_hash_id: Union[str, int]) -> Dict[str, Any]:
        return self.api("fetch_collection", {"collection_hash_id": str(collection_hash_id)})

    def modify_collection(
        self,
        *,
        collection_hash_id: Union[str, int],
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Any:
        payload: Dict[str, Any] = {"collection_hash_id": str(collection_hash_id)}
        if title is not None:
            payload["title"] = title
        if description is not None:
            payload["description"] = description
        return self.api("modify_document_collection", payload)

    def list_collection_documents(
        self,
        *,
        collection_hash_id: Union[str, int],
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        return self.api(
            "fetch_collection_documents",
            {
                "collection_hash_id": str(collection_hash_id),
                "limit": int(limit),
                "offset": int(offset),
            },
        )

    def fetch_document(
        self,
        *,
        document_hash_id: Union[str, int],
        get_chunk_count: bool = False,
    ) -> Dict[str, Any]:
        return self.api(
            "fetch_document",
            {
                "document_id": str(document_hash_id),
                "get_chunk_count": bool(get_chunk_count),
            },
        )

    def delete_document(self, *, document_hash_id: Union[str, int]) -> Any:
        return self.api("delete_document", {"hash_id": str(document_hash_id)})

    def upload_document(
        self,
        *,
        file_path: Union[str, Path],
        collection_hash_id: Union[str, int],
        scan_text: bool = True,
        create_embeddings: bool = True,
        create_sparse_embeddings: bool = False,
        sparse_embedding_function: str = "embedding_sparse",
        sparse_embedding_dimensions: int = 1024,
        enforce_sparse_dimension_match: bool = True,
        await_embedding: bool = False,
        document_metadata: Optional[Dict[str, Any]] = None,
        idempotency_key: Optional[str] = None,
        auth: AuthOverride = None,
    ) -> Dict[str, Any]:
        resolved_auth = self._resolve_auth(auth)
        if resolved_auth is None:
            raise ValueError("upload_document requires auth. Set oauth2/api_key on client or pass auth=...")
        path = Path(file_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File not found: {path}")

        params_payload: Dict[str, Any] = {
            "auth": resolved_auth,
            "collection_hash_id": str(collection_hash_id),
            "scan_text": bool(scan_text),
            "create_embeddings": bool(create_embeddings),
            "create_sparse_embeddings": bool(create_sparse_embeddings),
            "sparse_embedding_function": sparse_embedding_function,
            "sparse_embedding_dimensions": int(sparse_embedding_dimensions),
            "enforce_sparse_dimension_match": bool(enforce_sparse_dimension_match),
            "await_embedding": bool(await_embedding),
        }
        effective_metadata: Optional[Dict[str, Any]] = None
        if isinstance(document_metadata, dict):
            effective_metadata = dict(document_metadata)
        if isinstance(idempotency_key, str) and idempotency_key.strip():
            if effective_metadata is None:
                effective_metadata = {}
            ingest_meta = effective_metadata.get("_querylake_ingest")
            if not isinstance(ingest_meta, dict):
                ingest_meta = {}
            ingest_meta["idempotency_key"] = idempotency_key.strip()
            effective_metadata["_querylake_ingest"] = ingest_meta
        if effective_metadata is not None:
            params_payload["document_metadata"] = effective_metadata

        with path.open("rb") as f:
            files = {"file": (path.name, f, "application/octet-stream")}
            response = self._request(
                "POST",
                "/upload_document",
                params={"parameters": json.dumps(params_payload)},
                files=files,
            )
        return _extract_api_result("upload_document", response.json())

    def upload_directory(
        self,
        *,
        collection_hash_id: Union[str, int],
        directory: Optional[Union[str, Path]] = None,
        file_paths: Optional[Iterable[Union[str, Path]]] = None,
        pattern: str = "*",
        recursive: bool = False,
        max_files: Optional[int] = None,
        include_extensions: Optional[Iterable[str]] = None,
        exclude_globs: Optional[Iterable[str]] = None,
        dry_run: bool = False,
        fail_fast: bool = False,
        scan_text: bool = True,
        create_embeddings: bool = True,
        create_sparse_embeddings: bool = False,
        sparse_embedding_function: str = "embedding_sparse",
        sparse_embedding_dimensions: int = 1024,
        enforce_sparse_dimension_match: bool = True,
        await_embedding: bool = False,
        document_metadata: Optional[Dict[str, Any]] = None,
        checkpoint_file: Optional[Union[str, Path]] = None,
        resume: bool = False,
        checkpoint_save_every: int = 1,
        strict_checkpoint_match: bool = True,
        dedupe_by_content_hash: bool = False,
        dedupe_scope: str = "run-local",
        idempotency_strategy: str = "none",
        idempotency_prefix: str = "qlsdk",
        auth: AuthOverride = None,
    ) -> Dict[str, Any]:
        """
        Bulk upload local files for one collection.

        Selection modes:
        - directory scan (`directory`, `pattern`, filters)
        - explicit file list (`file_paths`)
        """
        selection_mode = "directory-scan"
        resolved_files: List[Path] = []
        payload_directory = "<explicit-file-list>"

        if file_paths is not None:
            selection_mode = "explicit-file-list"
            for value in file_paths:
                candidate = Path(value).expanduser().resolve()
                if not candidate.exists() or not candidate.is_file():
                    raise FileNotFoundError(f"File not found: {candidate}")
                resolved_files.append(candidate)
            if isinstance(directory, (str, Path)):
                payload_directory = str(Path(directory).expanduser().resolve())
        else:
            if directory is None:
                raise ValueError("directory is required unless file_paths is provided")
            root = Path(directory).expanduser().resolve()
            if not root.exists() or not root.is_dir():
                raise ValueError(f"directory must be an existing directory: {root}")
            payload_directory = str(root)
            iterator = root.rglob(pattern) if recursive else root.glob(pattern)
            resolved_files = [path for path in iterator if path.is_file()]

            if include_extensions:
                ext_set = {
                    value.lower() if value.startswith(".") else f".{value.lower()}"
                    for value in include_extensions
                    if isinstance(value, str) and value.strip()
                }
                if ext_set:
                    resolved_files = [path for path in resolved_files if path.suffix.lower() in ext_set]

            if exclude_globs:
                patterns = [value.strip() for value in exclude_globs if isinstance(value, str) and value.strip()]

                def _is_excluded(path: Path) -> bool:
                    rel_posix = path.relative_to(root).as_posix()
                    name = path.name
                    for pattern_value in patterns:
                        if fnmatch.fnmatch(rel_posix, pattern_value) or fnmatch.fnmatch(name, pattern_value):
                            return True
                    return False

                if patterns:
                    resolved_files = [path for path in resolved_files if not _is_excluded(path)]

        resolved_files.sort()
        if max_files is not None:
            resolved_files = resolved_files[: max(0, int(max_files))]
        if not resolved_files:
            raise ValueError("No files selected for upload.")

        selected_files = [str(path) for path in resolved_files]
        selection_hash = _selection_sha256(selected_files)

        checkpoint_path: Optional[Path] = None
        resumed_from_checkpoint = False
        skipped_already_uploaded = 0
        uploaded_set: set[str] = set()
        persisted_errors: List[Dict[str, Any]] = []
        checkpoint_started_at_unix: Optional[float] = None
        checkpoint_cadence = int(max(1, checkpoint_save_every))

        loaded_checkpoint: Dict[str, Any] = {}
        if checkpoint_file is not None:
            checkpoint_path = Path(checkpoint_file).expanduser().resolve()
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            if resume and checkpoint_path.exists():
                loaded = json.loads(checkpoint_path.read_text(encoding="utf-8"))
                if not isinstance(loaded, dict):
                    raise ValueError(f"Invalid checkpoint payload at {checkpoint_path}: expected object.")
                loaded_checkpoint = loaded
                checkpoint_hash = loaded.get("selection_sha256")
                if strict_checkpoint_match and checkpoint_hash != selection_hash:
                    raise ValueError(
                        "Checkpoint selection hash mismatch. "
                        f"checkpoint={checkpoint_hash} current={selection_hash}"
                    )
                prior_uploaded = loaded.get("uploaded_files")
                if isinstance(prior_uploaded, list):
                    uploaded_set = {str(value) for value in prior_uploaded if isinstance(value, str)}
                prior_errors = loaded.get("errors")
                if isinstance(prior_errors, list):
                    persisted_errors = [row for row in prior_errors if isinstance(row, dict)]
                started_value = loaded.get("started_at_unix")
                if isinstance(started_value, (int, float)):
                    checkpoint_started_at_unix = float(started_value)
                resumed_from_checkpoint = True
            elif resume and not checkpoint_path.exists():
                raise ValueError(f"Checkpoint file does not exist for resume: {checkpoint_path}")

        if uploaded_set:
            before = len(resolved_files)
            resolved_files = [path for path in resolved_files if str(path) not in uploaded_set]
            skipped_already_uploaded = before - len(resolved_files)

        dedupe_scope_value = (dedupe_scope or "run-local").strip().lower()
        valid_dedupe_scopes = {"run-local", "checkpoint-resume", "all"}
        if dedupe_by_content_hash and dedupe_scope_value not in valid_dedupe_scopes:
            raise ValueError(f"Unsupported dedupe_scope={dedupe_scope!r}. Choose one of {sorted(valid_dedupe_scopes)}.")
        idempotency_strategy_value = (idempotency_strategy or "none").strip().lower()
        valid_idempotency = {"none", "content-hash", "path-hash"}
        if idempotency_strategy_value not in valid_idempotency:
            raise ValueError(
                f"Unsupported idempotency_strategy={idempotency_strategy!r}. Choose one of {sorted(valid_idempotency)}."
            )

        need_content_hash = dedupe_by_content_hash or idempotency_strategy_value == "content-hash"
        content_hash_by_path: Dict[str, str] = {}
        if need_content_hash:
            for path in resolved_files:
                content_hash_by_path[str(path)] = _file_sha256(path)

        checkpoint_uploaded_hashes: set[str] = set()
        if dedupe_by_content_hash and resumed_from_checkpoint:
            prior_hashes = loaded_checkpoint.get("uploaded_content_hashes")
            if isinstance(prior_hashes, list):
                checkpoint_uploaded_hashes = {str(value) for value in prior_hashes if isinstance(value, str)}

        dedupe_skipped_files: List[Dict[str, Any]] = []
        seen_hashes: set[str] = set()
        if dedupe_by_content_hash:
            filtered_files: List[Path] = []
            for path in resolved_files:
                path_key = str(path)
                content_hash = content_hash_by_path.get(path_key)
                if not isinstance(content_hash, str):
                    filtered_files.append(path)
                    continue
                skip_reason: Optional[str] = None
                if dedupe_scope_value in {"run-local", "all"} and content_hash in seen_hashes:
                    skip_reason = "run-local-duplicate"
                if (
                    skip_reason is None
                    and dedupe_scope_value in {"checkpoint-resume", "all"}
                    and content_hash in checkpoint_uploaded_hashes
                ):
                    skip_reason = "checkpoint-resume-duplicate"
                if skip_reason is not None:
                    dedupe_skipped_files.append(
                        {
                            "file": path_key,
                            "content_sha256": content_hash,
                            "reason": skip_reason,
                        }
                    )
                    continue
                seen_hashes.add(content_hash)
                filtered_files.append(path)
            resolved_files = filtered_files

        payload: Dict[str, Any] = {
            "directory": payload_directory,
            "selection_mode": selection_mode,
            "pattern": pattern,
            "recursive": bool(recursive),
            "requested_files": len(selected_files),
            "pending_files": len(resolved_files),
            "uploaded": 0,
            "failed": 0,
            "dry_run": bool(dry_run),
            "selected_files": selected_files,
            "fail_fast": bool(fail_fast),
            "selection_sha256": selection_hash,
            "resumed_from_checkpoint": resumed_from_checkpoint,
            "skipped_already_uploaded": skipped_already_uploaded,
            "dedupe_by_content_hash": bool(dedupe_by_content_hash),
            "dedupe_scope": dedupe_scope_value if dedupe_by_content_hash else "none",
            "dedupe_skipped": len(dedupe_skipped_files),
            "idempotency_strategy": idempotency_strategy_value,
            "idempotency_prefix": idempotency_prefix,
        }
        if dedupe_skipped_files:
            payload["dedupe_skipped_files"] = dedupe_skipped_files
        if checkpoint_path is not None:
            payload["checkpoint_file"] = str(checkpoint_path)
            payload["checkpoint_save_every"] = checkpoint_cadence

        if dry_run:
            return payload

        if not resolved_files:
            payload["status"] = "already_complete"
            return payload

        def _checkpoint_payload(errors_payload: List[Dict[str, Any]], uploaded_payload: set[str], completed: bool) -> Dict[str, Any]:
            now = time.time()
            started = checkpoint_started_at_unix if checkpoint_started_at_unix is not None else now
            return {
                "version": 1,
                "collection_hash_id": str(collection_hash_id),
                "selection_mode": selection_mode,
                "selection_sha256": selection_hash,
                "requested_files": len(selected_files),
                "pending_files": len(resolved_files),
                "uploaded_files_count": len(uploaded_payload),
                "uploaded_files": sorted(uploaded_payload),
                "uploaded_content_hashes_count": len(uploaded_content_hashes),
                "uploaded_content_hashes": sorted(uploaded_content_hashes),
                "errors": errors_payload,
                "fail_fast": bool(fail_fast),
                "checkpoint_save_every": checkpoint_cadence,
                "completed": bool(completed),
                "started_at_unix": started,
                "updated_at_unix": now,
            }

        def _flush_checkpoint(errors_payload: List[Dict[str, Any]], uploaded_payload: set[str], completed: bool) -> None:
            if checkpoint_path is None:
                return
            checkpoint_path.write_text(
                json.dumps(_checkpoint_payload(errors_payload, uploaded_payload, completed), indent=2, sort_keys=True),
                encoding="utf-8",
            )

        errors: List[Dict[str, Any]] = list(persisted_errors)
        uploaded_content_hashes: set[str] = set(checkpoint_uploaded_hashes)
        uploaded = 0
        failed = 0
        since_flush = 0
        for path in resolved_files:
            path_key = str(path)
            content_hash = content_hash_by_path.get(path_key)
            idempotency_key: Optional[str] = None
            if idempotency_strategy_value == "content-hash" and isinstance(content_hash, str):
                idempotency_key = f"{idempotency_prefix}:{collection_hash_id}:{content_hash}"
            elif idempotency_strategy_value == "path-hash":
                idempotency_key = f"{idempotency_prefix}:{collection_hash_id}:{hashlib.sha256(path_key.encode('utf-8')).hexdigest()}"
            try:
                self.upload_document(
                    file_path=path,
                    collection_hash_id=collection_hash_id,
                    scan_text=scan_text,
                    create_embeddings=create_embeddings,
                    create_sparse_embeddings=create_sparse_embeddings,
                    sparse_embedding_function=sparse_embedding_function,
                    sparse_embedding_dimensions=sparse_embedding_dimensions,
                    enforce_sparse_dimension_match=enforce_sparse_dimension_match,
                    await_embedding=await_embedding,
                    document_metadata=document_metadata,
                    idempotency_key=idempotency_key,
                    auth=auth,
                )
                uploaded += 1
                uploaded_set.add(path_key)
                if isinstance(content_hash, str):
                    uploaded_content_hashes.add(content_hash)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                errors.append(
                    {
                        "file": path_key,
                        "error": str(exc),
                        "idempotency_key": idempotency_key,
                        "content_sha256": content_hash,
                    }
                )
                if fail_fast:
                    _flush_checkpoint(errors, uploaded_set, completed=False)
                    break
            since_flush += 1
            if since_flush >= checkpoint_cadence:
                _flush_checkpoint(errors, uploaded_set, completed=False)
                since_flush = 0

        completed = failed == 0 and uploaded >= len(resolved_files)
        _flush_checkpoint(errors, uploaded_set, completed=completed)

        payload["uploaded"] = uploaded
        payload["failed"] = failed
        if errors:
            payload["errors"] = errors
        return payload

    def upload_directory_with_options(
        self,
        *,
        collection_hash_id: Union[str, int],
        options: UploadDirectoryOptions,
        auth: AuthOverride = None,
    ) -> Dict[str, Any]:
        """
        Typed wrapper around ``upload_directory`` for reproducible ingestion setup.
        """
        kwargs = options.to_kwargs()
        return self.upload_directory(
            collection_hash_id=collection_hash_id,
            auth=auth,
            **kwargs,
        )

    def search_hybrid(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        limit_bm25: int = 12,
        limit_similarity: int = 12,
        limit_sparse: int = 0,
        bm25_weight: float = 0.55,
        similarity_weight: float = 0.45,
        sparse_weight: float = 0.0,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {
            "query": query,
            "collection_ids": [str(v) for v in collection_ids],
            "limit_bm25": int(limit_bm25),
            "limit_similarity": int(limit_similarity),
            "limit_sparse": int(limit_sparse),
            "bm25_weight": float(bm25_weight),
            "similarity_weight": float(similarity_weight),
            "sparse_weight": float(sparse_weight),
        }
        payload.update(kwargs)
        result = self.api("search_hybrid", payload)
        if isinstance(result, list):
            return result
        if isinstance(result, dict):
            rows = result.get("rows")
            if isinstance(rows, list):
                return rows
        return []

    def search_hybrid_with_options(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        options: HybridSearchOptions,
        **kwargs: Any,
    ) -> List[Dict[str, Any]]:
        profile_kwargs = options.to_kwargs()
        return self.search_hybrid(
            query=query,
            collection_ids=collection_ids,
            **profile_kwargs,
            **kwargs,
        )

    def search_hybrid_with_metrics(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        limit_bm25: int = 12,
        limit_similarity: int = 12,
        limit_sparse: int = 0,
        bm25_weight: float = 0.55,
        similarity_weight: float = 0.45,
        sparse_weight: float = 0.0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "query": query,
            "collection_ids": [str(v) for v in collection_ids],
            "limit_bm25": int(limit_bm25),
            "limit_similarity": int(limit_similarity),
            "limit_sparse": int(limit_sparse),
            "bm25_weight": float(bm25_weight),
            "similarity_weight": float(similarity_weight),
            "sparse_weight": float(sparse_weight),
        }
        payload.update(kwargs)
        result = self.api("search_hybrid", payload)
        if isinstance(result, list):
            return {"rows": result}
        if isinstance(result, dict):
            rows = result.get("rows")
            if not isinstance(rows, list):
                result = {"rows": []}
            return result
        return {"rows": []}

    def search_hybrid_with_metrics_options(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        options: HybridSearchOptions,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        profile_kwargs = options.to_kwargs()
        return self.search_hybrid_with_metrics(
            query=query,
            collection_ids=collection_ids,
            **profile_kwargs,
            **kwargs,
        )

    def search_hybrid_plan_explain(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        **kwargs: Any,
    ) -> RetrievalPlanExplainSummary:
        payload = self.search_hybrid_with_metrics(
            query=query,
            collection_ids=collection_ids,
            explain_plan=True,
            **kwargs,
        )
        return parse_retrieval_plan_explain_summary(payload.get("plan_explain"))

    def search_hybrid_plan_explain_with_options(
        self,
        *,
        query: Union[str, Dict[str, Any]],
        collection_ids: Iterable[Union[str, int]],
        options: HybridSearchOptions,
        **kwargs: Any,
    ) -> RetrievalPlanExplainSummary:
        profile_kwargs = options.to_kwargs()
        return self.search_hybrid_plan_explain(
            query=query,
            collection_ids=collection_ids,
            **profile_kwargs,
            **kwargs,
        )

    def search_hybrid_chunks(self, **kwargs: Any) -> List[SearchResultChunk]:
        rows = self.search_hybrid(**kwargs)
        parsed: List[SearchResultChunk] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            parsed.append(SearchResultChunk.from_api_dict(row))
        return parsed

    def search_bm25_with_metrics(
        self,
        *,
        query: str,
        collection_ids: Iterable[Union[str, int]],
        limit: int = 10,
        offset: int = 0,
        table: str = "document_chunk",
        group_chunks: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "query": str(query),
            "collection_ids": [str(v) for v in collection_ids],
            "limit": int(limit),
            "offset": int(offset),
            "table": str(table),
            "group_chunks": bool(group_chunks),
        }
        payload.update(kwargs)
        result = self.api("search_bm25", payload)
        if isinstance(result, list):
            return {"rows": result}
        if isinstance(result, dict):
            rows = result.get("rows")
            if not isinstance(rows, list):
                result = {"rows": []}
            return result
        return {"rows": []}

    def search_bm25_plan_explain(
        self,
        *,
        query: str,
        collection_ids: Iterable[Union[str, int]],
        **kwargs: Any,
    ) -> RetrievalPlanExplainSummary:
        payload = self.search_bm25_with_metrics(
            query=query,
            collection_ids=collection_ids,
            explain_plan=True,
            **kwargs,
        )
        return parse_retrieval_plan_explain_summary(payload.get("plan_explain"))

    def search_file_chunks_with_metrics(
        self,
        *,
        query: str,
        limit: int = 20,
        offset: int = 0,
        sort_by: str = "score",
        sort_dir: str = "DESC",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "query": str(query),
            "limit": int(limit),
            "offset": int(offset),
            "sort_by": str(sort_by),
            "sort_dir": str(sort_dir),
        }
        payload.update(kwargs)
        result = self.api("search_file_chunks", payload)
        if isinstance(result, list):
            return {"rows": result}
        if isinstance(result, dict):
            if isinstance(result.get("results"), list) and not isinstance(result.get("rows"), list):
                return {"rows": list(result.get("results") or []), **result}
            rows = result.get("rows")
            if not isinstance(rows, list):
                result = {"rows": []}
            return result
        return {"rows": []}

    def search_file_chunks_plan_explain(
        self,
        *,
        query: str,
        **kwargs: Any,
    ) -> RetrievalPlanExplainSummary:
        payload = self.search_file_chunks_with_metrics(
            query=query,
            explain_plan=True,
            **kwargs,
        )
        return parse_retrieval_plan_explain_summary(payload.get("plan_explain"))

    def count_chunks(self, *, collection_ids: Optional[Iterable[Union[str, int]]] = None) -> Dict[str, Any]:
        payload: Dict[str, Any] = {}
        if collection_ids is not None:
            payload["collection_ids"] = [str(v) for v in collection_ids]
        return self.api("count_chunks", payload)

    def get_random_chunks(
        self,
        *,
        limit: int = 5,
        collection_ids: Optional[Iterable[Union[str, int]]] = None,
    ) -> List[Dict[str, Any]]:
        payload: Dict[str, Any] = {"limit": int(limit)}
        if collection_ids is not None:
            payload["collection_ids"] = [str(v) for v in collection_ids]
        rows = self.api("get_random_chunks", payload)
        return rows if isinstance(rows, list) else []


class AsyncQueryLakeClient:
    """Async QueryLake SDK client."""

    def __init__(
        self,
        *,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 60.0,
        auth: Optional[Dict[str, str]] = None,
        oauth2: Optional[str] = None,
        api_key: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self.base_url = _normalize_base_url(base_url)
        self._auth: Dict[str, str] = {}
        self.set_auth(auth=auth, oauth2=oauth2, api_key=api_key)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=float(timeout_seconds),
            headers=headers or {},
        )

    def set_auth(
        self,
        *,
        auth: Optional[Dict[str, str]] = None,
        oauth2: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        if auth is not None:
            self._auth = dict(auth)
            return
        if oauth2:
            self._auth = {"oauth2": oauth2}
            return
        if api_key:
            self._auth = {"api_key": api_key}
            return
        self._auth = {}

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncQueryLakeClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()

    def _resolve_auth(self, auth_override: AuthOverride) -> Optional[Dict[str, str]]:
        if auth_override is False:
            return None
        if isinstance(auth_override, dict):
            return auth_override
        if self._auth:
            return self._auth
        return None

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, path, **kwargs)
        except httpx.HTTPError as exc:
            raise QueryLakeTransportError(str(exc)) from exc
        _ensure_http_success(response)
        return response

    async def api(
        self,
        function_name: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        method: Literal["POST", "GET"] = "POST",
        auth: AuthOverride = None,
    ) -> Any:
        body = dict(payload or {})
        resolved_auth = self._resolve_auth(auth)
        if resolved_auth and "auth" not in body:
            body["auth"] = resolved_auth
        response = await self._request(method, _api_function_path(function_name), json=body)
        return _extract_api_result(function_name, response.json())

    async def healthz(self) -> Dict[str, Any]:
        return (await self._request("GET", "/healthz")).json()

    async def readyz(self) -> Dict[str, Any]:
        return (await self._request("GET", "/readyz")).json()

    async def readyz_summary(self) -> ReadyzSummary:
        return parse_readyz_summary(await self.readyz())

    async def capabilities(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v1/capabilities")).json()

    async def kernel_capabilities(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v2/kernel/capabilities")).json()

    async def capabilities_summary(self) -> CapabilitiesSummary:
        return parse_capabilities_summary(await self.capabilities())

    async def support_state(self, capability_id: str) -> Optional[str]:
        return (await self.capabilities_summary()).support_state(capability_id)

    async def supports(self, capability_id: str, *, allow_degraded: bool = True) -> bool:
        return (await self.capabilities_summary()).is_available(capability_id, allow_degraded=allow_degraded)

    async def representation_scopes(self) -> Dict[str, Any]:
        summary = await self.capabilities_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    async def route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = await self.capabilities_summary()
        payload: Dict[str, Any] = {}
        for entry in summary.route_support_v2:
            payload[entry.route_id] = {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
        return payload

    async def route_representation_scope_id_from_capabilities(self, route_id: str) -> Optional[str]:
        return (await self.capabilities_summary()).route_representation_scope_id(route_id)

    async def route_capability_dependencies_from_capabilities(self, route_id: str) -> List[str]:
        return (await self.capabilities_summary()).route_capability_dependencies(route_id)

    async def route_declared_executable_from_capabilities(self, route_id: str) -> bool:
        entry = (await self.capabilities_summary()).route_support_manifest_v2_entry(route_id)
        return bool(entry is not None and entry.declared_executable)

    async def route_declared_optional_from_capabilities(self, route_id: str) -> bool:
        entry = (await self.capabilities_summary()).route_support_manifest_v2_entry(route_id)
        return bool(entry is not None and entry.declared_optional)

    async def profile_diagnostics(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v1/profile-diagnostics")).json()

    async def kernel_profile_diagnostics(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v2/kernel/profile-diagnostics")).json()

    async def projection_diagnostics(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v1/projection-diagnostics")).json()

    async def kernel_projection_diagnostics(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v2/kernel/projection-diagnostics")).json()

    async def profile_bringup(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v1/profile-bringup")).json()

    async def kernel_profile_bringup(self) -> Dict[str, Any]:
        return (await self._request("GET", "/v2/kernel/profile-bringup")).json()

    async def projection_diagnostics_summary(self) -> ProjectionDiagnosticsSummary:
        return parse_projection_diagnostics_summary(await self.projection_diagnostics())

    async def profile_bringup_summary(self) -> ProfileBringupSummary:
        return parse_profile_bringup_summary(await self.profile_bringup())

    async def kernel_profile_bringup_summary(self) -> ProfileBringupSummary:
        return parse_profile_bringup_summary(await self.kernel_profile_bringup())

    async def diagnostics_representation_scopes(self) -> Dict[str, Any]:
        summary = await self.profile_diagnostics_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    async def diagnostics_route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = await self.profile_diagnostics_summary()
        return {
            entry.route_id: {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope_id": entry.representation_scope_id(),
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
            for entry in summary.route_support_v2
        }

    async def route_planning_v2(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if entry is None:
            return {}
        return dict(entry.planning_v2)

    async def route_query_ir_v2_template(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if entry is None:
            return {}
        return entry.query_ir_v2_template()

    async def route_projection_ir_v2(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if entry is None:
            return {}
        return entry.projection_ir_v2()

    async def bringup_representation_scopes(self) -> Dict[str, Any]:
        summary = await self.profile_bringup_summary()
        return {
            scope_id: {
                "scope_id": scope.scope_id,
                "authority_model": scope.authority_model,
                "compatibility_projection": scope.compatibility_projection,
                "metadata": dict(scope.metadata),
            }
            for scope_id, scope in summary.representation_scopes.items()
        }

    async def bringup_route_support_manifest_v2(self) -> Dict[str, Any]:
        summary = await self.profile_bringup_summary()
        return {
            entry.route_id: {
                "route_id": entry.route_id,
                "support_state": entry.support_state,
                "implemented": entry.implemented,
                "declared_executable": entry.declared_executable,
                "declared_optional": entry.declared_optional,
                "representation_scope_id": entry.representation_scope_id(),
                "representation_scope": (
                    {
                        "scope_id": entry.representation_scope.scope_id,
                        "authority_model": entry.representation_scope.authority_model,
                        "compatibility_projection": entry.representation_scope.compatibility_projection,
                        "metadata": dict(entry.representation_scope.metadata),
                    }
                    if entry.representation_scope is not None
                    else None
                ),
                "capability_dependencies": list(entry.capability_dependencies),
                "notes": entry.notes,
            }
            for entry in summary.route_support_v2
        }

    async def bringup_bootstrap_command(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).bootstrap_command()

    async def bringup_next_actions(self) -> List[Dict[str, Any]]:
        summary = await self.profile_bringup_summary()
        return [
            {
                "kind": action.kind,
                "priority": action.priority,
                "summary": action.summary,
                "details": action.details,
                "command": action.command,
                "docs_ref": action.docs_ref,
                "plane": action.plane,
                "route_id": action.route_id,
                "backend": action.backend,
                "blocker_kinds": list(action.blocker_kinds),
                "projection_ids": list(action.projection_ids),
            }
            for action in summary.highest_priority_actions()
        ]

    async def bringup_backend_targets(self) -> List[Dict[str, Any]]:
        summary = await self.profile_bringup_summary()
        return [
            {
                "plane": entry.plane,
                "backend": entry.backend,
                "status": entry.status,
                "checked": entry.checked,
                "checked_at": entry.checked_at,
                "required": entry.required,
                "database_url_env": entry.database_url_env,
                "env_var": entry.env_var,
                "endpoint": entry.endpoint,
                "status_code": entry.status_code,
                "detail": entry.detail,
            }
            for entry in summary.backend_targets
        ]

    async def bringup_lexical_degraded_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).lexical_degraded_route_ids)

    async def bringup_lexical_gold_recommended_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).lexical_gold_recommended_route_ids)

    async def bringup_declared_route_support(self) -> Dict[str, str]:
        return dict((await self.profile_bringup_summary()).declared_route_support)

    async def bringup_route_declared_executable(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).route_declared_executable(route_id)

    async def bringup_route_declared_optional(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).route_declared_optional(route_id)

    async def bringup_route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).route_required_projection_descriptor_ids(route_id)

    async def bringup_declared_executable_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).declared_executable_route_ids)

    async def bringup_declared_optional_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).declared_optional_route_ids)

    async def bringup_declared_runtime_ready_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).declared_executable_runtime_ready_ids)

    async def bringup_declared_runtime_blocked_routes(self) -> List[str]:
        return list((await self.profile_bringup_summary()).declared_executable_runtime_blocked_ids)

    async def bringup_declared_routes_runtime_ready(self) -> bool:
        return (await self.profile_bringup_summary()).declared_routes_runtime_ready()

    async def bringup_route_recovery(self) -> List[Dict[str, Any]]:
        summary = await self.profile_bringup_summary()
        return [
            {
                "route_id": entry.route_id,
                "implemented": entry.implemented,
                "support_state": entry.support_state,
                "runtime_ready": entry.runtime_ready,
                "projection_ready": entry.projection_ready,
                "planning_v2": dict(entry.planning_v2),
                "query_ir_v2": entry.query_ir_v2_template(),
                "projection_ir_v2": entry.projection_ir_v2(),
                "blocker_kinds": list(entry.blocker_kinds),
                "bootstrapable_blocking_projection_ids": list(entry.bootstrapable_blocking_projection_ids),
                "nonbootstrapable_blocking_projection_ids": list(entry.nonbootstrapable_blocking_projection_ids),
                "bootstrap_command": entry.bootstrap_command,
                "lexical_support_class": entry.lexical_support_class,
                "gold_recommended_for_exact_constraints": entry.gold_recommended_for_exact_constraints,
                "exact_constraint_degraded_capabilities": list(entry.exact_constraint_degraded_capabilities),
                "exact_constraint_unsupported_capabilities": list(entry.exact_constraint_unsupported_capabilities),
            }
            for entry in summary.route_recovery
        ]

    async def bringup_route_recovery_entry(self, route_id: str) -> Optional[Dict[str, Any]]:
        entry = (await self.profile_bringup_summary()).route_recovery_entry(route_id)
        if entry is None:
            return None
        return {
            "route_id": entry.route_id,
            "implemented": entry.implemented,
            "support_state": entry.support_state,
            "runtime_ready": entry.runtime_ready,
            "projection_ready": entry.projection_ready,
            "planning_v2": dict(entry.planning_v2),
            "query_ir_v2": entry.query_ir_v2_template(),
            "projection_ir_v2": entry.projection_ir_v2(),
            "blocker_kinds": list(entry.blocker_kinds),
            "bootstrapable_blocking_projection_ids": list(entry.bootstrapable_blocking_projection_ids),
            "nonbootstrapable_blocking_projection_ids": list(entry.nonbootstrapable_blocking_projection_ids),
            "bootstrap_command": entry.bootstrap_command,
            "lexical_support_class": entry.lexical_support_class,
            "gold_recommended_for_exact_constraints": entry.gold_recommended_for_exact_constraints,
            "exact_constraint_degraded_capabilities": list(entry.exact_constraint_degraded_capabilities),
            "exact_constraint_unsupported_capabilities": list(entry.exact_constraint_unsupported_capabilities),
        }

    async def bringup_route_planning_v2(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_bringup_summary()).route_recovery_entry(route_id)
        if entry is None:
            return {}
        return dict(entry.planning_v2)

    async def bringup_route_query_ir_v2_template(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_bringup_summary()).route_recovery_entry(route_id)
        if entry is None:
            return {}
        return entry.query_ir_v2_template()

    async def bringup_route_projection_ir_v2(self, route_id: str) -> Dict[str, Any]:
        entry = (await self.profile_bringup_summary()).route_recovery_entry(route_id)
        if entry is None:
            return {}
        return entry.projection_ir_v2()

    async def local_support_matrix(self) -> List[Dict[str, Any]]:
        return (await self.profile_diagnostics_summary()).local_support_matrix()

    async def local_profile_maturity(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_profile_maturity()

    async def local_promotion_status(self) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_promotion_status()

    async def local_scope_expansion_status(self) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_scope_expansion_status()

    async def local_scope_expansion_contract(self) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_scope_expansion_contract()

    async def local_route_support_entry(self, route_id: str) -> Dict[str, Any]:
        return (await self.profile_diagnostics_summary()).local_route_support_entry(route_id)

    async def local_route_representation_scope_id(self, route_id: str) -> Optional[str]:
        return (await self.profile_diagnostics_summary()).local_route_representation_scope_id(route_id)

    async def local_route_declared_executable(self, route_id: str) -> bool:
        return (await self.profile_diagnostics_summary()).local_route_declared_executable(route_id)

    async def local_dense_sidecar(self) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_dense_sidecar()

    async def local_dense_sidecar_contract(self) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_contract()

    async def local_dense_sidecar_contract_version(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_contract_version()

    async def local_dense_sidecar_lifecycle_contract_version(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_lifecycle_contract_version()

    async def local_dense_sidecar_ready(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_ready()

    async def local_dense_sidecar_ready_state_source(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_ready_state_source()

    async def local_dense_sidecar_stats_source(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_stats_source()

    async def local_dense_sidecar_cache_lifecycle_state(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_cache_lifecycle_state()

    async def local_dense_sidecar_rebuildable_from_projection_records(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_rebuildable_from_projection_records()

    async def local_dense_sidecar_requires_process_warmup(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_requires_process_warmup()

    async def local_dense_sidecar_warmup_recommended(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_warmup_recommended()

    async def local_dense_sidecar_warmup_required_for_peak_performance(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_warmup_required_for_peak_performance()

    async def local_dense_sidecar_cold_start_recoverable(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_cold_start_recoverable()

    async def local_dense_sidecar_cache_persistence_mode(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_cache_persistence_mode()

    async def local_dense_sidecar_lifecycle_recovery_mode(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_lifecycle_recovery_mode()

    async def local_dense_sidecar_lifecycle_recovery_hints(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_lifecycle_recovery_hints()

    async def local_dense_sidecar_warmup_target_route_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_warmup_target_route_ids()

    async def local_dense_sidecar_warmup_command_hint(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_dense_sidecar_warmup_command_hint()

    async def local_dense_sidecar_persisted_projection_state_available(self) -> bool:
        return (await self.profile_bringup_summary()).local_dense_sidecar_persisted_projection_state_available()

    async def local_projection_plan_v2_registry(self) -> List[Dict[str, Any]]:
        return (await self.profile_bringup_summary()).local_projection_plan_v2_registry()

    async def local_projection_plan_v2(self, projection_id: str) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_projection_plan_v2(projection_id)

    async def local_route_runtime_contract(self, route_id: str) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_route_runtime_contract(route_id)

    async def local_route_runtime_ready(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_runtime_ready(route_id)

    async def local_route_required_projection_ids(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).local_route_required_projection_ids(route_id)

    async def local_route_capability_dependencies(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).local_route_capability_dependencies(route_id)

    async def local_route_representation_scope(self, route_id: str) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_route_representation_scope(route_id)

    async def local_route_lexical_support_class(self, route_id: str) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_route_lexical_support_class(route_id)

    async def local_route_requires_dense_sidecar(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_requires_dense_sidecar(route_id)

    async def local_route_dense_sidecar_ready(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_ready(route_id)

    async def local_route_dense_sidecar_cache_warmed(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_cache_warmed(route_id)

    async def local_route_dense_sidecar_indexed_record_count(self, route_id: str) -> int:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_indexed_record_count(route_id)

    async def local_route_dense_sidecar_contract(self, route_id: str) -> Dict[str, Any]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_contract(route_id)

    async def local_route_dense_sidecar_ready_state_source(self, route_id: str) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_ready_state_source(route_id)

    async def local_route_dense_sidecar_stats_source(self, route_id: str) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_stats_source(route_id)

    async def local_route_dense_sidecar_cache_lifecycle_state(self, route_id: str) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_cache_lifecycle_state(route_id)

    async def local_route_dense_sidecar_rebuildable_from_projection_records(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_rebuildable_from_projection_records(route_id)

    async def local_route_dense_sidecar_requires_process_warmup(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_requires_process_warmup(route_id)

    async def local_route_dense_sidecar_warmup_recommended(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_warmup_recommended(route_id)

    async def local_route_dense_sidecar_warmup_required_for_peak_performance(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_warmup_required_for_peak_performance(route_id)

    async def local_route_dense_sidecar_lifecycle_recovery_mode(self, route_id: str) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_lifecycle_recovery_mode(route_id)

    async def local_route_dense_sidecar_lifecycle_recovery_hints(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_lifecycle_recovery_hints(route_id)

    async def local_route_dense_sidecar_persisted_projection_state_available(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).local_route_dense_sidecar_persisted_projection_state_available(route_id)

    async def local_declared_executable_route_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_declared_executable_route_ids()

    async def local_declared_runtime_ready_route_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_declared_runtime_ready_route_ids()

    async def local_declared_runtime_blocked_route_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_declared_runtime_blocked_route_ids()

    async def local_required_projection_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_required_projection_ids()

    async def local_representation_scope_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_representation_scope_ids()

    async def local_current_supported_slice_frozen(self) -> bool:
        return (await self.profile_bringup_summary()).local_current_supported_slice_frozen()

    async def local_scope_expansion_pending_for_wider_scope(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_pending_for_wider_scope()

    async def local_scope_expansion_required_now(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_required_now()

    async def local_scope_expansion_satisfied_now(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_satisfied_now()

    async def local_scope_expansion_future_scope_candidates(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_future_scope_candidates()

    async def local_scope_expansion_docs_ref(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_docs_ref()

    async def local_scope_expansion_contract_docs_ref(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_contract_docs_ref()

    async def local_scope_expansion_contract_version(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_contract_version()

    async def local_scope_expansion_lifecycle_contract_version(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_lifecycle_contract_version()

    async def local_scope_expansion_lifecycle_state(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_lifecycle_state()

    async def local_scope_expansion_cache_lifecycle_state(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_cache_lifecycle_state()

    async def local_scope_expansion_dense_sidecar_promotion_contract_ready(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_dense_sidecar_promotion_contract_ready()

    async def local_scope_expansion_required_before_widening(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_required_before_widening()

    async def local_scope_expansion_rebuildable_from_projection_records(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_rebuildable_from_projection_records()

    async def local_scope_expansion_requires_process_warmup(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_requires_process_warmup()

    async def local_scope_expansion_warmup_recommended(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_warmup_recommended()

    async def local_scope_expansion_warmup_required_for_peak_performance(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_warmup_required_for_peak_performance()

    async def local_scope_expansion_cold_start_recoverable(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_cold_start_recoverable()

    async def local_scope_expansion_cache_persistence_mode(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_cache_persistence_mode()

    async def local_scope_expansion_lifecycle_recovery_mode(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_lifecycle_recovery_mode()

    async def local_scope_expansion_lifecycle_recovery_hints(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_lifecycle_recovery_hints()

    async def local_scope_expansion_warmup_target_route_ids(self) -> List[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_warmup_target_route_ids()

    async def local_scope_expansion_warmup_command_hint(self) -> Optional[str]:
        return (await self.profile_bringup_summary()).local_scope_expansion_warmup_command_hint()

    async def local_scope_expansion_persisted_projection_state_available(self) -> bool:
        return (await self.profile_bringup_summary()).local_scope_expansion_persisted_projection_state_available()

    async def route_prefers_gold_for_exact_constraints(self, route_id: str) -> bool:
        return (await self.profile_bringup_summary()).route_prefers_gold_for_exact_constraints(route_id)

    async def route_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).route_exact_constraint_degraded_capabilities(route_id)

    async def route_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        return (await self.profile_bringup_summary()).route_exact_constraint_unsupported_capabilities(route_id)

    async def bringup_projection_status_buckets(self) -> Dict[str, List[str]]:
        summary = await self.profile_bringup_summary()
        return {
            "ready": list(summary.ready_projection_ids),
            "building": list(summary.projection_building_ids),
            "failed": list(summary.projection_failed_ids),
            "stale": list(summary.projection_stale_ids),
            "absent": list(summary.projection_absent_ids),
        }

    async def bringup_recommended_projection_status_buckets(self) -> Dict[str, List[str]]:
        summary = await self.profile_bringup_summary()
        return {
            "ready": list(summary.recommended_ready_projection_ids),
            "needs_build": list(summary.recommended_projection_ids_needing_build),
            "all": list(summary.recommended_projection_ids),
        }

    async def projection_plan_explain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return (await self._request("POST", "/v1/projection-plan/explain", json=payload)).json()

    async def kernel_projection_plan_explain(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return (await self._request("POST", "/v2/kernel/projection-plan/explain", json=payload)).json()

    async def projection_plan_explain_summary(self, payload: Dict[str, Any]) -> ProjectionPlanExplainSummary:
        return parse_projection_plan_explain_summary(await self.projection_plan_explain(payload))

    async def projection_refresh_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return (await self._request("POST", "/v1/projection-refresh/run", json=payload)).json()

    async def kernel_projection_refresh_run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return (await self._request("POST", "/v2/kernel/projection-refresh/run", json=payload)).json()

    async def projection_refresh_run_summary(self, payload: Dict[str, Any]) -> ProjectionRefreshExecutionReportSummary:
        return parse_projection_refresh_execution_report_summary(await self.projection_refresh_run(payload))

    async def projection_ids_needing_build(self, *, allow_degraded: bool = True) -> List[str]:
        return (await self.projection_diagnostics_summary()).projection_ids_needing_build(
            allow_degraded=allow_degraded
        )

    async def profile_diagnostics_summary(self) -> ProfileDiagnosticsSummary:
        return parse_profile_diagnostics_summary(await self.profile_diagnostics())

    async def route_support_state(self, route_id: str) -> Optional[str]:
        return (await self.profile_diagnostics_summary()).route_support_state(route_id)

    async def route_executable(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return (await self.profile_diagnostics_summary()).route_executable(route_id, allow_degraded=allow_degraded)

    async def route_projection_ready(self, route_id: str) -> bool:
        return (await self.profile_diagnostics_summary()).route_projection_ready(route_id)

    async def route_projection_missing_descriptors(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_projection_missing_descriptors(route_id)

    async def route_runtime_ready(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        return (await self.profile_diagnostics_summary()).route_runtime_ready(route_id, allow_degraded=allow_degraded)

    async def route_blocker_kinds(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_blocker_kinds(route_id)

    async def route_blocking_projection_ids(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_blocking_projection_ids(route_id)

    async def route_lane_backends(self, route_id: str) -> Dict[str, str]:
        return (await self.profile_diagnostics_summary()).route_lane_backends(route_id)

    async def route_adapter_ids(self, route_id: str) -> Dict[str, str]:
        return (await self.profile_diagnostics_summary()).route_adapter_ids(route_id)

    async def route_projection_targets(self, route_id: str) -> List[Dict[str, Any]]:
        return (await self.profile_diagnostics_summary()).route_projection_targets(route_id)

    async def route_projection_target_backend_names(self, route_id: str) -> Dict[str, str]:
        return (await self.profile_diagnostics_summary()).route_projection_target_backend_names(route_id)

    async def route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_required_projection_descriptor_ids(route_id)

    async def route_declared_executable(self, route_id: str) -> bool:
        return (await self.profile_diagnostics_summary()).route_declared_executable(route_id)

    async def route_declared_optional(self, route_id: str) -> bool:
        return (await self.profile_diagnostics_summary()).route_declared_optional(route_id)

    async def route_lexical_semantics(self, route_id: str) -> Dict[str, Any]:
        return (await self.profile_diagnostics_summary()).route_lexical_semantics(route_id)

    async def route_lexical_support_class(self, route_id: str) -> Optional[str]:
        return (await self.profile_diagnostics_summary()).route_lexical_support_class(route_id)

    async def route_lexical_capability_states(self, route_id: str) -> Dict[str, str]:
        return (await self.profile_diagnostics_summary()).route_lexical_capability_states(route_id)

    async def route_lexical_degraded_capabilities(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_lexical_degraded_capabilities(route_id)

    async def route_lexical_unsupported_capabilities(self, route_id: str) -> List[str]:
        return (await self.profile_diagnostics_summary()).route_lexical_unsupported_capabilities(route_id)

    async def route_gold_recommended_for_exact_constraints(self, route_id: str) -> bool:
        route = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if route is None:
            return False
        return route.gold_recommended_for_exact_constraints()

    async def route_lexical_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        route = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_degraded_capabilities()

    async def route_lexical_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        route = (await self.profile_diagnostics_summary()).route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_unsupported_capabilities()

    async def route_summary(self) -> Dict[str, Any]:
        summary = (await self.profile_diagnostics_summary()).route_summary_payload()
        return {
            "inspected_route_count": summary.inspected_route_count,
            "executable_route_count": summary.executable_route_count,
            "runtime_ready_route_count": summary.runtime_ready_route_count,
            "projection_blocked_route_count": summary.projection_blocked_route_count,
            "runtime_blocked_route_count": summary.runtime_blocked_route_count,
            "compatibility_projection_route_count": summary.compatibility_projection_route_count,
            "canonical_projection_route_count": summary.canonical_projection_route_count,
            "support_state_counts": dict(summary.support_state_counts),
            "blocker_kind_counts": dict(summary.blocker_kind_counts),
            "executable_route_ids": list(summary.executable_route_ids),
            "runtime_ready_route_ids": list(summary.runtime_ready_route_ids),
            "projection_blocked_route_ids": list(summary.projection_blocked_route_ids),
            "runtime_blocked_route_ids": list(summary.runtime_blocked_route_ids),
            "compatibility_projection_route_ids": list(summary.compatibility_projection_route_ids),
            "canonical_projection_route_ids": list(summary.canonical_projection_route_ids),
        }

    async def runtime_blocker_summary(self) -> Dict[str, int]:
        return (await self.profile_diagnostics_summary()).runtime_blocker_summary()

    async def projection_blocked_routes(self, *, allow_degraded: bool = True) -> List[str]:
        return [
            entry.route_id
            for entry in (await self.profile_diagnostics_summary()).projection_blocked_routes(
                allow_degraded=allow_degraded
            )
        ]

    async def runtime_blocked_routes(self, *, allow_degraded: bool = True) -> List[str]:
        return [
            entry.route_id
            for entry in (await self.profile_diagnostics_summary()).runtime_blocked_routes(
                allow_degraded=allow_degraded
            )
        ]

    async def backend_connectivity_status(self, plane: str) -> Optional[str]:
        return (await self.profile_diagnostics_summary()).backend_connectivity_status(plane)

    async def ping(self) -> Any:
        return await self.api("ping", method="GET", auth=False)

    async def login(self, *, username: str, password: str) -> Dict[str, Any]:
        result = await self.api(
            "login",
            {"auth": {"username": username, "password": password}},
            auth=False,
        )
        if isinstance(result, dict) and isinstance(result.get("auth"), str):
            self.set_auth(oauth2=result["auth"])
        return result
