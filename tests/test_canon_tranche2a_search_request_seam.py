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
    def __init__(self, authoritative: bool) -> None:
        self.resolution = SimpleNamespace(authoritative=authoritative)


def test_direct_bm25_execution_seam_falls_back_without_canon_env(monkeypatch):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_bm25_route_executor", lambda **kwargs: legacy)

    resolved, canon_contract = search_api._resolve_direct_bm25_execution_seam(
        table="document_chunk",
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is None


def test_direct_bm25_execution_seam_uses_authoritative_canon_contract(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_bm25_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(authoritative=True)

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract = search_api._resolve_direct_bm25_execution_seam(
        table="document_chunk",
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is not None
    assert captured["route_id"] == "search_bm25.document_chunk"
    assert captured["profile_id"] == "planetscale_opensearch_v1"
    assert captured["mode"] == "primary"


def test_direct_file_chunks_execution_seam_uses_authoritative_canon_contract(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_file_chunks_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(authoritative=True)

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract = search_api._resolve_direct_file_chunks_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
    )

    assert resolved is legacy
    assert canon_contract is not None
    assert captured["route_id"] == "search_file_chunks"
    assert captured["profile_id"] == "planetscale_opensearch_v1"
    assert captured["mode"] == "primary"


def test_direct_hybrid_execution_seam_uses_authoritative_canon_contract_when_sparse_disabled(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_hybrid_route_executor", lambda **kwargs: legacy)
    captured = {}

    def _fake_contract(**kwargs):
        captured.update(kwargs)
        return _CanonContract(authoritative=True)

    monkeypatch.setattr(search_api, "resolve_search_plane_a_execution_contract", _fake_contract)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_MODE", "primary")

    resolved, canon_contract = search_api._resolve_direct_hybrid_execution_seam(
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


def test_direct_hybrid_execution_seam_does_not_use_canon_when_sparse_enabled(monkeypatch, tmp_path):
    legacy = _LegacyResolution()
    monkeypatch.setattr(search_api, "resolve_search_hybrid_route_executor", lambda **kwargs: legacy)
    monkeypatch.setenv("QUERYLAKE_CANON_PACKAGE_REGISTRY_PATH", str(tmp_path / "package_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_POINTER_REGISTRY_PATH", str(tmp_path / "pointer_registry.json"))
    monkeypatch.setenv("QUERYLAKE_CANON_ROUTE_SERVING_REGISTRY_PATH", str(tmp_path / "route_serving_registry.json"))

    resolved, canon_contract = search_api._resolve_direct_hybrid_execution_seam(
        profile=SimpleNamespace(id="planetscale_opensearch_v1"),
        return_statement=False,
        use_bm25=True,
        use_similarity=True,
        use_sparse=True,
    )

    assert resolved is legacy
    assert canon_contract is None
