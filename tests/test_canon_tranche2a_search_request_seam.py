from __future__ import annotations

from types import SimpleNamespace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.api import search as search_api


class _LegacyResolution:
    def __init__(self, marker: str = "legacy") -> None:
        self.marker = marker


class _CanonContract:
    def __init__(
        self,
        *,
        authoritative: bool,
        route_id: str = "search_bm25.document_chunk",
        profile_id: str = "planetscale_opensearch_v1",
    ) -> None:
        self.resolution = SimpleNamespace(
            authoritative=authoritative,
            route_id=route_id,
            profile_id=profile_id,
            execution_mode=(
                "canon_target_profile_authoritative_executor"
                if authoritative
                else "canon_target_profile_shadow_executor"
            ),
            primary_ready=authoritative,
            executor_id=f"{route_id}.executor",
            selected_package={"package": {"package_ref": f"{route_id}@test"}},
            search_plane_blockers=[],
            authority_blockers=[] if authoritative else ["authority_plane_not_migrated"],
        )


def test_direct_bm25_execution_seam_falls_back_without_canon_env(monkeypatch):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_bm25_route_executor", lambda **kwargs: legacy)

    resolved, canon_contract, seam = search_api._resolve_direct_bm25_execution_seam(
        table="document_chunk",
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is None
    assert seam["schema"] == "canon_direct_execution_seam_v1"
    assert seam["execution_seam"] == "legacy_fallback"
    assert seam["fallback_reason"] == "canon_registry_env_missing"
    assert seam["route_id"] == "search_bm25.document_chunk"
    assert seam["profile_id"] == "planetscale_opensearch_v1"


def test_direct_bm25_execution_seam_uses_authoritative_canon_contract(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_bm25_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(
            authoritative=True,
            route_id=kwargs["route_id"],
            profile_id=kwargs["profile_id"],
        )

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract, seam = search_api._resolve_direct_bm25_execution_seam(
        table="document_chunk",
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is not None
    assert captured["route_id"] == "search_bm25.document_chunk"
    assert captured["profile_id"] == "planetscale_opensearch_v1"
    assert captured["mode"] == "primary"
    assert seam["execution_seam"] == "canon_authoritative"
    assert seam["fallback_reason"] is None
    assert seam["canon_execution_mode"] == "canon_target_profile_authoritative_executor"
    assert seam["canon_package_ref"] == "search_bm25.document_chunk@test"
    assert seam["authoritative"] is True
    assert seam["primary_ready"] is True


def test_direct_file_chunks_execution_seam_uses_authoritative_canon_contract(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_file_chunks_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(
            authoritative=True,
            route_id=kwargs["route_id"],
            profile_id=kwargs["profile_id"],
        )

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract, seam = search_api._resolve_direct_file_chunks_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is not None
    assert captured["route_id"] == "search_file_chunks"
    assert captured["profile_id"] == "planetscale_opensearch_v1"
    assert captured["mode"] == "primary"
    assert seam["execution_seam"] == "canon_authoritative"
    assert seam["route_id"] == "search_file_chunks"
    assert seam["canon_package_ref"] == "search_file_chunks@test"


def test_direct_hybrid_execution_seam_uses_authoritative_canon_contract_when_sparse_disabled(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_hybrid_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(
            authoritative=True,
            route_id=kwargs["route_id"],
            profile_id=kwargs["profile_id"],
        )

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract, seam = search_api._resolve_direct_hybrid_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
        use_bm25=True,
        use_similarity=True,
        use_sparse=False,
    )

    assert resolved is legacy
    assert canon_contract is not None
    assert captured["route_id"] == "search_hybrid.document_chunk"
    assert captured["profile_id"] == "planetscale_opensearch_v1"
    assert captured["mode"] == "primary"
    assert seam["execution_seam"] == "canon_authoritative"
    assert seam["variant_label"] == "hybrid_sparse_disabled"
    assert seam["canon_package_ref"] == "search_hybrid.document_chunk@test"


def test_direct_hybrid_execution_seam_does_not_use_canon_when_sparse_enabled(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_hybrid_route_executor", lambda **kwargs: legacy)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))

    resolved, canon_contract, seam = search_api._resolve_direct_hybrid_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
        use_bm25=True,
        use_similarity=True,
        use_sparse=True,
    )

    assert resolved is legacy
    assert canon_contract is None
    assert seam["execution_seam"] == "legacy_fallback"
    assert seam["fallback_reason"] == "sparse_enabled_variant_deferred"
    assert seam["variant_label"] == "hybrid_sparse_enabled"


def test_direct_bm25_execution_seam_reports_non_authoritative_contract(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_bm25_route_executor", lambda **kwargs: legacy)

    def _fake_contract(**kwargs):
        return _CanonContract(
            authoritative=False,
            route_id=kwargs["route_id"],
            profile_id=kwargs["profile_id"],
        )

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))

    resolved, canon_contract, seam = search_api._resolve_direct_bm25_execution_seam(
        table="document_chunk",
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is None
    assert seam["execution_seam"] == "legacy_fallback"
    assert seam["fallback_reason"] == "canon_contract_not_authoritative"
    assert seam["canon_execution_mode"] == "canon_target_profile_shadow_executor"
    assert seam["authority_blockers"] == ["authority_plane_not_migrated"]


def test_direct_file_chunks_execution_seam_reports_plan_only(monkeypatch):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_file_chunks_route_executor", lambda **kwargs: legacy)

    resolved, canon_contract, seam = search_api._resolve_direct_file_chunks_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=True,
    )

    assert resolved is legacy
    assert canon_contract is None
    assert seam["execution_seam"] == "plan_only"
    assert seam["fallback_reason"] == "plan_only_request"
