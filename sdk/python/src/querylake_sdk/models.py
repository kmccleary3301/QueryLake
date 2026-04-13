from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


AuthDict = Dict[str, str]


@dataclass
class QueryLakeProfile:
    """Serializable profile for local SDK CLI usage."""

    name: str
    base_url: str
    auth: AuthDict = field(default_factory=dict)


@dataclass
class CollectionSummary:
    id: str
    name: str
    document_count: int = 0


@dataclass
class CapabilitySummary:
    id: str
    support_state: str
    summary: str
    notes: Optional[str] = None

    def is_supported(self) -> bool:
        return self.support_state == "supported"

    def is_degraded(self) -> bool:
        return self.support_state == "degraded"

    def is_available(self, *, allow_degraded: bool = True) -> bool:
        if self.is_supported():
            return True
        return allow_degraded and self.is_degraded()


@dataclass
class DeploymentProfileSummary:
    id: str
    label: str
    implemented: bool
    recommended: bool
    maturity: Optional[str] = None
    backend_stack: Dict[str, Any] = field(default_factory=dict)
    notes: Optional[str] = None


@dataclass
class RepresentationScopeSummary:
    scope_id: str
    authority_model: str
    compatibility_projection: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RouteSupportManifestEntryV2Summary:
    route_id: str
    support_state: str
    implemented: bool
    declared_executable: bool = False
    declared_optional: bool = False
    representation_scope: Optional[RepresentationScopeSummary] = None
    capability_dependencies: List[str] = field(default_factory=list)
    notes: Optional[str] = None

    def representation_scope_id(self) -> Optional[str]:
        if self.representation_scope is None:
            return None
        return self.representation_scope.scope_id


@dataclass
class CapabilitiesSummary:
    profile: DeploymentProfileSummary
    capabilities: List[CapabilitySummary] = field(default_factory=list)
    representation_scopes: Dict[str, RepresentationScopeSummary] = field(default_factory=dict)
    route_support_v2: List[RouteSupportManifestEntryV2Summary] = field(default_factory=list)

    def capability_map(self) -> Dict[str, CapabilitySummary]:
        return {entry.id: entry for entry in self.capabilities}

    def capability(self, capability_id: str) -> Optional[CapabilitySummary]:
        return self.capability_map().get(capability_id)

    def support_state(self, capability_id: str) -> Optional[str]:
        capability = self.capability(capability_id)
        return capability.support_state if capability is not None else None

    def is_supported(self, capability_id: str) -> bool:
        capability = self.capability(capability_id)
        return capability.is_supported() if capability is not None else False

    def is_available(self, capability_id: str, *, allow_degraded: bool = True) -> bool:
        capability = self.capability(capability_id)
        return capability.is_available(allow_degraded=allow_degraded) if capability is not None else False

    def supported_capabilities(self) -> List[CapabilitySummary]:
        return [entry for entry in self.capabilities if entry.is_supported()]

    def degraded_capabilities(self) -> List[CapabilitySummary]:
        return [entry for entry in self.capabilities if entry.is_degraded()]

    def unavailable_capabilities(self) -> List[CapabilitySummary]:
        return [entry for entry in self.capabilities if not entry.is_available()]

    def representation_scope(self, scope_id: str) -> Optional[RepresentationScopeSummary]:
        return self.representation_scopes.get(str(scope_id))

    def route_support_manifest_v2_map(self) -> Dict[str, RouteSupportManifestEntryV2Summary]:
        return {entry.route_id: entry for entry in self.route_support_v2}

    def route_support_manifest_v2_entry(self, route_id: str) -> Optional[RouteSupportManifestEntryV2Summary]:
        return self.route_support_manifest_v2_map().get(str(route_id))

    def route_representation_scope(self, route_id: str) -> Optional[RepresentationScopeSummary]:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is None:
            return None
        return entry.representation_scope

    def route_representation_scope_id(self, route_id: str) -> Optional[str]:
        scope = self.route_representation_scope(route_id)
        if scope is None:
            return None
        return scope.scope_id

    def route_capability_dependencies(self, route_id: str) -> List[str]:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is None:
            return []
        return list(entry.capability_dependencies)


@dataclass
class ProfileConfigRequirementStatus:
    env_var: str
    kind: str
    summary: str
    required_for_execution: bool
    present: bool
    valid: bool
    error: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ProfileConfigurationSummary:
    profile_id: str
    ready: bool
    requirements: List[ProfileConfigRequirementStatus] = field(default_factory=list)

    def missing_requirements(self) -> List[ProfileConfigRequirementStatus]:
        return [entry for entry in self.requirements if not entry.present]

    def invalid_requirements(self) -> List[ProfileConfigRequirementStatus]:
        return [entry for entry in self.requirements if entry.present and not entry.valid]

    def blocking_requirements(self) -> List[ProfileConfigRequirementStatus]:
        return [entry for entry in self.requirements if entry.required_for_execution and (not entry.present or not entry.valid)]


