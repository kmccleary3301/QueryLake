from __future__ import annotations

from QueryLake.canon.control.authority_control_registry import (
    apply_authority_control_bootstrap,
    get_authority_control_bootstrap_entry,
    load_authority_control_registry,
)
from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_phase1a_package_set_bundle, load_graph_package_registry
from QueryLake.canon.runtime.authority_control_bootstrap import build_authority_control_bootstrap_bundle


def _seed_pointer_registry(tmp_path, *, profile_id: str, routes: list[str], disable_sparse: bool = True):
    build_phase1a_package_set_bundle(
        routes=routes,
        package_revision="rev-bootstrap",
        output_dir=tmp_path / "packages",
        registry_path=tmp_path / "package_registry.json",
        route_options=(
            {"search_hybrid.document_chunk": {"disable_sparse": True}} if disable_sparse else None
        ),
    )
    package_registry = load_graph_package_registry(tmp_path / "package_registry.json")
    bindings = {}
    seed = None
    for package in package_registry["packages"]:
        bindings[package["route_id"]] = {
            "package_id": package["package_id"],
            "package_revision": package["package_revision"],
            "graph_id": package["graph_id"],
        }
        if package["route_id"] == "search_bm25.document_chunk":
            seed = package
    assert seed is not None
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-19T00:00:00+00:00",
            "shadow_pointer": {
                "pointer_id": "ptr-shadow",
                "graph_id": seed["graph_id"],
                "package_revision": seed["package_revision"],
                "profile_id": profile_id,
                "route_ids": routes,
                "mode": "shadow",
                "metadata": {"package_bindings": bindings},
            },
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        },
        tmp_path / "pointer_registry.json",
    )


def test_authority_control_bootstrap_bundle_is_ready_to_apply(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PLANETSCALE_DSN", "mysql://planetscale.example.com")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    routes = ["search_bm25.document_chunk", "search_file_chunks", "search_hybrid.document_chunk"]
    _seed_pointer_registry(tmp_path, profile_id="planetscale_opensearch_v1", routes=routes)

    payload = build_authority_control_bootstrap_bundle(
        profile_id="planetscale_opensearch_v1",
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        mode="shadow",
    )

    assert payload["summary"]["candidate_primary_bootstrap_ready"] is True
    assert payload["summary"]["primary_bootstrap_ready"] is False
    assert "authority_control_bootstrap_ready_for_candidate_primary_apply" in payload["recommendations"]


def test_authority_control_bootstrap_apply_persists_scope_entry(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PLANETSCALE_DSN", "mysql://planetscale.example.com")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    routes = ["search_bm25.document_chunk", "search_file_chunks", "search_hybrid.document_chunk"]
    _seed_pointer_registry(tmp_path, profile_id="planetscale_opensearch_v1", routes=routes)
    bundle = build_authority_control_bootstrap_bundle(
        profile_id="planetscale_opensearch_v1",
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
        mode="shadow",
    )

    apply_authority_control_bootstrap(
        bundle=bundle,
        registry_path=tmp_path / "authority_control_registry.json",
    )
    registry = load_authority_control_registry(tmp_path / "authority_control_registry.json")
    entry = get_authority_control_bootstrap_entry(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        mode="shadow",
        routes=routes,
    )

    assert entry is not None
    assert entry["candidate_primary_bootstrap_ready"] is True
