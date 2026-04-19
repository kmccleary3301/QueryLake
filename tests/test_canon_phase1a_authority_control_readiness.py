from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_phase1a_package_set_bundle, load_graph_package_registry
from QueryLake.canon.runtime.authority_control_readiness import build_authority_control_readiness_bundle


def _seed_pointer_registry(tmp_path, *, profile_id: str, routes: list[str], disable_sparse: bool = True):
    build_phase1a_package_set_bundle(
        routes=routes,
        package_revision="rev-authority",
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


def test_authority_control_readiness_surfaces_target_shadow_executable_routes(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.setenv("QUERYLAKE_PLANETSCALE_DSN", "mysql://planetscale.example.com")
    monkeypatch.setenv("QUERYLAKE_SPARSE_INDEX_DIMENSIONS", "8192")
    routes = [
        "search_bm25.document_chunk",
        "search_file_chunks",
        "search_hybrid.document_chunk",
    ]
    _seed_pointer_registry(tmp_path, profile_id="planetscale_opensearch_v1", routes=routes, disable_sparse=True)

    payload = build_authority_control_readiness_bundle(
        profile_id="planetscale_opensearch_v1",
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
    )

    assert payload["summary"]["route_count"] == 3
    assert payload["summary"]["selected_package_resolved_count"] == 3
    assert payload["summary"]["shadow_executable_count"] == 3
    assert payload["summary"]["candidate_primary_ready"] is True
    assert payload["summary"]["primary_ready"] is False
    assert payload["summary"]["authority_blocked_count"] == 3
    assert payload["summary"]["control_blocked_count"] == 3
    assert "target_profile_search_plane_shadow_execution_covers_bounded_routes" in payload["recommendations"]


def test_authority_control_readiness_requires_target_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    monkeypatch.delenv("QUERYLAKE_PLANETSCALE_HOST", raising=False)
    routes = ["search_bm25.document_chunk"]
    _seed_pointer_registry(tmp_path, profile_id="planetscale_opensearch_v1", routes=routes, disable_sparse=True)

    payload = build_authority_control_readiness_bundle(
        profile_id="planetscale_opensearch_v1",
        routes=routes,
        package_registry_path=str(tmp_path / "package_registry.json"),
        pointer_registry_path=str(tmp_path / "pointer_registry.json"),
    )

    assert payload["configuration"]["ready"] is False
    assert payload["summary"]["candidate_primary_ready"] is False
    assert "complete_required_target_profile_configuration" in payload["recommendations"]