@dataclass
class RouteExecutorSummary:
    route_id: str
    executor_id: str
    profile_id: str
    implemented: bool
    support_state: str
    backend_stack: Dict[str, Any] = field(default_factory=dict)
    lane_adapters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    planning_v2: Dict[str, Any] = field(default_factory=dict)
    representation_scope_id: Optional[str] = None
    representation_scope: Dict[str, Any] = field(default_factory=dict)
    projection_descriptors: List[str] = field(default_factory=list)
    projection_targets: List[Dict[str, Any]] = field(default_factory=list)
    projection_dependency_mode: Optional[str] = None
    projection_ready: bool = True
    projection_missing_descriptors: List[str] = field(default_factory=list)
    projection_writer_gap_descriptors: List[str] = field(default_factory=list)
    projection_build_gap_descriptors: List[str] = field(default_factory=list)
    compatibility_projection_target_ids: List[str] = field(default_factory=list)
    canonical_projection_target_ids: List[str] = field(default_factory=list)
    compatibility_projection_reliance: bool = False
    projection_readiness: Dict[str, Any] = field(default_factory=dict)
    lexical_semantics: Dict[str, Any] = field(default_factory=dict)
    runtime_blockers: List[Dict[str, Any]] = field(default_factory=list)
    notes: Optional[str] = None

    def requires_external_projection(self) -> bool:
        return self.projection_dependency_mode == "required_external_projection"

    def is_projection_ready(self) -> bool:
        return self.projection_ready

    def missing_required_projections(self) -> List[str]:
        return list(self.projection_missing_descriptors)

    def projection_target_map(self) -> Dict[str, Dict[str, Any]]:
        payload: Dict[str, Dict[str, Any]] = {}
        for entry in self.projection_targets:
            if not isinstance(entry, dict):
                continue
            projection_id = entry.get("projection_id")
            if projection_id is None:
                continue
            payload[str(projection_id)] = dict(entry)
        return payload

    def projection_target_backend_names(self) -> Dict[str, str]:
        return {
            projection_id: str(target.get("target_backend_name") or "")
            for projection_id, target in self.projection_target_map().items()
        }

    def projection_targets_for_authority_model(self, authority_model: str) -> List[Dict[str, Any]]:
        expected = str(authority_model)
        return [
            target
            for target in self.projection_target_map().values()
            if str(target.get("authority_model") or "") == expected
        ]

    def compatibility_projection_targets(self) -> List[Dict[str, Any]]:
        return [
            target
            for projection_id, target in self.projection_target_map().items()
            if projection_id in set(self.compatibility_projection_target_ids)
        ]

    def canonical_projection_targets(self) -> List[Dict[str, Any]]:
        return [
            target
            for projection_id, target in self.projection_target_map().items()
            if projection_id in set(self.canonical_projection_target_ids)
        ]

    def writer_gap_projection_ids(self) -> List[str]:
        return list(self.projection_writer_gap_descriptors)

    def build_gap_projection_ids(self) -> List[str]:
        return list(self.projection_build_gap_descriptors)

    def has_projection_writer_gap(self) -> bool:
        return len(self.projection_writer_gap_descriptors) > 0 or "projection_writer_unavailable" in self.blocker_kinds()

    def blocker_kinds(self) -> List[str]:
        return [
            str(entry.get("kind"))
            for entry in self.runtime_blockers
            if isinstance(entry, dict) and entry.get("kind")
        ]

    def query_ir_v2_template(self) -> Dict[str, Any]:
        return dict(self.planning_v2.get("query_ir_v2_template") or {})

    def projection_ir_v2(self) -> Dict[str, Any]:
        return dict(self.planning_v2.get("projection_ir_v2") or {})

    def blocking_projection_ids(self) -> List[str]:
        projection_ids: List[str] = []
        for entry in self.runtime_blockers:
            if not isinstance(entry, dict):
                continue
            for projection_id in entry.get("projection_ids") or []:
                projection_ids.append(str(projection_id))
        return projection_ids

    def adapter_ids(self) -> Dict[str, str]:
        direct = {
            lane_id: str(adapter.get("adapter_id"))
            for lane_id, adapter in self.lane_adapters.items()
            if isinstance(adapter, dict) and adapter.get("adapter_id")
        }
        if direct:
            return direct
        return _infer_route_adapter_ids(self.route_id, self.backend_stack)

    def lane_backends(self) -> Dict[str, str]:
        direct = {
            lane_id: str(adapter.get("backend"))
            for lane_id, adapter in self.lane_adapters.items()
            if isinstance(adapter, dict) and adapter.get("backend")
        }
        if direct:
            return direct
        return _infer_route_lane_backends(self.route_id, self.backend_stack)

    def uses_backend(self, backend_name: str) -> bool:
        return str(backend_name) in set(self.lane_backends().values())

    def representation_scope_authority_model(self) -> Optional[str]:
        value = self.representation_scope.get("authority_model")
        return str(value) if value is not None else None

    def uses_compatibility_projection_scope(self) -> bool:
        return bool(self.representation_scope.get("compatibility_projection"))

    def support_allows_execution(self, *, allow_degraded: bool = True) -> bool:
        if not self.implemented:
            return False
        if self.support_state == "supported":
            return True
        return allow_degraded and self.support_state == "degraded"

    def lexical_support_class(self) -> Optional[str]:
        value = self.lexical_semantics.get("support_class")
        return str(value) if value is not None else None

    def lexical_capability_states(self) -> Dict[str, str]:
        raw = self.lexical_semantics.get("capability_states")
        if not isinstance(raw, dict):
            return {}
        return {str(key): str(value) for key, value in raw.items()}

    def lexical_degraded_capabilities(self) -> List[str]:
        raw = self.lexical_semantics.get("degraded_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(entry) for entry in raw]

    def lexical_unsupported_capabilities(self) -> List[str]:
        raw = self.lexical_semantics.get("unsupported_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(entry) for entry in raw]

    def gold_recommended_for_exact_constraints(self) -> bool:
        return bool(self.lexical_semantics.get("gold_recommended_for_exact_constraints"))

    def exact_constraint_degraded_capabilities(self) -> List[str]:
        raw = self.lexical_semantics.get("exact_constraint_degraded_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(entry) for entry in raw]

    def exact_constraint_unsupported_capabilities(self) -> List[str]:
        raw = self.lexical_semantics.get("exact_constraint_unsupported_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(entry) for entry in raw]

    def lexical_unsupported_capabilities(self) -> List[str]:
        raw = self.lexical_semantics.get("unsupported_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(entry) for entry in raw]

    def runtime_ready(self, *, allow_degraded: bool = True) -> bool:
        if not self.support_allows_execution(allow_degraded=allow_degraded):
            return False
        if self.runtime_blockers:
            return False
        if self.requires_external_projection():
            return self.is_projection_ready()
        return True


@dataclass
class ExecutionTargetScopeItem:
    route_id: str
    state: str
    summary: str
    notes: Optional[str] = None


@dataclass
class ExecutionTargetSummary:
    profile_id: str
    maturity: str
    primary_recommendation: str
    mvp_scope: List[ExecutionTargetScopeItem] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class StartupValidationSummary:
    boot_ready: bool
    profile_implemented: bool
    configuration_ready: bool
    route_execution_ready: bool
    route_runtime_ready: bool = False
    inspected_route_ids: List[str] = field(default_factory=list)
    required_route_ids: List[str] = field(default_factory=list)
    optional_route_ids: List[str] = field(default_factory=list)
    non_executable_required_routes: List[str] = field(default_factory=list)
    non_executable_optional_routes: List[str] = field(default_factory=list)
    full_route_coverage_ready: bool = False
    non_runtime_ready_required_routes: List[str] = field(default_factory=list)
    non_runtime_ready_optional_routes: List[str] = field(default_factory=list)
    full_runtime_coverage_ready: bool = False
    validation_error: Optional[str] = None
    validation_error_kind: Optional[str] = None
    validation_error_details: Dict[str, Any] = field(default_factory=dict)
    validation_error_hint: Optional[str] = None
    validation_error_docs_ref: Optional[str] = None
    validation_error_command: Optional[str] = None

    def is_configuration_invalid(self) -> bool:
        return self.validation_error_kind == "configuration_invalid"

    def is_backend_unreachable(self) -> bool:
        return self.validation_error_kind == "backend_unreachable"

    def is_projection_runtime_blocked(self) -> bool:
        return self.validation_error_kind in {
            "projection_runtime_blocked",
            "projection_missing",
            "projection_building",
            "projection_failed",
            "projection_stale",
        }

    def has_route_execution_gap(self) -> bool:
        return self.validation_error_kind == "route_non_executable"

    def has_route_runtime_gap(self) -> bool:
        return self.validation_error_kind in {"projection_runtime_blocked", "route_not_runtime_ready"}


@dataclass
class RouteSummaryRollup:
    inspected_route_count: int
    executable_route_count: int
    runtime_ready_route_count: int
    projection_blocked_route_count: int = 0
    runtime_blocked_route_count: int = 0
    compatibility_projection_route_count: int = 0
    canonical_projection_route_count: int = 0
    support_state_counts: Dict[str, int] = field(default_factory=dict)
    blocker_kind_counts: Dict[str, int] = field(default_factory=dict)
    executable_route_ids: List[str] = field(default_factory=list)
    runtime_ready_route_ids: List[str] = field(default_factory=list)
    projection_blocked_route_ids: List[str] = field(default_factory=list)
    runtime_blocked_route_ids: List[str] = field(default_factory=list)
    compatibility_projection_route_ids: List[str] = field(default_factory=list)
    canonical_projection_route_ids: List[str] = field(default_factory=list)


@dataclass
class BackendConnectivitySummary:
    plane: str
    backend: str
    status: str
    checked: bool = False
    checked_at: Optional[float] = None
    detail: Optional[str] = None
    endpoint: Optional[str] = None
    env_var: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ready(self) -> bool:
        return self.status in {"ready", "available", "configured_ready"}

    def is_unreachable(self) -> bool:
        return self.status in {"unreachable", "backend_unreachable", "connection_failed"}

    def is_not_probed(self) -> bool:
        return self.status in {"not_probed", "configured_unprobed"}

    def blocks_execution(self) -> bool:
        return self.is_unreachable()


@dataclass
class LaneDiagnosticSummary:
    lane_family: str
    backend: str
    adapter_id: str
    support_state: str
    implemented: bool
    route_surface_declared: bool
    capability_ids: List[str] = field(default_factory=list)
    execution_mode: str = "native"
    blocked_by_capability: Optional[str] = None
    placeholder_executor_id: Optional[str] = None
    recommended_profile_id: Optional[str] = None
    hint: Optional[str] = None
    notes: Optional[str] = None

    def is_placeholder(self) -> bool:
        return self.execution_mode == "placeholder"


@dataclass
class ProfileDiagnosticsSummary:
    profile: DeploymentProfileSummary
    capabilities: List[CapabilitySummary] = field(default_factory=list)
    representation_scopes: Dict[str, RepresentationScopeSummary] = field(default_factory=dict)
    route_support_v2: List[RouteSupportManifestEntryV2Summary] = field(default_factory=list)
    configuration: Optional[ProfileConfigurationSummary] = None
    execution_target: Optional[ExecutionTargetSummary] = None
    startup_validation: Optional[StartupValidationSummary] = None
    route_summary: Optional[RouteSummaryRollup] = None
    route_executors: List[RouteExecutorSummary] = field(default_factory=list)
    lane_diagnostics: List[LaneDiagnosticSummary] = field(default_factory=list)
    backend_connectivity: Dict[str, Any] = field(default_factory=dict)
    local_profile: Dict[str, Any] = field(default_factory=dict)

    def capability_map(self) -> Dict[str, CapabilitySummary]:
        return {entry.id: entry for entry in self.capabilities}

    def capability(self, capability_id: str) -> Optional[CapabilitySummary]:
        return self.capability_map().get(capability_id)

    def representation_scope(self, scope_id: str) -> Optional[RepresentationScopeSummary]:
        return self.representation_scopes.get(str(scope_id))

    def route_support_manifest_v2_map(self) -> Dict[str, RouteSupportManifestEntryV2Summary]:
        return {entry.route_id: entry for entry in self.route_support_v2}

    def route_support_manifest_v2_entry(self, route_id: str) -> Optional[RouteSupportManifestEntryV2Summary]:
        return self.route_support_manifest_v2_map().get(str(route_id))

    def route_declared_executable(self, route_id: str) -> bool:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is not None:
            return bool(entry.declared_executable)
        route = self.route_executor(route_id)
        return bool(route is not None and route.implemented)

    def route_declared_optional(self, route_id: str) -> bool:
        entry = self.route_support_manifest_v2_entry(route_id)
        return bool(entry is not None and entry.declared_optional)

    def route_capability_dependencies(self, route_id: str) -> List[str]:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is None:
            return []
        return list(entry.capability_dependencies)

    def route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is not None and len(route.projection_descriptors) > 0:
            return list(route.projection_descriptors)
        return []

    def support_state(self, capability_id: str) -> Optional[str]:
        capability = self.capability(capability_id)
        return capability.support_state if capability is not None else None

    def is_supported(self, capability_id: str) -> bool:
        capability = self.capability(capability_id)
        return capability.is_supported() if capability is not None else False

    def is_available(self, capability_id: str, *, allow_degraded: bool = True) -> bool:
        capability = self.capability(capability_id)
        return capability.is_available(allow_degraded=allow_degraded) if capability is not None else False

    def route_executor_map(self) -> Dict[str, RouteExecutorSummary]:
        return {entry.route_id: entry for entry in self.route_executors}

    def lane_diagnostic_map(self) -> Dict[str, LaneDiagnosticSummary]:
        return {entry.lane_family: entry for entry in self.lane_diagnostics}

    def lane_diagnostic(self, lane_family: str) -> Optional[LaneDiagnosticSummary]:
        return self.lane_diagnostic_map().get(lane_family)

    def route_executor(self, route_id: str) -> Optional[RouteExecutorSummary]:
        return self.route_executor_map().get(route_id)

    def route_support_state(self, route_id: str) -> Optional[str]:
        route = self.route_executor(route_id)
        return route.support_state if route is not None else None

    def route_executable(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        route = self.route_executor(route_id)
        if route is None or not route.implemented:
            return False
        if route.support_state == "supported":
            return True
        return allow_degraded and route.support_state == "degraded"

    def route_projection_ready(self, route_id: str) -> bool:
        route = self.route_executor(route_id)
        if route is None:
            return False
        return route.is_projection_ready()

    def route_projection_missing_descriptors(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.missing_required_projections()

    def route_runtime_ready(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        route = self.route_executor(route_id)
        if route is None:
            return False
        return route.runtime_ready(allow_degraded=allow_degraded)

    def route_blocker_kinds(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.blocker_kinds()

    def route_blocking_projection_ids(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.blocking_projection_ids()

    def route_lane_backends(self, route_id: str) -> Dict[str, str]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return route.lane_backends()

    def route_projection_targets(self, route_id: str) -> List[Dict[str, Any]]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return list(route.projection_targets)

    def route_projection_target_backend_names(self, route_id: str) -> Dict[str, str]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return route.projection_target_backend_names()

    def route_adapter_ids(self, route_id: str) -> Dict[str, str]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return route.adapter_ids()

    def route_representation_scope_id(self, route_id: str) -> Optional[str]:
        route = self.route_executor(route_id)
        if route is None:
            return None
        return route.representation_scope_id

    def route_representation_scope(self, route_id: str) -> Dict[str, Any]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return dict(route.representation_scope)

    def route_lexical_semantics(self, route_id: str) -> Dict[str, Any]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return dict(route.lexical_semantics)

    def route_lexical_support_class(self, route_id: str) -> Optional[str]:
        route = self.route_executor(route_id)
        if route is None:
            return None
        return route.lexical_support_class()

    def route_lexical_capability_states(self, route_id: str) -> Dict[str, str]:
        route = self.route_executor(route_id)
        if route is None:
            return {}
        return route.lexical_capability_states()

    def route_lexical_degraded_capabilities(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.lexical_degraded_capabilities()

    def route_lexical_unsupported_capabilities(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.lexical_unsupported_capabilities()

    def route_gold_recommended_for_exact_constraints(self, route_id: str) -> bool:
        route = self.route_executor(route_id)
        if route is None:
            return False
        return route.gold_recommended_for_exact_constraints()

    def route_lexical_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_degraded_capabilities()

    def route_lexical_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        route = self.route_executor(route_id)
        if route is None:
            return []
        return route.exact_constraint_unsupported_capabilities()

    def local_support_matrix(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("support_matrix") or [])

    def local_profile_maturity(self) -> Optional[str]:
        value = self.local_profile.get("maturity")
        return str(value) if value is not None else None

    def local_route_support_entry(self, route_id: str) -> Dict[str, Any]:
        for row in self.local_support_matrix():
            if str(row.get("route_id") or "") == str(route_id):
                return dict(row)
        return {}

    def local_route_representation_scope_id(self, route_id: str) -> Optional[str]:
        value = self.local_route_support_entry(route_id).get("representation_scope_id")
        return str(value) if value is not None else None

    def local_route_representation_scope(self, route_id: str) -> Dict[str, Any]:
        support_scope = dict(self.local_route_support_entry(route_id).get("representation_scope") or {})
        if support_scope:
            return support_scope
        return dict(self.local_route_runtime_contract(route_id).get("representation_scope") or {})

    def local_route_declared_executable(self, route_id: str) -> bool:
        return bool(self.local_route_support_entry(route_id).get("declared_executable"))

    def local_dense_sidecar(self) -> Dict[str, Any]:
        return dict(self.local_profile.get("dense_sidecar") or {})

    def local_dense_sidecar_contract(self) -> Dict[str, Any]:
        return dict(self.local_dense_sidecar().get("contract") or {})

    def local_dense_sidecar_contract_version(self) -> Optional[str]:
        value = self.local_dense_sidecar_contract().get("storage_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_contract_version")
        if value is None:
            value = self.local_scope_expansion_contract().get("dense_sidecar_contract_version")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_contract_version(self) -> Optional[str]:
        value = self.local_dense_sidecar_contract().get("lifecycle_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_scope_expansion_contract().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_dense_sidecar_contract_version()
        return str(value) if value is not None else None

    def local_dense_sidecar_ready(self) -> bool:
        return bool(self.local_dense_sidecar().get("ready"))

    def local_dense_sidecar_ready_state_source(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("ready_state_source")
        return str(value) if value is not None else None

    def local_dense_sidecar_stats_source(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("stats_source")
        return str(value) if value is not None else None

    def local_dense_sidecar_cache_lifecycle_state(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_dense_sidecar_rebuildable_from_projection_records(self) -> bool:
        return bool(self.local_dense_sidecar().get("rebuildable_from_projection_records"))

    def local_dense_sidecar_requires_process_warmup(self) -> bool:
        return bool(self.local_dense_sidecar().get("requires_process_warmup"))

    def local_dense_sidecar_warmup_recommended(self) -> bool:
        return bool(self.local_dense_sidecar().get("warmup_recommended"))

    def local_dense_sidecar_warmup_required_for_peak_performance(self) -> bool:
        return bool(self.local_dense_sidecar().get("warmup_required_for_peak_performance"))

    def local_dense_sidecar_cold_start_recoverable(self) -> bool:
        return bool(self.local_dense_sidecar().get("cold_start_recoverable"))

    def local_dense_sidecar_cache_persistence_mode(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("cache_persistence_mode")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_recovery_mode(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("lifecycle_recovery_mode")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_recovery_hints(self) -> List[str]:
        return [str(item) for item in list(self.local_dense_sidecar().get("lifecycle_recovery_hints") or [])]

    def local_dense_sidecar_warmup_target_route_ids(self) -> List[str]:
        return [str(item) for item in list(self.local_dense_sidecar().get("warmup_target_route_ids") or [])]

    def local_dense_sidecar_warmup_command_hint(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("warmup_command_hint")
        return str(value) if value is not None else None

    def local_dense_sidecar_persisted_projection_state_available(self) -> bool:
        return bool(self.local_dense_sidecar().get("persisted_projection_state_available"))

    def local_dense_sidecar_cache_lifecycle_state(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_dense_sidecar_rebuildable_from_projection_records(self) -> bool:
        return bool(self.local_dense_sidecar().get("rebuildable_from_projection_records"))

    def local_dense_sidecar_requires_process_warmup(self) -> bool:
        return bool(self.local_dense_sidecar().get("requires_process_warmup"))

    def local_dense_sidecar_persisted_projection_state_available(self) -> bool:
        return bool(self.local_dense_sidecar().get("persisted_projection_state_available"))

    def local_projection_plan_v2_registry(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("projection_plan_v2_registry") or [])

    def local_projection_plan_v2(self, projection_id: str) -> Dict[str, Any]:
        for row in self.local_projection_plan_v2_registry():
            if str(row.get("projection_id") or "") == str(projection_id):
                return dict(row)
        return {}

    def local_route_runtime_contracts(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("route_runtime_contracts") or [])

    def local_route_runtime_contract(self, route_id: str) -> Dict[str, Any]:
        for row in self.local_route_runtime_contracts():
            if str(row.get("route_id") or "") == str(route_id):
                return dict(row)
        return {}

    def local_route_runtime_ready(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("runtime_ready"))

    def local_route_required_projection_ids(self, route_id: str) -> List[str]:
        return list(self.local_route_runtime_contract(route_id).get("required_projection_ids") or [])

    def local_route_capability_dependencies(self, route_id: str) -> List[str]:
        return list(self.local_route_runtime_contract(route_id).get("capability_dependencies") or [])

    def local_route_lexical_support_class(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("lexical_support_class")
        return str(value) if value is not None else None

    def local_route_requires_dense_sidecar(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_required"))

    def local_route_dense_sidecar_ready(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_ready"))

    def local_route_dense_sidecar_cache_warmed(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_cache_warmed"))

    def local_route_dense_sidecar_indexed_record_count(self, route_id: str) -> int:
        return int(self.local_route_runtime_contract(route_id).get("dense_sidecar_indexed_record_count") or 0)

    def local_route_dense_sidecar_contract(self, route_id: str) -> Dict[str, Any]:
        return dict(self.local_route_runtime_contract(route_id).get("dense_sidecar_contract") or {})

    def local_route_dense_sidecar_ready_state_source(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_ready_state_source")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_stats_source(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_stats_source")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_cache_lifecycle_state(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_rebuildable_from_projection_records(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_rebuildable_from_projection_records"
            )
        )

    def local_route_dense_sidecar_requires_process_warmup(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_requires_process_warmup"
            )
        )

    def local_route_dense_sidecar_warmup_recommended(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_warmup_recommended"
            )
        )

    def local_route_dense_sidecar_warmup_required_for_peak_performance(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_warmup_required_for_peak_performance"
            )
        )

    def local_route_dense_sidecar_lifecycle_recovery_mode(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_lifecycle_recovery_mode")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_lifecycle_recovery_hints(self, route_id: str) -> List[str]:
        return [
            str(item)
            for item in list(
                self.local_route_runtime_contract(route_id).get(
                    "dense_sidecar_lifecycle_recovery_hints"
                ) or []
            )
        ]

    def local_route_dense_sidecar_persisted_projection_state_available(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_persisted_projection_state_available"
            )
        )

    def local_route_dense_sidecar_cache_lifecycle_state(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_rebuildable_from_projection_records(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_rebuildable_from_projection_records"
            )
        )

    def local_route_dense_sidecar_requires_process_warmup(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_requires_process_warmup"
            )
        )

    def local_route_dense_sidecar_persisted_projection_state_available(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_persisted_projection_state_available"
            )
        )

    def route_summary_payload(self) -> RouteSummaryRollup:
        if self.route_summary is not None:
            return self.route_summary
        executable_routes = self.executable_routes()
        runtime_ready_routes = self.runtime_ready_routes()
        projection_blocked_routes = self.projection_blocked_routes()
        runtime_blocked_routes = self.runtime_blocked_routes()
        support_state_counts: Dict[str, int] = {}
        blocker_kind_counts: Dict[str, int] = {}
        for route in self.route_executors:
            support_state_counts[route.support_state] = support_state_counts.get(route.support_state, 0) + 1
            for kind in route.blocker_kinds():
                blocker_kind_counts[kind] = blocker_kind_counts.get(kind, 0) + 1
        return RouteSummaryRollup(
            inspected_route_count=len(self.route_executors),
            executable_route_count=len(executable_routes),
            runtime_ready_route_count=len(runtime_ready_routes),
            projection_blocked_route_count=len(projection_blocked_routes),
            runtime_blocked_route_count=len(runtime_blocked_routes),
            compatibility_projection_route_count=len(
                [route for route in self.route_executors if route.compatibility_projection_reliance]
            ),
            canonical_projection_route_count=len(
                [route for route in self.route_executors if len(route.canonical_projection_target_ids) > 0]
            ),
            support_state_counts=support_state_counts,
            blocker_kind_counts=blocker_kind_counts,
            executable_route_ids=[entry.route_id for entry in executable_routes],
            runtime_ready_route_ids=[entry.route_id for entry in runtime_ready_routes],
            projection_blocked_route_ids=[entry.route_id for entry in projection_blocked_routes],
            runtime_blocked_route_ids=[entry.route_id for entry in runtime_blocked_routes],
            compatibility_projection_route_ids=[
                entry.route_id for entry in self.route_executors if entry.compatibility_projection_reliance
            ],
            canonical_projection_route_ids=[
                entry.route_id for entry in self.route_executors if len(entry.canonical_projection_target_ids) > 0
            ],
        )

    def runtime_blocker_summary(self) -> Dict[str, int]:
        return dict(self.route_summary_payload().blocker_kind_counts)

    def executable_routes(self, *, allow_degraded: bool = True) -> List[RouteExecutorSummary]:
        return [entry for entry in self.route_executors if self.route_executable(entry.route_id, allow_degraded=allow_degraded)]

    def degraded_routes(self) -> List[RouteExecutorSummary]:
        return [entry for entry in self.route_executors if entry.implemented and entry.support_state == "degraded"]

    def missing_route_executors(self) -> List[RouteExecutorSummary]:
        return [entry for entry in self.route_executors if not entry.implemented]

    def projection_blocked_routes(self, *, allow_degraded: bool = True) -> List[RouteExecutorSummary]:
        blocked: List[RouteExecutorSummary] = []
        for entry in self.route_executors:
            if not self.route_executable(entry.route_id, allow_degraded=allow_degraded):
                continue
            if not entry.runtime_ready(allow_degraded=allow_degraded):
                blocked.append(entry)
        return blocked

    def runtime_ready_routes(self, *, allow_degraded: bool = True) -> List[RouteExecutorSummary]:
        return [entry for entry in self.route_executors if entry.runtime_ready(allow_degraded=allow_degraded)]

    def runtime_blocked_routes(self, *, allow_degraded: bool = True) -> List[RouteExecutorSummary]:
        blocked: List[RouteExecutorSummary] = []
        for entry in self.route_executors:
            if not entry.support_allows_execution(allow_degraded=allow_degraded):
                blocked.append(entry)
                continue
            if not entry.runtime_ready(allow_degraded=allow_degraded):
                blocked.append(entry)
        return blocked

    def backend_connectivity_status(self, plane: str) -> Optional[str]:
        entry = self.backend_connectivity.get(str(plane))
        if not isinstance(entry, dict):
            return None
        status = entry.get("status")
        return str(status) if status is not None else None

    def backend_connectivity_entry(self, plane: str) -> Optional[BackendConnectivitySummary]:
        entry = self.backend_connectivity.get(str(plane))
        if not isinstance(entry, dict):
            return None
        metadata = {
            key: value
            for key, value in entry.items()
            if key not in {"backend", "status", "checked", "checked_at", "detail", "endpoint", "env_var"}
        }
        return BackendConnectivitySummary(
            plane=str(plane),
            backend=str(entry.get("backend") or ""),
            status=str(entry.get("status") or ""),
            checked=bool(entry.get("checked")),
            checked_at=_optional_float(entry.get("checked_at")),
            detail=entry.get("detail"),
            endpoint=entry.get("endpoint"),
            env_var=entry.get("env_var"),
            metadata=metadata,
        )

    def backend_connectivity_entries(self) -> Dict[str, BackendConnectivitySummary]:
        parsed: Dict[str, BackendConnectivitySummary] = {}
        for plane in self.backend_connectivity.keys():
            entry = self.backend_connectivity_entry(str(plane))
            if entry is not None:
                parsed[str(plane)] = entry
        return parsed

    def route_is_degraded(self, route_id: str) -> bool:
        route = self.route_executor(route_id)
        return bool(route is not None and route.implemented and route.support_state == "degraded")

    def route_blocked_by_projection(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        route = self.route_executor(route_id)
        if route is None:
            return False
        if not route.support_allows_execution(allow_degraded=allow_degraded):
            return False
        blocker_kinds = set(route.blocker_kinds())
        return bool(
            {
                "projection_writer_unavailable",
                "projection_not_ready",
                "projection_building",
                "projection_failed",
                "projection_stale",
            }
            & blocker_kinds
        )

    def route_blocked_by_backend_connectivity(self, route_id: str, *, allow_degraded: bool = True) -> bool:
        route = self.route_executor(route_id)
        if route is None:
            return False
        if not route.support_allows_execution(allow_degraded=allow_degraded):
            return False
        if route.runtime_ready(allow_degraded=allow_degraded):
            return False
        projection_entry = self.backend_connectivity_entry("projection")
        authority_entry = self.backend_connectivity_entry("authority")
        if projection_entry is not None and projection_entry.blocks_execution():
            lane_backends = set(route.lane_backends().values())
            if projection_entry.backend in lane_backends or route.requires_external_projection():
                return True
        if authority_entry is not None and authority_entry.blocks_execution():
            authority_backend = str(route.backend_stack.get("authority") or "")
            if authority_backend and authority_backend == authority_entry.backend:
                return True
        return False

    def route_state(self, route_id: str, *, allow_degraded: bool = True) -> str:
        route = self.route_executor(route_id)
        if route is None:
            return "missing_route"
        if not route.implemented:
            return "planned"
        if not route.support_allows_execution(allow_degraded=allow_degraded):
            if route.support_state == "degraded":
                return "degraded_requires_opt_in"
            return "unsupported"
        if route.runtime_ready(allow_degraded=allow_degraded):
            return "degraded_runtime_ready" if route.support_state == "degraded" else "runtime_ready"
        if self.route_blocked_by_projection(route_id, allow_degraded=allow_degraded):
            return "blocked_by_projection"
        if self.route_blocked_by_backend_connectivity(route_id, allow_degraded=allow_degraded):
            return "blocked_by_backend_connectivity"
        return "blocked_runtime"


@dataclass
class ProfileBringupSummaryRollup:
    boot_ready: bool
    configuration_ready: bool
    route_execution_ready: bool
    route_runtime_ready: bool
    backend_connectivity_ready: bool
    declared_executable_routes_runtime_ready: bool = False
    required_projection_count: int = 0
    ready_projection_count: int = 0
    projection_ids_needing_build_count: int = 0
    bootstrapable_required_projection_count: int = 0
    nonbootstrapable_required_projection_count: int = 0
    recommended_projection_count: int = 0
    recommended_ready_projection_count: int = 0
    recommended_projection_ids_needing_build_count: int = 0
    bootstrapable_recommended_projection_count: int = 0
    nonbootstrapable_recommended_projection_count: int = 0
    projection_building_count: int = 0
    projection_failed_count: int = 0
    projection_stale_count: int = 0
    projection_absent_count: int = 0
    required_projection_status_counts: Dict[str, int] = field(default_factory=dict)
    runtime_ready_route_count: int = 0
    runtime_blocked_route_count: int = 0
    declared_route_count: int = 0
    declared_executable_route_count: int = 0
    declared_optional_route_count: int = 0
    declared_executable_runtime_ready_count: int = 0
    declared_executable_runtime_blocked_count: int = 0
    backend_unreachable_plane_count: int = 0
    lexical_degraded_route_count: int = 0
    lexical_gold_recommended_route_count: int = 0
    route_lexical_support_class_counts: Dict[str, int] = field(default_factory=dict)
    lexical_capability_blocker_counts: Dict[str, int] = field(default_factory=dict)
    compatibility_projection_route_count: int = 0
    canonical_projection_route_count: int = 0
    compatibility_projection_target_count: int = 0
    canonical_projection_target_count: int = 0
    next_action_count: int = 0
    route_recovery_count: int = 0


@dataclass
class BringupBackendTargetSummary:
    plane: str
    backend: str
    status: str
    checked: bool
    checked_at: Any = None
    required: bool = True
    database_url_env: Optional[str] = None
    env_var: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    detail: Optional[str] = None
    target: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BringupNextActionSummary:
    kind: str
    priority: str
    summary: str
    details: Optional[str] = None
    command: Optional[str] = None
    docs_ref: Optional[str] = None
    plane: Optional[str] = None
    route_id: Optional[str] = None
    route_ids: List[str] = field(default_factory=list)
    backend: Optional[str] = None
    capability_ids: List[str] = field(default_factory=list)
    blocker_kinds: List[str] = field(default_factory=list)
    projection_ids: List[str] = field(default_factory=list)


@dataclass
class BringupRouteRecoverySummary:
    route_id: str
    implemented: bool
    support_state: str
    runtime_ready: bool = False
    projection_ready: bool = False
    planning_v2: Dict[str, Any] = field(default_factory=dict)
    query_ir_v2: Dict[str, Any] = field(default_factory=dict)
    projection_ir_v2_payload: Dict[str, Any] = field(default_factory=dict)
    representation_scope_id: Optional[str] = None
    representation_scope: Dict[str, Any] = field(default_factory=dict)
    capability_dependencies: List[str] = field(default_factory=list)
    blocker_kinds: List[str] = field(default_factory=list)
    bootstrapable_blocking_projection_ids: List[str] = field(default_factory=list)
    nonbootstrapable_blocking_projection_ids: List[str] = field(default_factory=list)
    bootstrap_command: Optional[str] = None
    lexical_support_class: Optional[str] = None
    gold_recommended_for_exact_constraints: bool = False
    exact_constraint_degraded_capabilities: List[str] = field(default_factory=list)
    exact_constraint_unsupported_capabilities: List[str] = field(default_factory=list)

    def needs_bootstrap(self) -> bool:
        return len(self.bootstrapable_blocking_projection_ids) > 0

    def has_nonbootstrapable_blockers(self) -> bool:
        return len(self.nonbootstrapable_blocking_projection_ids) > 0

    def representation_scope_authority_model(self) -> Optional[str]:
        value = self.representation_scope.get("authority_model")
        return str(value) if value is not None else None

    def _inferred_representation_scope_id(self) -> str:
        if self.representation_scope_id is not None and str(self.representation_scope_id):
            return str(self.representation_scope_id)
        scope_id = str(self.representation_scope.get("scope_id") or "")
        if scope_id:
            return scope_id
        if self.route_id.endswith(".document_chunk"):
            return "document_chunk"
        if self.route_id == "search_file_chunks":
            return "file_chunk"
        if self.route_id.endswith(".segment"):
            return "segment"
        return ""

    def query_ir_v2_template(self) -> Dict[str, Any]:
        payload = dict(self.query_ir_v2 or self.planning_v2.get("query_ir_v2_template") or {})
        if payload:
            return payload
        if not self.route_id:
            return {}
        representation_scope_id = self._inferred_representation_scope_id()
        payload = {
            "route_id": str(self.route_id),
            "strictness_policy": "approximate" if self.support_state == "degraded" else "exact",
        }
        if representation_scope_id:
            payload["representation_scope_id"] = representation_scope_id
        return payload

    def projection_ir_v2(self) -> Dict[str, Any]:
        payload = dict(self.projection_ir_v2_payload or self.planning_v2.get("projection_ir_v2") or {})
        if payload:
            return payload
        if not self.route_id:
            return {}
        representation_scope_id = self._inferred_representation_scope_id()
        if not representation_scope_id:
            representation_scope_id = str(self.query_ir_v2_template().get("representation_scope_id") or "")
        payload = {
            "route_id": str(self.route_id),
            "capability_dependencies": list(self.capability_dependencies),
        }
        if representation_scope_id:
            payload["representation_scope_id"] = representation_scope_id
        return payload


@dataclass
class ProfileBringupSummary:
    profile: DeploymentProfileSummary
    summary: ProfileBringupSummaryRollup
    representation_scopes: Dict[str, RepresentationScopeSummary] = field(default_factory=dict)
    route_support_v2: List[RouteSupportManifestEntryV2Summary] = field(default_factory=list)
    required_projection_ids: List[str] = field(default_factory=list)
    ready_projection_ids: List[str] = field(default_factory=list)
    projection_ids_needing_build: List[str] = field(default_factory=list)
    bootstrapable_required_projection_ids: List[str] = field(default_factory=list)
    nonbootstrapable_required_projection_ids: List[str] = field(default_factory=list)
    recommended_projection_ids: List[str] = field(default_factory=list)
    recommended_ready_projection_ids: List[str] = field(default_factory=list)
    recommended_projection_ids_needing_build: List[str] = field(default_factory=list)
    bootstrapable_recommended_projection_ids: List[str] = field(default_factory=list)
    nonbootstrapable_recommended_projection_ids: List[str] = field(default_factory=list)
    projection_building_ids: List[str] = field(default_factory=list)
    projection_failed_ids: List[str] = field(default_factory=list)
    projection_stale_ids: List[str] = field(default_factory=list)
    projection_absent_ids: List[str] = field(default_factory=list)
    route_runtime_ready_ids: List[str] = field(default_factory=list)
    route_runtime_blocked_ids: List[str] = field(default_factory=list)
    declared_route_support: Dict[str, str] = field(default_factory=dict)
    declared_executable_route_ids: List[str] = field(default_factory=list)
    declared_optional_route_ids: List[str] = field(default_factory=list)
    declared_executable_runtime_ready_ids: List[str] = field(default_factory=list)
    declared_executable_runtime_blocked_ids: List[str] = field(default_factory=list)
    lexical_degraded_route_ids: List[str] = field(default_factory=list)
    lexical_gold_recommended_route_ids: List[str] = field(default_factory=list)
    compatibility_projection_route_ids: List[str] = field(default_factory=list)
    canonical_projection_route_ids: List[str] = field(default_factory=list)
    compatibility_projection_target_ids: List[str] = field(default_factory=list)
    canonical_projection_target_ids: List[str] = field(default_factory=list)
    backend_unreachable_planes: List[str] = field(default_factory=list)
    backend_targets: List[BringupBackendTargetSummary] = field(default_factory=list)
    route_recovery: List[BringupRouteRecoverySummary] = field(default_factory=list)
    next_actions: List[BringupNextActionSummary] = field(default_factory=list)
    profile_diagnostics: Optional[ProfileDiagnosticsSummary] = None
    projection_diagnostics: Optional["ProjectionDiagnosticsSummary"] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    local_profile: Dict[str, Any] = field(default_factory=dict)

    def needs_projection_build(self) -> bool:
        return len(self.projection_ids_needing_build) > 0

    def representation_scope(self, scope_id: str) -> Optional[RepresentationScopeSummary]:
        return self.representation_scopes.get(str(scope_id))

    def route_support_manifest_v2_map(self) -> Dict[str, RouteSupportManifestEntryV2Summary]:
        return {entry.route_id: entry for entry in self.route_support_v2}

    def route_support_manifest_v2_entry(self, route_id: str) -> Optional[RouteSupportManifestEntryV2Summary]:
        return self.route_support_manifest_v2_map().get(str(route_id))

    def route_declared_executable(self, route_id: str) -> bool:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is not None:
            return bool(entry.declared_executable)
        return str(route_id) in set(self.declared_executable_route_ids)

    def route_declared_optional(self, route_id: str) -> bool:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is not None:
            return bool(entry.declared_optional)
        return str(route_id) in set(self.declared_optional_route_ids)

    def route_capability_dependencies(self, route_id: str) -> List[str]:
        entry = self.route_support_manifest_v2_entry(route_id)
        if entry is None:
            return []
        return list(entry.capability_dependencies)

    def route_required_projection_descriptor_ids(self, route_id: str) -> List[str]:
        entry = self.route_recovery_entry(route_id)
        if entry is not None:
            projection_ir = entry.projection_ir_v2()
            raw = projection_ir.get("required_projection_descriptors")
            if isinstance(raw, list):
                return [str(item) for item in raw]
            fallback = list(entry.bootstrapable_blocking_projection_ids) + list(entry.nonbootstrapable_blocking_projection_ids)
            if len(fallback) > 0:
                return list(dict.fromkeys(str(item) for item in fallback))
        return []

    def bootstrapable_required_projections(self) -> List[str]:
        return list(self.bootstrapable_required_projection_ids)

    def nonbootstrapable_required_projections(self) -> List[str]:
        return list(self.nonbootstrapable_required_projection_ids)

    def failed_projections(self) -> List[str]:
        return list(self.projection_failed_ids)

    def stale_projections(self) -> List[str]:
        return list(self.projection_stale_ids)

    def building_projections(self) -> List[str]:
        return list(self.projection_building_ids)

    def absent_projections(self) -> List[str]:
        return list(self.projection_absent_ids)

    def recommended_projections(self) -> List[str]:
        return list(self.recommended_projection_ids)

    def recommended_projections_needing_build(self) -> List[str]:
        return list(self.recommended_projection_ids_needing_build)

    def bootstrapable_recommended_projections(self) -> List[str]:
        return list(self.bootstrapable_recommended_projection_ids)

    def nonbootstrapable_recommended_projections(self) -> List[str]:
        return list(self.nonbootstrapable_recommended_projection_ids)

    def backend_connectivity_blocked(self) -> bool:
        return len(self.backend_unreachable_planes) > 0

    def runtime_blocked(self) -> bool:
        return len(self.route_runtime_blocked_ids) > 0

    def lexical_degraded(self) -> bool:
        return len(self.lexical_degraded_route_ids) > 0

    def exact_lexical_constraints_recommend_gold(self) -> bool:
        return len(self.lexical_gold_recommended_route_ids) > 0

    def compatibility_projection_reliance(self) -> bool:
        return len(self.compatibility_projection_route_ids) > 0

    def canonical_projection_coverage(self) -> bool:
        return len(self.canonical_projection_route_ids) > 0

    def bootstrap_command(self) -> Optional[str]:
        for action in self.next_actions:
            if action.kind == "bootstrap_projections" and action.command:
                return action.command
        return None

    def highest_priority_actions(self) -> List[BringupNextActionSummary]:
        priority_order = {"high": 0, "medium": 1, "low": 2}
        return sorted(self.next_actions, key=lambda action: priority_order.get(action.priority, 99))

    def route_recovery_entry(self, route_id: str) -> Optional[BringupRouteRecoverySummary]:
        for entry in self.route_recovery:
            if entry.route_id == str(route_id):
                return entry
        return None

    def declared_route_support_state(self, route_id: str) -> Optional[str]:
        value = self.declared_route_support.get(str(route_id))
        return str(value) if value is not None else None

    def declared_route_runtime_ready(self, route_id: str) -> bool:
        return str(route_id) in set(self.declared_executable_runtime_ready_ids)

    def declared_routes_runtime_ready(self) -> bool:
        return len(self.declared_executable_runtime_blocked_ids) == 0

    def route_prefers_gold_for_exact_constraints(self, route_id: str) -> bool:
        entry = self.route_recovery_entry(route_id)
        return bool(entry is not None and entry.gold_recommended_for_exact_constraints)

    def route_exact_constraint_degraded_capabilities(self, route_id: str) -> List[str]:
        entry = self.route_recovery_entry(route_id)
        if entry is None:
            return []
        return list(entry.exact_constraint_degraded_capabilities)

    def route_exact_constraint_unsupported_capabilities(self, route_id: str) -> List[str]:
        entry = self.route_recovery_entry(route_id)
        if entry is None:
            return []
        return list(entry.exact_constraint_unsupported_capabilities)

    def local_support_matrix(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("support_matrix") or [])

    def local_promotion_status(self) -> Dict[str, Any]:
        return dict(self.local_profile.get("promotion_status") or {})

    def local_scope_expansion_status(self) -> Dict[str, Any]:
        return dict(self.local_profile.get("scope_expansion_status") or {})

    def local_scope_expansion_contract(self) -> Dict[str, Any]:
        return dict(self.local_profile.get("scope_expansion_contract") or {})

    def local_profile_maturity(self) -> Optional[str]:
        value = self.local_profile.get("maturity")
        return str(value) if value is not None else None

    def local_route_support_entry(self, route_id: str) -> Dict[str, Any]:
        for row in self.local_support_matrix():
            if str(row.get("route_id") or "") == str(route_id):
                return dict(row)
        return {}

    def local_route_representation_scope_id(self, route_id: str) -> Optional[str]:
        value = self.local_route_support_entry(route_id).get("representation_scope_id")
        return str(value) if value is not None else None

    def local_route_representation_scope(self, route_id: str) -> Dict[str, Any]:
        support_scope = dict(self.local_route_support_entry(route_id).get("representation_scope") or {})
        if support_scope:
            return support_scope
        return dict(self.local_route_runtime_contract(route_id).get("representation_scope") or {})

    def local_route_declared_executable(self, route_id: str) -> bool:
        return bool(self.local_route_support_entry(route_id).get("declared_executable"))

    def local_dense_sidecar(self) -> Dict[str, Any]:
        return dict(self.local_profile.get("dense_sidecar") or {})

    def local_dense_sidecar_contract(self) -> Dict[str, Any]:
        return dict(self.local_dense_sidecar().get("contract") or {})

    def local_dense_sidecar_contract_version(self) -> Optional[str]:
        value = self.local_dense_sidecar_contract().get("storage_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_contract_version")
        if value is None:
            value = self.local_scope_expansion_contract().get("dense_sidecar_contract_version")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_contract_version(self) -> Optional[str]:
        value = self.local_dense_sidecar_contract().get("lifecycle_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_scope_expansion_contract().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_dense_sidecar_contract_version()
        return str(value) if value is not None else None

    def local_dense_sidecar_ready(self) -> bool:
        return bool(self.local_dense_sidecar().get("ready"))

    def local_dense_sidecar_ready_state_source(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("ready_state_source")
        return str(value) if value is not None else None

    def local_dense_sidecar_stats_source(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("stats_source")
        return str(value) if value is not None else None

    def local_dense_sidecar_cache_lifecycle_state(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_dense_sidecar_rebuildable_from_projection_records(self) -> bool:
        return bool(self.local_dense_sidecar().get("rebuildable_from_projection_records"))

    def local_dense_sidecar_requires_process_warmup(self) -> bool:
        return bool(self.local_dense_sidecar().get("requires_process_warmup"))

    def local_dense_sidecar_warmup_recommended(self) -> bool:
        return bool(self.local_dense_sidecar().get("warmup_recommended"))

    def local_dense_sidecar_warmup_required_for_peak_performance(self) -> bool:
        return bool(self.local_dense_sidecar().get("warmup_required_for_peak_performance"))

    def local_dense_sidecar_cold_start_recoverable(self) -> bool:
        return bool(self.local_dense_sidecar().get("cold_start_recoverable"))

    def local_dense_sidecar_cache_persistence_mode(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("cache_persistence_mode")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_recovery_mode(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("lifecycle_recovery_mode")
        return str(value) if value is not None else None

    def local_dense_sidecar_lifecycle_recovery_hints(self) -> List[str]:
        return [str(item) for item in list(self.local_dense_sidecar().get("lifecycle_recovery_hints") or [])]

    def local_dense_sidecar_warmup_target_route_ids(self) -> List[str]:
        return [str(item) for item in list(self.local_dense_sidecar().get("warmup_target_route_ids") or [])]

    def local_dense_sidecar_warmup_command_hint(self) -> Optional[str]:
        value = self.local_dense_sidecar().get("warmup_command_hint")
        return str(value) if value is not None else None

    def local_dense_sidecar_persisted_projection_state_available(self) -> bool:
        return bool(self.local_dense_sidecar().get("persisted_projection_state_available"))

    def local_projection_plan_v2_registry(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("projection_plan_v2_registry") or [])

    def local_projection_plan_v2(self, projection_id: str) -> Dict[str, Any]:
        for row in self.local_projection_plan_v2_registry():
            if str(row.get("projection_id") or "") == str(projection_id):
                return dict(row)
        return {}

    def local_route_runtime_contracts(self) -> List[Dict[str, Any]]:
        return list(self.local_profile.get("route_runtime_contracts") or [])

    def local_route_runtime_contract(self, route_id: str) -> Dict[str, Any]:
        for row in self.local_route_runtime_contracts():
            if str(row.get("route_id") or "") == str(route_id):
                return dict(row)
        return {}

    def local_route_runtime_ready(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("runtime_ready"))

    def local_route_required_projection_ids(self, route_id: str) -> List[str]:
        return list(self.local_route_runtime_contract(route_id).get("required_projection_ids") or [])

    def local_route_capability_dependencies(self, route_id: str) -> List[str]:
        return list(self.local_route_runtime_contract(route_id).get("capability_dependencies") or [])

    def local_route_lexical_support_class(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("lexical_support_class")
        return str(value) if value is not None else None

    def local_route_requires_dense_sidecar(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_required"))

    def local_route_dense_sidecar_ready(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_ready"))

    def local_route_dense_sidecar_cache_warmed(self, route_id: str) -> bool:
        return bool(self.local_route_runtime_contract(route_id).get("dense_sidecar_cache_warmed"))

    def local_route_dense_sidecar_indexed_record_count(self, route_id: str) -> int:
        return int(self.local_route_runtime_contract(route_id).get("dense_sidecar_indexed_record_count") or 0)

    def local_route_dense_sidecar_contract(self, route_id: str) -> Dict[str, Any]:
        return dict(self.local_route_runtime_contract(route_id).get("dense_sidecar_contract") or {})

    def local_route_dense_sidecar_ready_state_source(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_ready_state_source")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_stats_source(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_stats_source")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_cache_lifecycle_state(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_rebuildable_from_projection_records(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_rebuildable_from_projection_records"
            )
        )

    def local_route_dense_sidecar_requires_process_warmup(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_requires_process_warmup"
            )
        )

    def local_route_dense_sidecar_warmup_recommended(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_warmup_recommended"
            )
        )

    def local_route_dense_sidecar_warmup_required_for_peak_performance(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_warmup_required_for_peak_performance"
            )
        )

    def local_route_dense_sidecar_lifecycle_recovery_mode(self, route_id: str) -> Optional[str]:
        value = self.local_route_runtime_contract(route_id).get("dense_sidecar_lifecycle_recovery_mode")
        return str(value) if value is not None else None

    def local_route_dense_sidecar_lifecycle_recovery_hints(self, route_id: str) -> List[str]:
        return [
            str(item)
            for item in list(
                self.local_route_runtime_contract(route_id).get(
                    "dense_sidecar_lifecycle_recovery_hints"
                ) or []
            )
        ]

    def local_route_dense_sidecar_persisted_projection_state_available(self, route_id: str) -> bool:
        return bool(
            self.local_route_runtime_contract(route_id).get(
                "dense_sidecar_persisted_projection_state_available"
            )
        )

    def local_declared_executable_route_ids(self) -> List[str]:
        return list(self.local_promotion_status().get("declared_executable_route_ids") or [])

    def local_declared_runtime_ready_route_ids(self) -> List[str]:
        return list(self.local_promotion_status().get("declared_executable_runtime_ready_ids") or [])

    def local_declared_runtime_blocked_route_ids(self) -> List[str]:
        return list(self.local_promotion_status().get("declared_executable_runtime_blocked_ids") or [])

    def local_required_projection_ids(self) -> List[str]:
        return list(self.local_promotion_status().get("required_projection_ids") or [])

    def local_representation_scope_ids(self) -> List[str]:
        return list(self.local_promotion_status().get("representation_scope_ids") or [])

    def local_current_supported_slice_frozen(self) -> bool:
        return bool(self.local_scope_expansion_status().get("current_supported_slice_frozen"))

    def local_scope_expansion_pending_for_wider_scope(self) -> List[str]:
        return list(self.local_scope_expansion_status().get("pending_for_wider_scope") or [])

    def local_scope_expansion_required_now(self) -> List[str]:
        return list(self.local_scope_expansion_status().get("required_for_scope_expansion") or [])

    def local_scope_expansion_satisfied_now(self) -> List[str]:
        return list(self.local_scope_expansion_status().get("satisfied_now") or [])

    def local_scope_expansion_future_scope_candidates(self) -> List[str]:
        return list(self.local_scope_expansion_status().get("future_scope_candidates") or [])

    def local_scope_expansion_docs_ref(self) -> Optional[str]:
        value = self.local_profile.get("scope_expansion_docs_ref")
        if value is None:
            value = self.local_scope_expansion_status().get("docs_ref")
        return str(value) if value is not None else None

    def local_scope_expansion_contract_docs_ref(self) -> Optional[str]:
        value = self.local_scope_expansion_contract().get("docs_ref")
        if value is None:
            value = self.local_scope_expansion_docs_ref()
        return str(value) if value is not None else None

    def local_scope_expansion_contract_version(self) -> Optional[str]:
        value = self.local_scope_expansion_contract().get("dense_sidecar_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_contract_version")
        if value is None:
            value = self.local_dense_sidecar_contract_version()
        return str(value) if value is not None else None

    def local_scope_expansion_lifecycle_contract_version(self) -> Optional[str]:
        value = self.local_scope_expansion_contract().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_scope_expansion_status().get("dense_sidecar_lifecycle_contract_version")
        if value is None:
            value = self.local_dense_sidecar_lifecycle_contract_version()
        if value is None:
            value = self.local_scope_expansion_contract_version()
        return str(value) if value is not None else None

    def local_scope_expansion_lifecycle_state(self) -> Optional[str]:
        value = self.local_scope_expansion_status().get("dense_sidecar_lifecycle_state")
        return str(value) if value is not None else None

    def local_scope_expansion_cache_lifecycle_state(self) -> Optional[str]:
        value = self.local_scope_expansion_status().get("dense_sidecar_cache_lifecycle_state")
        return str(value) if value is not None else None

    def local_scope_expansion_dense_sidecar_promotion_contract_ready(self) -> bool:
        return bool(
            self.local_scope_expansion_status().get("dense_sidecar_promotion_contract_ready")
        )

    def local_scope_expansion_rebuildable_from_projection_records(self) -> bool:
        return bool(
            self.local_scope_expansion_status().get(
                "dense_sidecar_rebuildable_from_projection_records"
            )
        )

    def local_scope_expansion_requires_process_warmup(self) -> bool:
        return bool(
            self.local_scope_expansion_status().get("dense_sidecar_requires_process_warmup")
        )

    def local_scope_expansion_warmup_recommended(self) -> bool:
        return bool(self.local_scope_expansion_status().get("dense_sidecar_warmup_recommended"))

    def local_scope_expansion_warmup_required_for_peak_performance(self) -> bool:
        return bool(
            self.local_scope_expansion_status().get(
                "dense_sidecar_warmup_required_for_peak_performance"
            )
        )

    def local_scope_expansion_cold_start_recoverable(self) -> bool:
        return bool(self.local_scope_expansion_status().get("dense_sidecar_cold_start_recoverable"))

    def local_scope_expansion_cache_persistence_mode(self) -> Optional[str]:
        value = self.local_scope_expansion_status().get("dense_sidecar_cache_persistence_mode")
        return str(value) if value is not None else None

    def local_scope_expansion_lifecycle_recovery_mode(self) -> Optional[str]:
        value = self.local_scope_expansion_status().get("dense_sidecar_lifecycle_recovery_mode")
        return str(value) if value is not None else None

    def local_scope_expansion_lifecycle_recovery_hints(self) -> List[str]:
        return [
            str(item)
            for item in list(
                self.local_scope_expansion_status().get(
                    "dense_sidecar_lifecycle_recovery_hints"
                ) or []
            )
        ]

    def local_scope_expansion_warmup_target_route_ids(self) -> List[str]:
        return [
            str(item)
            for item in list(
                self.local_scope_expansion_status().get(
                    "dense_sidecar_warmup_target_route_ids"
                ) or []
            )
        ]

    def local_scope_expansion_warmup_command_hint(self) -> Optional[str]:
        value = self.local_scope_expansion_status().get("dense_sidecar_warmup_command_hint")
        return str(value) if value is not None else None

    def local_scope_expansion_persisted_projection_state_available(self) -> bool:
        return bool(
            self.local_scope_expansion_status().get(
                "dense_sidecar_persisted_projection_state_available"
            )
        )

    def local_scope_expansion_required_before_widening(self) -> List[str]:
        return list(self.local_scope_expansion_contract().get("required_before_widening") or [])


@dataclass
class ReadyzProfileBringupCompactSummary:
    summary: ProfileBringupSummaryRollup
    projection_ids_needing_build: List[str] = field(default_factory=list)
    route_runtime_blocked_ids: List[str] = field(default_factory=list)
    backend_unreachable_planes: List[str] = field(default_factory=list)

    def runtime_ready(self) -> bool:
        return bool(self.summary.route_runtime_ready)

    def projection_blocked(self) -> bool:
        return len(self.projection_ids_needing_build) > 0

    def backend_blocked(self) -> bool:
        return len(self.backend_unreachable_planes) > 0


@dataclass
class ReadyzSummary:
    ok: bool
    db: str
    models: List[str] = field(default_factory=list)
    profile: Optional[DeploymentProfileSummary] = None
    startup_validation: Dict[str, Any] = field(default_factory=dict)
    bringup: Optional[ReadyzProfileBringupCompactSummary] = None

    def boot_ready(self) -> bool:
        return bool(self.startup_validation.get("boot_ready"))

    def configuration_ready(self) -> bool:
        return bool(self.startup_validation.get("configuration_ready"))

    def route_runtime_ready(self) -> bool:
        if self.bringup is not None:
            return self.bringup.runtime_ready()
        return bool(self.startup_validation.get("route_runtime_ready"))


@dataclass
class ProjectionBuildStateSummary:
    projection_id: str
    projection_version: str
    profile_id: str
    lane_family: str
    target_backend: str
    status: str
    last_build_revision: Optional[str] = None
    last_build_timestamp: Optional[float] = None
    error_summary: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProjectionDiagnosticSummaryItem:
    projection_id: str
    projection_version: str
    lane_family: str
    authority_model: str
    source_scope: str
    record_schema: str
    target_backend_family: str
    backend_name: str
    support_state: str
    executable: bool
    build_status: str
    action_mode: str
    invalidated_by: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    materialization_target: Dict[str, Any] = field(default_factory=dict)
    build_state: Optional[ProjectionBuildStateSummary] = None

    def is_ready(self) -> bool:
        return self.build_status == "ready"

    def is_available(self, *, allow_degraded: bool = True) -> bool:
        if self.support_state == "supported":
            return self.executable
        if allow_degraded and self.support_state == "degraded":
            return self.executable
        return False

    def needs_build(self, *, allow_degraded: bool = True) -> bool:
        return self.is_available(allow_degraded=allow_degraded) and not self.is_ready()


@dataclass
class ProjectionDiagnosticsSummary:
    profile_id: str
    projection_items: List[ProjectionDiagnosticSummaryItem] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def projection_map(self) -> Dict[str, ProjectionDiagnosticSummaryItem]:
        return {entry.projection_id: entry for entry in self.projection_items}

    def projection(self, projection_id: str) -> Optional[ProjectionDiagnosticSummaryItem]:
        return self.projection_map().get(projection_id)

    def ready_projections(self) -> List[ProjectionDiagnosticSummaryItem]:
        return [entry for entry in self.projection_items if entry.is_ready()]

    def actionable_projections(self, *, allow_degraded: bool = True) -> List[ProjectionDiagnosticSummaryItem]:
        return [entry for entry in self.projection_items if entry.is_available(allow_degraded=allow_degraded)]

    def blocked_projections(self, *, allow_degraded: bool = True) -> List[ProjectionDiagnosticSummaryItem]:
        return [entry for entry in self.projection_items if entry.needs_build(allow_degraded=allow_degraded)]

    def projection_ids_needing_build(self, *, allow_degraded: bool = True) -> List[str]:
        return [entry.projection_id for entry in self.blocked_projections(allow_degraded=allow_degraded)]

    def projections_for_backend(self, backend_name: str) -> List[ProjectionDiagnosticSummaryItem]:
        expected = str(backend_name)
        return [entry for entry in self.projection_items if entry.backend_name == expected]

    def projections_for_lane(self, lane_family: str) -> List[ProjectionDiagnosticSummaryItem]:
        expected = str(lane_family)
        return [entry for entry in self.projection_items if entry.lane_family == expected]

    def projections_for_authority_model(self, authority_model: str) -> List[ProjectionDiagnosticSummaryItem]:
        expected = str(authority_model)
        return [entry for entry in self.projection_items if entry.authority_model == expected]


@dataclass
class ProjectionPlanExplainSummary:
    profile_id: str
    projection_id: str
    projection_version: str
    descriptor: Dict[str, Any] = field(default_factory=dict)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    status_snapshot: List[ProjectionBuildStateSummary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalPlanStageSummary:
    stage_id: str
    primitive_id: Optional[str] = None
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    adapter: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalPlanPipelineSummary:
    pipeline_id: str
    pipeline_version: str
    source: Optional[str] = None
    resolution: Dict[str, Any] = field(default_factory=dict)
    flags: Dict[str, Any] = field(default_factory=dict)
    budgets: Dict[str, Any] = field(default_factory=dict)
    stages: List[RetrievalPlanStageSummary] = field(default_factory=list)


@dataclass
class RetrievalPlanExplainSummary:
    route: str
    pipeline: RetrievalPlanPipelineSummary
    effective: Dict[str, Any] = field(default_factory=dict)

    def route_executor(self) -> Any:
        effective_route = self.effective.get("route_executor")
        if isinstance(effective_route, str):
            return effective_route
        if isinstance(effective_route, dict):
            return effective_route
        return {}

    def lexical_capability_plan(self) -> Dict[str, Any]:
        payload = self.effective.get("lexical_capability_plan")
        if isinstance(payload, dict):
            return payload
        return {}

    def lane_state(self) -> Dict[str, Any]:
        payload = self.effective.get("lane_state")
        if isinstance(payload, dict):
            return payload
        return {}

    def adapter_ids(self) -> Dict[str, str]:
        adapter_ids: Dict[str, str] = {}
        for stage in self.pipeline.stages:
            adapter = stage.adapter
            if not isinstance(adapter, dict):
                continue
            adapter_id = adapter.get("adapter_id")
            lane_family = adapter.get("lane_family")
            if adapter_id is None or lane_family is None:
                continue
            adapter_ids[str(lane_family)] = str(adapter_id)
        return adapter_ids

    def degraded_capabilities(self) -> List[str]:
        payload = self.lexical_capability_plan()
        raw = payload.get("degraded_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(item) for item in raw]

    def unsupported_capabilities(self) -> List[str]:
        payload = self.lexical_capability_plan()
        raw = payload.get("unsupported_capabilities")
        if not isinstance(raw, list):
            return []
        return [str(item) for item in raw]

    def query_ir_v2(self) -> Dict[str, Any]:
        payload = self.effective.get("query_ir_v2")
        if isinstance(payload, dict):
            return payload
        return {}

    def projection_ir_v2(self) -> Dict[str, Any]:
        payload = self.effective.get("projection_ir_v2")
        if isinstance(payload, dict):
            return payload
        return {}

    def route_id(self) -> str:
        payload = self.query_ir_v2()
        return str(payload.get("route_id") or "")

    def representation_scope_id(self) -> str:
        payload = self.query_ir_v2()
        if payload.get("representation_scope_id") is not None:
            return str(payload.get("representation_scope_id") or "")
        projection = self.projection_ir_v2()
        return str(projection.get("representation_scope_id") or "")

    def planning_surface(self) -> Optional[str]:
        route_executor = self.route_executor()
        if isinstance(route_executor, dict):
            planning_v2 = route_executor.get("planning_v2")
            if isinstance(planning_v2, dict) and planning_v2.get("planning_surface") is not None:
                return str(planning_v2.get("planning_surface") or "")
        projection = self.projection_ir_v2()
        metadata = projection.get("metadata")
        if isinstance(metadata, dict) and metadata.get("planning_surface") is not None:
            return str(metadata.get("planning_surface") or "")
        return None

    def projection_buildability_class(self) -> Optional[str]:
        payload = self.projection_ir_v2()
        if payload.get("buildability_class") is None:
            return None
        return str(payload.get("buildability_class") or "")


@dataclass
class ProjectionRefreshActionSummary:
    projection_descriptor_id: str
    lane_family: str
    record_schema: str
    adapter_backend: str
    writer_id: Optional[str] = None
    writer_implemented: bool = False
    implemented: bool = False
    support_state: str = ""
    mode: str = ""
    current_status: str = ""
    invalidated_by: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass
class ProjectionRefreshExecutionReportSummary:
    profile_id: str
    projection_id: str
    executed_actions: List[ProjectionRefreshActionSummary] = field(default_factory=list)
    skipped_actions: List[ProjectionRefreshActionSummary] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def executed_projection_ids(self) -> List[str]:
        if len(self.executed_actions) == 0:
            return []
        return [self.projection_id]

    def skipped_modes(self) -> List[str]:
        return [action.mode for action in self.skipped_actions]

    def has_writer_gap(self) -> bool:
        return any(action.mode == "external_writer_unavailable" for action in self.skipped_actions)


@dataclass
class SearchResultChunk:
    id: str
    text: str
    document_name: Optional[str] = None
    collection_id: Optional[str] = None
    hybrid_score: Optional[float] = None
    bm25_score: Optional[float] = None
    similarity_score: Optional[float] = None
    sparse_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_api_dict(cls, payload: Dict[str, Any]) -> "SearchResultChunk":
        row_id = payload.get("id")
        if isinstance(row_id, list):
            row_id = ",".join(str(v) for v in row_id)
        return cls(
            id=str(row_id),
            text=str(payload.get("text", "")),
            document_name=payload.get("document_name"),
            collection_id=payload.get("collection_id"),
            hybrid_score=_optional_float(payload.get("hybrid_score")),
            bm25_score=_optional_float(payload.get("bm25_score")),
            similarity_score=_optional_float(payload.get("similarity_score")),
            sparse_score=_optional_float(payload.get("sparse_score")),
            metadata=payload.get("md") or {},
        )


@dataclass
class PdfOutputContractSummary:
    output_contract: str = "ocr_markdown"
    page_source_by_page: Dict[str, str] = field(default_factory=dict)
    page_source_counts: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ocr_markdown(self) -> bool:
        return self.output_contract == "ocr_markdown"

    def is_text_layer_fastpath(self) -> bool:
        return self.output_contract == "text_layer_fastpath_markdown"

    def is_mixed_text_layer_fastpath(self) -> bool:
        return self.output_contract == "mixed_text_layer_fastpath_markdown"

    def uses_text_layer(self) -> bool:
        if self.is_text_layer_fastpath() or self.is_mixed_text_layer_fastpath():
            return True
        return self.text_layer_page_count() > 0

    def text_layer_page_count(self) -> int:
        value = self.page_source_counts.get("text_layer")
        if value is None:
            return sum(1 for source in self.page_source_by_page.values() if str(source) == "text_layer")
        return int(value)

    def ocr_page_count(self) -> int:
        value = self.page_source_counts.get("ocr")
        if value is None:
            return sum(1 for source in self.page_source_by_page.values() if str(source) == "ocr")
        return int(value)

    def page_source(self, page_number: Union[int, str]) -> Optional[str]:
        if isinstance(page_number, int):
            page_key = f"{page_number:04d}"
        else:
            page_key = str(page_number).zfill(4) if str(page_number).isdigit() else str(page_number)
        source = self.page_source_by_page.get(page_key)
        return str(source) if source is not None else None


@dataclass
class UploadDirectoryOptions:
    directory: Optional[Union[str, Path]] = None
    file_paths: Optional[List[Union[str, Path]]] = None
    pattern: str = "*"
    recursive: bool = True
    max_files: Optional[int] = None
    include_extensions: Optional[List[str]] = None
    exclude_globs: Optional[List[str]] = None
    dry_run: bool = False
    fail_fast: bool = False
    scan_text: bool = True
    create_embeddings: bool = True
    create_sparse_embeddings: bool = False
    sparse_embedding_function: Optional[str] = None
    sparse_embedding_dimensions: int = 1024
    enforce_sparse_dimension_match: bool = True
    await_embedding: bool = False
    document_metadata: Optional[Dict[str, Any]] = None
    checkpoint_file: Optional[Union[str, Path]] = None
    resume: bool = False
    checkpoint_save_every: int = 1
    strict_checkpoint_match: bool = True
    dedupe_by_content_hash: bool = False
    dedupe_scope: str = "run-local"
    idempotency_strategy: str = "none"
    idempotency_prefix: str = "qlsdk"

    def __post_init__(self) -> None:
        if self.max_files is not None and int(self.max_files) < 0:
            raise ValueError("max_files must be >= 0 when provided.")
        if int(self.sparse_embedding_dimensions) < 1:
            raise ValueError("sparse_embedding_dimensions must be >= 1.")
        if int(self.checkpoint_save_every) < 1:
            raise ValueError("checkpoint_save_every must be >= 1.")
        dedupe_scope = str(self.dedupe_scope).strip().lower()
        if dedupe_scope not in {"run-local", "checkpoint-resume", "all"}:
            raise ValueError("dedupe_scope must be one of: run-local, checkpoint-resume, all.")
        self.dedupe_scope = dedupe_scope
        idempotency_strategy = str(self.idempotency_strategy).strip().lower()
        if idempotency_strategy not in {"none", "content-hash", "path-hash"}:
            raise ValueError("idempotency_strategy must be one of: none, content-hash, path-hash.")
        self.idempotency_strategy = idempotency_strategy
        prefix = str(self.idempotency_prefix).strip()
        if not prefix:
            raise ValueError("idempotency_prefix must be non-empty.")
        self.idempotency_prefix = prefix
        if self.resume and self.checkpoint_file is None:
            raise ValueError("resume=True requires checkpoint_file.")

    def to_kwargs(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "pattern": self.pattern,
            "recursive": bool(self.recursive),
            "dry_run": bool(self.dry_run),
            "fail_fast": bool(self.fail_fast),
            "scan_text": bool(self.scan_text),
            "create_embeddings": bool(self.create_embeddings),
            "create_sparse_embeddings": bool(self.create_sparse_embeddings),
            "sparse_embedding_dimensions": int(self.sparse_embedding_dimensions),
            "enforce_sparse_dimension_match": bool(self.enforce_sparse_dimension_match),
            "await_embedding": bool(self.await_embedding),
            "resume": bool(self.resume),
            "checkpoint_save_every": int(self.checkpoint_save_every),
            "strict_checkpoint_match": bool(self.strict_checkpoint_match),
            "dedupe_by_content_hash": bool(self.dedupe_by_content_hash),
            "dedupe_scope": self.dedupe_scope,
            "idempotency_strategy": self.idempotency_strategy,
            "idempotency_prefix": self.idempotency_prefix,
        }
        if self.directory is not None:
            payload["directory"] = str(Path(self.directory).expanduser().resolve())
        if self.file_paths is not None:
            payload["file_paths"] = [str(Path(v).expanduser().resolve()) for v in self.file_paths]
        if self.max_files is not None:
            payload["max_files"] = int(self.max_files)
        if self.include_extensions is not None:
            payload["include_extensions"] = list(self.include_extensions)
        if self.exclude_globs is not None:
            payload["exclude_globs"] = list(self.exclude_globs)
        if self.sparse_embedding_function is not None:
            payload["sparse_embedding_function"] = str(self.sparse_embedding_function)
        if self.document_metadata is not None:
            payload["document_metadata"] = dict(self.document_metadata)
        if self.checkpoint_file is not None:
            payload["checkpoint_file"] = str(Path(self.checkpoint_file).expanduser().resolve())
        return payload


@dataclass
class HybridSearchOptions:
    limit_bm25: int = 12
    limit_similarity: int = 12
    limit_sparse: int = 0
    bm25_weight: float = 0.55
    similarity_weight: float = 0.45
    sparse_weight: float = 0.0

    def __post_init__(self) -> None:
        for key in ("limit_bm25", "limit_similarity", "limit_sparse"):
            value = int(getattr(self, key))
            if value < 0:
                raise ValueError(f"{key} must be >= 0.")
            setattr(self, key, value)
        for key in ("bm25_weight", "similarity_weight", "sparse_weight"):
            setattr(self, key, float(getattr(self, key)))

    def to_kwargs(self) -> Dict[str, Any]:
        return {
            "limit_bm25": int(self.limit_bm25),
            "limit_similarity": int(self.limit_similarity),
            "limit_sparse": int(self.limit_sparse),
            "bm25_weight": float(self.bm25_weight),
            "similarity_weight": float(self.similarity_weight),
            "sparse_weight": float(self.sparse_weight),
        }


def build_hybrid_search_options(**kwargs: Any) -> HybridSearchOptions:
    return HybridSearchOptions(**kwargs)


def build_upload_directory_options(**kwargs: Any) -> UploadDirectoryOptions:
    return UploadDirectoryOptions(**kwargs)


def _optional_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _infer_route_lane_backends(route_id: str, backend_stack: Dict[str, Any]) -> Dict[str, str]:
    inferred: Dict[str, str] = {}
    lexical = backend_stack.get("lexical")
    dense = backend_stack.get("dense")
    sparse = backend_stack.get("sparse")

    if route_id == "search_bm25.document_chunk":
        if lexical:
            inferred["bm25"] = str(lexical)
        return inferred
    if route_id == "search_file_chunks":
        if lexical:
            inferred["bm25"] = str(lexical)
        return inferred
    if route_id == "search_hybrid.document_chunk":
        if lexical:
            inferred["bm25"] = str(lexical)
        if dense:
            inferred["dense"] = str(dense)
        if sparse and str(sparse).lower() not in {"none", "unsupported"}:
            inferred["sparse"] = str(sparse)
        return inferred
    return inferred


def _infer_route_adapter_ids(route_id: str, backend_stack: Dict[str, Any]) -> Dict[str, str]:
    adapter_ids: Dict[str, str] = {}
    lane_backends = _infer_route_lane_backends(route_id, backend_stack)

    for lane_id, backend in lane_backends.items():
        backend_name = str(backend)
        if lane_id == "bm25":
            if backend_name == "paradedb":
                adapter_ids[lane_id] = "paradedb_bm25_v1"
            elif backend_name == "opensearch":
                adapter_ids[lane_id] = "opensearch_bm25_v1"
            else:
                adapter_ids[lane_id] = f"{backend_name}_bm25_v1"
        elif lane_id == "dense":
            if backend_name == "pgvector_halfvec":
                adapter_ids[lane_id] = "pgvector_dense_halfvec_v1"
            elif backend_name == "opensearch":
                adapter_ids[lane_id] = "opensearch_dense_knn_v1"
            else:
                adapter_ids[lane_id] = f"{backend_name}_dense_v1"
        elif lane_id == "sparse":
            if backend_name == "pgvector_sparsevec":
                adapter_ids[lane_id] = "pgvector_sparse_v1"
            elif backend_name == "opensearch":
                adapter_ids[lane_id] = "opensearch_sparse_v1"
            else:
                adapter_ids[lane_id] = f"{backend_name}_sparse_v1"
    return adapter_ids


def parse_collection_summaries(data: Any) -> List[CollectionSummary]:
    rows = []
    if isinstance(data, dict) and isinstance(data.get("collections"), list):
        rows = data.get("collections", [])
    elif isinstance(data, list):
        rows = data
    parsed: List[CollectionSummary] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        parsed.append(
            CollectionSummary(
                id=str(row.get("id") or row.get("hash_id") or ""),
                name=str(row.get("name") or row.get("title") or ""),
                document_count=int(row.get("document_count") or 0),
            )
        )
    return parsed


def parse_pdf_output_contract_summary(data: Any) -> PdfOutputContractSummary:
    if not isinstance(data, dict):
        raise TypeError("pdf output contract payload must be a mapping")

    metadata = data
    if isinstance(data.get("metadata"), dict):
        metadata = dict(data.get("metadata") or {})
    elif isinstance(data.get("md"), dict):
        metadata = dict(data.get("md") or {})
    else:
        metadata = dict(data)

    raw_sources = metadata.get("page_source_by_page") or {}
    page_source_by_page: Dict[str, str] = {}
    if isinstance(raw_sources, dict):
        for key, value in raw_sources.items():
            if value is None:
                continue
            page_source_by_page[str(key)] = str(value)

    raw_counts = metadata.get("page_source_counts") or {}
    page_source_counts: Dict[str, int] = {}
    if isinstance(raw_counts, dict):
        for key, value in raw_counts.items():
            if value is None:
                continue
            try:
                page_source_counts[str(key)] = int(value)
            except (TypeError, ValueError):
                continue

    output_contract = metadata.get("output_contract")
    if output_contract is None:
        if page_source_counts.get("text_layer", 0) > 0:
            if page_source_counts.get("ocr", 0) > 0:
                output_contract = "mixed_text_layer_fastpath_markdown"
            else:
                output_contract = "text_layer_fastpath_markdown"
        else:
            output_contract = "ocr_markdown"

    return PdfOutputContractSummary(
        output_contract=str(output_contract or "ocr_markdown"),
        page_source_by_page=page_source_by_page,
        page_source_counts=page_source_counts,
        metadata=metadata,
    )


def parse_capabilities_summary(data: Any) -> CapabilitiesSummary:
    if not isinstance(data, dict):
        raise ValueError("capabilities payload must be a dictionary")
    profile_raw = data.get("profile")
    if not isinstance(profile_raw, dict):
        raise ValueError("capabilities payload is missing 'profile'")
    profile = DeploymentProfileSummary(
        id=str(profile_raw.get("id") or ""),
        label=str(profile_raw.get("label") or ""),
        implemented=bool(profile_raw.get("implemented")),
        recommended=bool(profile_raw.get("recommended")),
        maturity=(str(profile_raw.get("maturity")) if profile_raw.get("maturity") is not None else None),
        backend_stack=dict(profile_raw.get("backend_stack") or {}),
        notes=profile_raw.get("notes"),
    )
    capabilities_raw = data.get("capabilities") or []
    capabilities: List[CapabilitySummary] = []
    for row in capabilities_raw:
        if not isinstance(row, dict):
            continue
        capabilities.append(
            CapabilitySummary(
                id=str(row.get("id") or ""),
                support_state=str(row.get("support_state") or ""),
                summary=str(row.get("summary") or ""),
                notes=row.get("notes"),
            )
        )
    representation_scopes: Dict[str, RepresentationScopeSummary] = {}
    for scope_id, row in dict(data.get("representation_scopes") or {}).items():
        if not isinstance(row, dict):
            continue
        parsed = RepresentationScopeSummary(
            scope_id=str(row.get("scope_id") or scope_id),
            authority_model=str(row.get("authority_model") or ""),
            compatibility_projection=bool(row.get("compatibility_projection")),
            metadata=dict(row.get("metadata") or {}),
        )
        representation_scopes[parsed.scope_id] = parsed

    route_support_v2: List[RouteSupportManifestEntryV2Summary] = []
    for row in data.get("route_support_v2") or []:
        if not isinstance(row, dict):
            continue
        representation_scope = None
        scope_raw = row.get("representation_scope")
        if isinstance(scope_raw, dict):
            representation_scope = RepresentationScopeSummary(
                scope_id=str(scope_raw.get("scope_id") or row.get("representation_scope_id") or ""),
                authority_model=str(scope_raw.get("authority_model") or ""),
                compatibility_projection=bool(scope_raw.get("compatibility_projection")),
                metadata=dict(scope_raw.get("metadata") or {}),
            )
        route_support_v2.append(
            RouteSupportManifestEntryV2Summary(
                route_id=str(row.get("route_id") or ""),
                support_state=str(row.get("support_state") or ""),
                implemented=bool(row.get("implemented")),
                declared_executable=bool(row.get("declared_executable")),
                declared_optional=bool(row.get("declared_optional")),
                representation_scope=representation_scope,
                capability_dependencies=[str(entry) for entry in row.get("capability_dependencies") or []],
                notes=row.get("notes"),
            )
        )

    return CapabilitiesSummary(
        profile=profile,
        capabilities=capabilities,
        representation_scopes=representation_scopes,
        route_support_v2=route_support_v2,
    )


def parse_profile_diagnostics_summary(data: Any) -> ProfileDiagnosticsSummary:
    if not isinstance(data, dict):
        raise ValueError("profile diagnostics payload must be a dictionary")
    capabilities_summary = parse_capabilities_summary(data)

    configuration_raw = data.get("configuration")
    configuration = None
    if isinstance(configuration_raw, dict):
        requirements: List[ProfileConfigRequirementStatus] = []
        for row in configuration_raw.get("requirements") or []:
            if not isinstance(row, dict):
                continue
            requirements.append(
                ProfileConfigRequirementStatus(
                    env_var=str(row.get("env_var") or ""),
                    kind=str(row.get("kind") or ""),
                    summary=str(row.get("summary") or ""),
                    required_for_execution=bool(row.get("required_for_execution")),
                    present=bool(row.get("present")),
                    valid=bool(row.get("valid")),
                    error=row.get("error"),
                    notes=row.get("notes"),
                )
            )
        configuration = ProfileConfigurationSummary(
            profile_id=str(configuration_raw.get("profile_id") or ""),
            ready=bool(configuration_raw.get("ready")),
            requirements=requirements,
        )

    execution_target_raw = data.get("execution_target")
    execution_target = None
    if isinstance(execution_target_raw, dict):
        mvp_scope: List[ExecutionTargetScopeItem] = []
        for row in execution_target_raw.get("mvp_scope") or []:
            if not isinstance(row, dict):
                continue
            mvp_scope.append(
                ExecutionTargetScopeItem(
                    route_id=str(row.get("route_id") or ""),
                    state=str(row.get("state") or ""),
                    summary=str(row.get("summary") or ""),
                    notes=row.get("notes"),
                )
            )
        execution_target = ExecutionTargetSummary(
            profile_id=str(execution_target_raw.get("profile_id") or ""),
            maturity=str(execution_target_raw.get("maturity") or ""),
            primary_recommendation=str(execution_target_raw.get("primary_recommendation") or ""),
            mvp_scope=mvp_scope,
            notes=execution_target_raw.get("notes"),
        )

    startup_validation_raw = data.get("startup_validation")
    startup_validation = None
    if isinstance(startup_validation_raw, dict):
        startup_validation = StartupValidationSummary(
            boot_ready=bool(startup_validation_raw.get("boot_ready")),
            profile_implemented=bool(startup_validation_raw.get("profile_implemented")),
            configuration_ready=bool(startup_validation_raw.get("configuration_ready")),
            route_execution_ready=bool(startup_validation_raw.get("route_execution_ready")),
            route_runtime_ready=bool(startup_validation_raw.get("route_runtime_ready")),
            inspected_route_ids=list(startup_validation_raw.get("inspected_route_ids") or []),
            required_route_ids=list(startup_validation_raw.get("required_route_ids") or []),
            optional_route_ids=list(startup_validation_raw.get("optional_route_ids") or []),
            non_executable_required_routes=list(startup_validation_raw.get("non_executable_required_routes") or []),
            non_executable_optional_routes=list(startup_validation_raw.get("non_executable_optional_routes") or []),
            full_route_coverage_ready=bool(startup_validation_raw.get("full_route_coverage_ready")),
            non_runtime_ready_required_routes=list(startup_validation_raw.get("non_runtime_ready_required_routes") or []),
            non_runtime_ready_optional_routes=list(startup_validation_raw.get("non_runtime_ready_optional_routes") or []),
            full_runtime_coverage_ready=bool(startup_validation_raw.get("full_runtime_coverage_ready")),
            validation_error=startup_validation_raw.get("validation_error"),
            validation_error_kind=startup_validation_raw.get("validation_error_kind"),
            validation_error_details=dict(startup_validation_raw.get("validation_error_details") or {}),
            validation_error_hint=startup_validation_raw.get("validation_error_hint"),
            validation_error_docs_ref=startup_validation_raw.get("validation_error_docs_ref"),
            validation_error_command=startup_validation_raw.get("validation_error_command"),
        )

    route_summary_raw = data.get("route_summary")
    route_summary = None
    if isinstance(route_summary_raw, dict):
        route_summary = RouteSummaryRollup(
            inspected_route_count=int(route_summary_raw.get("inspected_route_count") or 0),
            executable_route_count=int(route_summary_raw.get("executable_route_count") or 0),
            runtime_ready_route_count=int(route_summary_raw.get("runtime_ready_route_count") or 0),
            projection_blocked_route_count=int(route_summary_raw.get("projection_blocked_route_count") or 0),
            runtime_blocked_route_count=int(route_summary_raw.get("runtime_blocked_route_count") or 0),
            compatibility_projection_route_count=int(route_summary_raw.get("compatibility_projection_route_count") or 0),
            canonical_projection_route_count=int(route_summary_raw.get("canonical_projection_route_count") or 0),
            support_state_counts=dict(route_summary_raw.get("support_state_counts") or {}),
            blocker_kind_counts=dict(route_summary_raw.get("blocker_kind_counts") or {}),
            executable_route_ids=list(route_summary_raw.get("executable_route_ids") or []),
            runtime_ready_route_ids=list(route_summary_raw.get("runtime_ready_route_ids") or []),
            projection_blocked_route_ids=list(route_summary_raw.get("projection_blocked_route_ids") or []),
            runtime_blocked_route_ids=list(route_summary_raw.get("runtime_blocked_route_ids") or []),
            compatibility_projection_route_ids=list(route_summary_raw.get("compatibility_projection_route_ids") or []),
            canonical_projection_route_ids=list(route_summary_raw.get("canonical_projection_route_ids") or []),
        )

    route_executors: List[RouteExecutorSummary] = []
    for row in data.get("route_executors") or []:
        if not isinstance(row, dict):
            continue
        projection_targets = [
            dict(target)
            for target in row.get("projection_targets") or []
            if isinstance(target, dict)
        ]
        compatibility_projection_target_ids = list(row.get("compatibility_projection_target_ids") or [])
        canonical_projection_target_ids = list(row.get("canonical_projection_target_ids") or [])
        if not compatibility_projection_target_ids and not canonical_projection_target_ids:
            for target in projection_targets:
                projection_id = str(target.get("projection_id") or "")
                authority_model = str(target.get("authority_model") or "")
                if not projection_id:
                    continue
                if authority_model.endswith("_compatibility"):
                    compatibility_projection_target_ids.append(projection_id)
                elif authority_model:
                    canonical_projection_target_ids.append(projection_id)
        route_executors.append(
            RouteExecutorSummary(
                route_id=str(row.get("route_id") or ""),
                executor_id=str(row.get("executor_id") or ""),
                profile_id=str(row.get("profile_id") or ""),
                implemented=bool(row.get("implemented")),
                support_state=str(row.get("support_state") or ""),
                backend_stack=dict(row.get("backend_stack") or {}),
                lane_adapters=dict(row.get("lane_adapters") or {}),
                planning_v2=dict(row.get("planning_v2") or {}),
                representation_scope_id=(
                    str(row.get("representation_scope_id"))
                    if row.get("representation_scope_id") is not None
                    else None
                ),
                representation_scope=dict(row.get("representation_scope") or {}),
                projection_descriptors=list(row.get("projection_descriptors") or []),
                projection_targets=projection_targets,
                projection_dependency_mode=row.get("projection_dependency_mode"),
                projection_ready=bool(row.get("projection_ready", True)),
                projection_missing_descriptors=list(row.get("projection_missing_descriptors") or []),
                projection_writer_gap_descriptors=list(row.get("projection_writer_gap_descriptors") or []),
                projection_build_gap_descriptors=list(row.get("projection_build_gap_descriptors") or []),
                compatibility_projection_target_ids=compatibility_projection_target_ids,
                canonical_projection_target_ids=canonical_projection_target_ids,
                compatibility_projection_reliance=bool(
                    row.get("compatibility_projection_reliance", False)
                    or len(compatibility_projection_target_ids) > 0
                ),
                projection_readiness=dict(row.get("projection_readiness") or {}),
                lexical_semantics=dict(row.get("lexical_semantics") or {}),
                runtime_blockers=list(row.get("runtime_blockers") or []),
                notes=row.get("notes"),
            )
        )

    lane_diagnostics: List[LaneDiagnosticSummary] = []
    for row in data.get("lane_diagnostics") or []:
        if not isinstance(row, dict):
            continue
        lane_diagnostics.append(
            LaneDiagnosticSummary(
                lane_family=str(row.get("lane_family") or ""),
                backend=str(row.get("backend") or ""),
                adapter_id=str(row.get("adapter_id") or ""),
                support_state=str(row.get("support_state") or ""),
                implemented=bool(row.get("implemented")),
                route_surface_declared=bool(row.get("route_surface_declared")),
                capability_ids=list(row.get("capability_ids") or []),
                execution_mode=str(row.get("execution_mode") or "native"),
                blocked_by_capability=row.get("blocked_by_capability"),
                placeholder_executor_id=row.get("placeholder_executor_id"),
                recommended_profile_id=row.get("recommended_profile_id"),
                hint=row.get("hint"),
                notes=row.get("notes"),
            )
        )

    return ProfileDiagnosticsSummary(
        profile=capabilities_summary.profile,
        capabilities=capabilities_summary.capabilities,
        representation_scopes=capabilities_summary.representation_scopes,
        route_support_v2=capabilities_summary.route_support_v2,
        configuration=configuration,
        execution_target=execution_target,
        startup_validation=startup_validation,
        route_summary=route_summary,
        route_executors=route_executors,
        lane_diagnostics=lane_diagnostics,
        backend_connectivity=dict(data.get("backend_connectivity") or {}),
        local_profile=dict(data.get("local_profile") or {}),
    )


def parse_projection_build_state_summary(data: Any) -> ProjectionBuildStateSummary:
    if not isinstance(data, dict):
        raise TypeError("projection build state payload must be a mapping")
    return ProjectionBuildStateSummary(
        projection_id=str(data.get("projection_id") or ""),
        projection_version=str(data.get("projection_version") or ""),
        profile_id=str(data.get("profile_id") or ""),
        lane_family=str(data.get("lane_family") or ""),
        target_backend=str(data.get("target_backend") or ""),
        status=str(data.get("status") or ""),
        last_build_revision=data.get("last_build_revision"),
        last_build_timestamp=_optional_float(data.get("last_build_timestamp")),
        error_summary=data.get("error_summary"),
        metadata=dict(data.get("metadata") or {}),
    )


def parse_projection_diagnostics_summary(data: Any) -> ProjectionDiagnosticsSummary:
    if not isinstance(data, dict):
        raise TypeError("projection diagnostics payload must be a mapping")
    items: List[ProjectionDiagnosticSummaryItem] = []
    for row in data.get("projection_items") or []:
        if not isinstance(row, dict):
            continue
        build_state_raw = row.get("build_state")
        build_state = None
        if isinstance(build_state_raw, dict) and len(build_state_raw) > 0:
            build_state = parse_projection_build_state_summary(build_state_raw)
        items.append(
            ProjectionDiagnosticSummaryItem(
                projection_id=str(row.get("projection_id") or ""),
                projection_version=str(row.get("projection_version") or ""),
                lane_family=str(row.get("lane_family") or ""),
                authority_model=str(row.get("authority_model") or ""),
                source_scope=str(row.get("source_scope") or ""),
                record_schema=str(row.get("record_schema") or ""),
                target_backend_family=str(row.get("target_backend_family") or ""),
                backend_name=str(row.get("backend_name") or ""),
                support_state=str(row.get("support_state") or ""),
                executable=bool(row.get("executable")),
                build_status=str(row.get("build_status") or ""),
                action_mode=str(row.get("action_mode") or ""),
                invalidated_by=list(row.get("invalidated_by") or []),
                notes=row.get("notes"),
                materialization_target=dict(row.get("materialization_target") or {}),
                build_state=build_state,
            )
        )
    return ProjectionDiagnosticsSummary(
        profile_id=str(data.get("profile_id") or ""),
        projection_items=items,
        metadata=dict(data.get("metadata") or {}),
    )


def parse_profile_bringup_summary(data: Any) -> ProfileBringupSummary:
    if not isinstance(data, dict):
        raise TypeError("profile bringup payload must be a mapping")
    profile_summary = parse_capabilities_summary(
        {
            "profile": data.get("profile") or {},
            "capabilities": [],
        }
    ).profile
    summary_raw = dict(data.get("summary") or {})
    profile_diagnostics_raw = data.get("profile_diagnostics") or {}
    projection_diagnostics_raw = data.get("projection_diagnostics") or {}
    return ProfileBringupSummary(
        profile=profile_summary,
        summary=ProfileBringupSummaryRollup(
            boot_ready=bool(summary_raw.get("boot_ready")),
            configuration_ready=bool(summary_raw.get("configuration_ready")),
            route_execution_ready=bool(summary_raw.get("route_execution_ready")),
            route_runtime_ready=bool(summary_raw.get("route_runtime_ready")),
            declared_executable_routes_runtime_ready=bool(
                summary_raw.get("declared_executable_routes_runtime_ready")
            ),
            backend_connectivity_ready=bool(summary_raw.get("backend_connectivity_ready")),
            required_projection_count=int(summary_raw.get("required_projection_count") or 0),
            ready_projection_count=int(summary_raw.get("ready_projection_count") or 0),
            projection_ids_needing_build_count=int(summary_raw.get("projection_ids_needing_build_count") or 0),
            bootstrapable_required_projection_count=int(summary_raw.get("bootstrapable_required_projection_count") or 0),
            nonbootstrapable_required_projection_count=int(summary_raw.get("nonbootstrapable_required_projection_count") or 0),
            recommended_projection_count=int(summary_raw.get("recommended_projection_count") or 0),
            recommended_ready_projection_count=int(summary_raw.get("recommended_ready_projection_count") or 0),
            recommended_projection_ids_needing_build_count=int(
                summary_raw.get("recommended_projection_ids_needing_build_count") or 0
            ),
            bootstrapable_recommended_projection_count=int(summary_raw.get("bootstrapable_recommended_projection_count") or 0),
            nonbootstrapable_recommended_projection_count=int(summary_raw.get("nonbootstrapable_recommended_projection_count") or 0),
            projection_building_count=int(summary_raw.get("projection_building_count") or 0),
            projection_failed_count=int(summary_raw.get("projection_failed_count") or 0),
            projection_stale_count=int(summary_raw.get("projection_stale_count") or 0),
            projection_absent_count=int(summary_raw.get("projection_absent_count") or 0),
            required_projection_status_counts=dict(summary_raw.get("required_projection_status_counts") or {}),
            runtime_ready_route_count=int(summary_raw.get("runtime_ready_route_count") or 0),
            runtime_blocked_route_count=int(summary_raw.get("runtime_blocked_route_count") or 0),
            declared_route_count=int(summary_raw.get("declared_route_count") or 0),
            declared_executable_route_count=int(summary_raw.get("declared_executable_route_count") or 0),
            declared_optional_route_count=int(summary_raw.get("declared_optional_route_count") or 0),
            declared_executable_runtime_ready_count=int(
                summary_raw.get("declared_executable_runtime_ready_count") or 0
            ),
            declared_executable_runtime_blocked_count=int(
                summary_raw.get("declared_executable_runtime_blocked_count") or 0
            ),
            backend_unreachable_plane_count=int(summary_raw.get("backend_unreachable_plane_count") or 0),
            lexical_degraded_route_count=int(summary_raw.get("lexical_degraded_route_count") or 0),
            lexical_gold_recommended_route_count=int(summary_raw.get("lexical_gold_recommended_route_count") or 0),
            route_lexical_support_class_counts=dict(summary_raw.get("route_lexical_support_class_counts") or {}),
            lexical_capability_blocker_counts=dict(summary_raw.get("lexical_capability_blocker_counts") or {}),
            compatibility_projection_route_count=int(summary_raw.get("compatibility_projection_route_count") or 0),
            canonical_projection_route_count=int(summary_raw.get("canonical_projection_route_count") or 0),
        compatibility_projection_target_count=int(summary_raw.get("compatibility_projection_target_count") or 0),
        canonical_projection_target_count=int(summary_raw.get("canonical_projection_target_count") or 0),
        next_action_count=int(summary_raw.get("next_action_count") or 0),
        route_recovery_count=int(summary_raw.get("route_recovery_count") or 0),
        ),
        representation_scopes={
            str(scope_id): RepresentationScopeSummary(
                scope_id=str(scope.get("scope_id") or scope_id),
                authority_model=str(scope.get("authority_model") or ""),
                compatibility_projection=bool(scope.get("compatibility_projection")),
                metadata=dict(scope.get("metadata") or {}),
            )
            for scope_id, scope in dict(data.get("representation_scopes") or {}).items()
            if isinstance(scope, dict)
        },
        route_support_v2=[
            RouteSupportManifestEntryV2Summary(
                route_id=str(row.get("route_id") or ""),
                support_state=str(row.get("support_state") or ""),
                implemented=bool(row.get("implemented")),
                declared_executable=bool(row.get("declared_executable")),
                declared_optional=bool(row.get("declared_optional")),
                representation_scope=(
                    RepresentationScopeSummary(
                        scope_id=str(dict(row.get("representation_scope") or {}).get("scope_id") or ""),
                        authority_model=str(dict(row.get("representation_scope") or {}).get("authority_model") or ""),
                        compatibility_projection=bool(dict(row.get("representation_scope") or {}).get("compatibility_projection")),
                        metadata=dict(dict(row.get("representation_scope") or {}).get("metadata") or {}),
                    )
                    if isinstance(row.get("representation_scope"), dict)
                    else None
                ),
                capability_dependencies=list(row.get("capability_dependencies") or []),
                notes=row.get("notes"),
            )
            for row in data.get("route_support_v2") or []
            if isinstance(row, dict)
        ],
        required_projection_ids=list(data.get("required_projection_ids") or []),
        ready_projection_ids=list(data.get("ready_projection_ids") or []),
        projection_ids_needing_build=list(data.get("projection_ids_needing_build") or []),
        bootstrapable_required_projection_ids=list(data.get("bootstrapable_required_projection_ids") or []),
        nonbootstrapable_required_projection_ids=list(data.get("nonbootstrapable_required_projection_ids") or []),
        recommended_projection_ids=list(data.get("recommended_projection_ids") or []),
        recommended_ready_projection_ids=list(data.get("recommended_ready_projection_ids") or []),
        recommended_projection_ids_needing_build=list(data.get("recommended_projection_ids_needing_build") or []),
        bootstrapable_recommended_projection_ids=list(data.get("bootstrapable_recommended_projection_ids") or []),
        nonbootstrapable_recommended_projection_ids=list(data.get("nonbootstrapable_recommended_projection_ids") or []),
        projection_building_ids=list(data.get("projection_building_ids") or []),
        projection_failed_ids=list(data.get("projection_failed_ids") or []),
        projection_stale_ids=list(data.get("projection_stale_ids") or []),
        projection_absent_ids=list(data.get("projection_absent_ids") or []),
        route_runtime_ready_ids=list(data.get("route_runtime_ready_ids") or []),
        route_runtime_blocked_ids=list(data.get("route_runtime_blocked_ids") or []),
        declared_route_support={
            str(key): str(value)
            for key, value in dict(data.get("declared_route_support") or {}).items()
        },
        declared_executable_route_ids=list(data.get("declared_executable_route_ids") or []),
        declared_optional_route_ids=list(data.get("declared_optional_route_ids") or []),
        declared_executable_runtime_ready_ids=list(data.get("declared_executable_runtime_ready_ids") or []),
        declared_executable_runtime_blocked_ids=list(data.get("declared_executable_runtime_blocked_ids") or []),
        lexical_degraded_route_ids=list(data.get("lexical_degraded_route_ids") or []),
        lexical_gold_recommended_route_ids=list(data.get("lexical_gold_recommended_route_ids") or []),
        compatibility_projection_route_ids=list(data.get("compatibility_projection_route_ids") or []),
        canonical_projection_route_ids=list(data.get("canonical_projection_route_ids") or []),
        compatibility_projection_target_ids=list(data.get("compatibility_projection_target_ids") or []),
        canonical_projection_target_ids=list(data.get("canonical_projection_target_ids") or []),
        backend_unreachable_planes=list(data.get("backend_unreachable_planes") or []),
        backend_targets=[
            BringupBackendTargetSummary(
                plane=str(row.get("plane") or ""),
                backend=str(row.get("backend") or ""),
                status=str(row.get("status") or ""),
                checked=bool(row.get("checked")),
                checked_at=row.get("checked_at"),
                required=bool(row.get("required", True)),
                database_url_env=row.get("database_url_env"),
                env_var=row.get("env_var"),
                endpoint=row.get("endpoint"),
                status_code=(int(row.get("status_code")) if row.get("status_code") is not None else None),
                detail=row.get("detail"),
                target=dict(row.get("target") or {}),
            )
            for row in data.get("backend_targets") or []
            if isinstance(row, dict)
        ],
        route_recovery=[
            BringupRouteRecoverySummary(
                route_id=str(row.get("route_id") or ""),
                implemented=bool(row.get("implemented")),
                support_state=str(row.get("support_state") or ""),
                planning_v2=dict(row.get("planning_v2") or {}),
                query_ir_v2=dict(row.get("query_ir_v2") or {}),
                projection_ir_v2_payload=dict(row.get("projection_ir_v2") or {}),
                representation_scope_id=(
                    str(row.get("representation_scope_id"))
                    if row.get("representation_scope_id") is not None
                    else None
                ),
                representation_scope=dict(row.get("representation_scope") or {}),
                capability_dependencies=list(row.get("capability_dependencies") or []),
                runtime_ready=bool(row.get("runtime_ready")),
                projection_ready=bool(row.get("projection_ready", True)),
                blocker_kinds=list(row.get("blocker_kinds") or []),
                bootstrapable_blocking_projection_ids=list(row.get("bootstrapable_blocking_projection_ids") or []),
                nonbootstrapable_blocking_projection_ids=list(row.get("nonbootstrapable_blocking_projection_ids") or []),
                bootstrap_command=row.get("bootstrap_command"),
                lexical_support_class=(
                    str(row.get("lexical_support_class"))
                    if row.get("lexical_support_class") is not None
                    else None
                ),
                gold_recommended_for_exact_constraints=bool(row.get("gold_recommended_for_exact_constraints")),
                exact_constraint_degraded_capabilities=list(row.get("exact_constraint_degraded_capabilities") or []),
                exact_constraint_unsupported_capabilities=list(
                    row.get("exact_constraint_unsupported_capabilities") or []
                ),
            )
            for row in data.get("route_recovery") or []
            if isinstance(row, dict)
        ],
        next_actions=[
            BringupNextActionSummary(
                kind=str(row.get("kind") or ""),
                priority=str(row.get("priority") or ""),
                summary=str(row.get("summary") or ""),
                details=row.get("details"),
                command=row.get("command"),
                docs_ref=row.get("docs_ref"),
                plane=row.get("plane"),
                route_id=row.get("route_id"),
                route_ids=list(row.get("route_ids") or []),
                backend=row.get("backend"),
                capability_ids=list(row.get("capability_ids") or []),
                blocker_kinds=list(row.get("blocker_kinds") or []),
                projection_ids=list(row.get("projection_ids") or []),
            )
            for row in data.get("next_actions") or []
            if isinstance(row, dict)
        ],
        profile_diagnostics=(
            parse_profile_diagnostics_summary(profile_diagnostics_raw)
            if isinstance(profile_diagnostics_raw, dict) and isinstance(profile_diagnostics_raw.get("profile"), dict)
            else None
        ),
        projection_diagnostics=(
            parse_projection_diagnostics_summary(projection_diagnostics_raw)
            if isinstance(projection_diagnostics_raw, dict)
            else None
        ),
        metadata=dict(data.get("metadata") or {}),
        local_profile=dict(data.get("local_profile") or {}),
    )


def parse_readyz_summary(data: Any) -> ReadyzSummary:
    if not isinstance(data, dict):
        raise TypeError("readyz payload must be a mapping")
    profile_payload = data.get("db_profile")
    profile_summary: Optional[DeploymentProfileSummary] = None
    if isinstance(profile_payload, dict):
        profile_summary = parse_capabilities_summary(
            {"profile": profile_payload, "capabilities": []}
        ).profile
    startup_validation = dict(data.get("db_profile_diagnostics") or {})
    bringup_payload = dict(data.get("db_profile_bringup") or {})
    bringup_summary: Optional[ReadyzProfileBringupCompactSummary] = None
    if bringup_payload:
        summary_raw = dict(bringup_payload.get("summary") or {})
        bringup_summary = ReadyzProfileBringupCompactSummary(
            summary=ProfileBringupSummaryRollup(
                boot_ready=bool(summary_raw.get("boot_ready")),
                configuration_ready=bool(summary_raw.get("configuration_ready")),
                route_execution_ready=bool(summary_raw.get("route_execution_ready")),
                route_runtime_ready=bool(summary_raw.get("route_runtime_ready")),
                backend_connectivity_ready=bool(summary_raw.get("backend_connectivity_ready")),
                required_projection_count=int(summary_raw.get("required_projection_count") or 0),
                ready_projection_count=int(summary_raw.get("ready_projection_count") or 0),
                projection_ids_needing_build_count=int(summary_raw.get("projection_ids_needing_build_count") or 0),
                bootstrapable_required_projection_count=int(summary_raw.get("bootstrapable_required_projection_count") or 0),
                nonbootstrapable_required_projection_count=int(summary_raw.get("nonbootstrapable_required_projection_count") or 0),
                runtime_ready_route_count=int(summary_raw.get("runtime_ready_route_count") or 0),
                runtime_blocked_route_count=int(summary_raw.get("runtime_blocked_route_count") or 0),
                backend_unreachable_plane_count=int(summary_raw.get("backend_unreachable_plane_count") or 0),
                next_action_count=int(summary_raw.get("next_action_count") or 0),
            ),
            projection_ids_needing_build=list(bringup_payload.get("projection_ids_needing_build") or []),
            route_runtime_blocked_ids=list(bringup_payload.get("route_runtime_blocked_ids") or []),
            backend_unreachable_planes=list(bringup_payload.get("backend_unreachable_planes") or []),
        )
    return ReadyzSummary(
        ok=bool(data.get("ok")),
        db=str(data.get("db") or ""),
        models=list(data.get("models") or []),
        profile=profile_summary,
        startup_validation=startup_validation,
        bringup=bringup_summary,
    )


def parse_projection_plan_explain_summary(data: Any) -> ProjectionPlanExplainSummary:
    if not isinstance(data, dict):
        raise TypeError("projection plan explain payload must be a mapping")
    status_snapshot: List[ProjectionBuildStateSummary] = []
    for row in data.get("status_snapshot") or []:
        if isinstance(row, dict):
            status_snapshot.append(parse_projection_build_state_summary(row))
    return ProjectionPlanExplainSummary(
        profile_id=str(data.get("profile_id") or ""),
        projection_id=str(data.get("projection_id") or ""),
        projection_version=str(data.get("projection_version") or ""),
        descriptor=dict(data.get("descriptor") or {}),
        actions=[dict(row) for row in data.get("actions") or [] if isinstance(row, dict)],
        status_snapshot=status_snapshot,
        metadata=dict(data.get("metadata") or {}),
    )


def parse_retrieval_plan_explain_summary(data: Any) -> RetrievalPlanExplainSummary:
    if not isinstance(data, dict):
        raise TypeError("retrieval plan explain payload must be a mapping")
    pipeline_raw = data.get("pipeline")
    if not isinstance(pipeline_raw, dict):
        raise ValueError("retrieval plan explain payload is missing 'pipeline'")
    stages: List[RetrievalPlanStageSummary] = []
    for row in pipeline_raw.get("stages") or []:
        if not isinstance(row, dict):
            continue
        stages.append(
            RetrievalPlanStageSummary(
                stage_id=str(row.get("stage_id") or ""),
                primitive_id=(str(row.get("primitive_id")) if row.get("primitive_id") is not None else None),
                enabled=bool(row.get("enabled", True)),
                config=dict(row.get("config") or {}),
                adapter=dict(row.get("adapter") or {}),
            )
        )
    pipeline = RetrievalPlanPipelineSummary(
        pipeline_id=str(pipeline_raw.get("pipeline_id") or ""),
        pipeline_version=str(pipeline_raw.get("pipeline_version") or ""),
        source=(str(pipeline_raw.get("source")) if pipeline_raw.get("source") is not None else None),
        resolution=dict(pipeline_raw.get("resolution") or {}),
        flags=dict(pipeline_raw.get("flags") or {}),
        budgets=dict(pipeline_raw.get("budgets") or {}),
        stages=stages,
    )
    return RetrievalPlanExplainSummary(
        route=str(data.get("route") or ""),
        pipeline=pipeline,
        effective=dict(data.get("effective") or {}),
    )


def parse_projection_refresh_action_summary(data: Any) -> ProjectionRefreshActionSummary:
    if not isinstance(data, dict):
        raise TypeError("projection refresh action payload must be a mapping")
    return ProjectionRefreshActionSummary(
        projection_descriptor_id=str(data.get("projection_descriptor_id") or ""),
        lane_family=str(data.get("lane_family") or ""),
        record_schema=str(data.get("record_schema") or ""),
        adapter_backend=str(data.get("adapter_backend") or ""),
        writer_id=data.get("writer_id"),
        writer_implemented=bool(data.get("writer_implemented")),
        implemented=bool(data.get("implemented")),
        support_state=str(data.get("support_state") or ""),
        mode=str(data.get("mode") or ""),
        current_status=str(data.get("current_status") or ""),
        invalidated_by=list(data.get("invalidated_by") or []),
        notes=data.get("notes"),
    )


def parse_projection_refresh_execution_report_summary(data: Any) -> ProjectionRefreshExecutionReportSummary:
    if not isinstance(data, dict):
        raise TypeError("projection refresh execution report payload must be a mapping")
    return ProjectionRefreshExecutionReportSummary(
        profile_id=str(data.get("profile_id") or ""),
        projection_id=str(data.get("projection_id") or ""),
        executed_actions=[
            parse_projection_refresh_action_summary(row)
            for row in data.get("executed_actions") or []
            if isinstance(row, dict)
        ],
        skipped_actions=[
            parse_projection_refresh_action_summary(row)
            for row in data.get("skipped_actions") or []
            if isinstance(row, dict)
        ],
        metadata=dict(data.get("metadata") or {}),
    )
