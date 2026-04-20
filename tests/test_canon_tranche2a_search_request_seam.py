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
