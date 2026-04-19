from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_route_graph_package_bundle, register_graph_package_bundle
from QueryLake.canon.runtime.search_plane_a_lowering import build_search_plane_a_lowering_bundle


def _build_bundle(route: str, revision: str) -> dict:
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    return build_route_graph_package_bundle(route=route, package_revision=revision)


def _write_shadow_pointer(path, *, bundle: dict, route_id: str, profile_id: str) -> None:
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-19T00:00:00+00:00",
            "shadow_pointer": {
                "pointer_id": "ptr-shadow",
                "graph_id": bundle["graph"]["graph_id"],
                "package_revision": bundle["package_revision"],
                "profile_id": profile_id,
                "route_ids": [route_id],
                "mode": "shadow",
                "metadata": {
                    "package_bindings": {
                        route_id: {
                            "package_id": bundle["package_id"],
                            "package_revision": bundle["package_revision"],
                            "graph_id": bundle["graph"]["graph_id"],
                        }
                    }
                },
            },
            "candidate_primary_pointer": None,
            "primary_pointer": None,
            "history": [],
        },
        path,
    )


def test_search_plane_a_lowering_source_profile_is_executable(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle = _build_bundle("search_bm25.document_chunk", "rev-source")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    _write_shadow_pointer(
        pointer_registry_path,
        bundle=bundle,
        route_id="search_bm25.document_chunk",
        profile_id="aws_aurora_pg_opensearch_v1",
    )

    payload = build_search_plane_a_lowering_bundle(
        route_id="search_bm25.document_chunk",
        profile_id="aws_aurora_pg_opensearch_v1",
        package_registry_path=registry_path,
        pointer_registry_path=pointer_registry_path,
    )

    assert payload["selected_package"]["resolved"] is True
    assert payload["execution_mode"] == "legacy_route_executor_passthrough"
    assert payload["lowering"]["implemented"] is True


def test_search_plane_a_lowering_planned_profile_stays_shadow_only(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle = _build_bundle("search_file_chunks", "rev-target")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    _write_shadow_pointer(
        pointer_registry_path,
        bundle=bundle,
        route_id="search_file_chunks",
        profile_id="planetscale_opensearch_v1",
    )

    payload = build_search_plane_a_lowering_bundle(
        route_id="search_file_chunks",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=registry_path,
        pointer_registry_path=pointer_registry_path,
    )

    assert payload["selected_package"]["resolved"] is True
    assert payload["execution_mode"] == "canon_target_profile_shadow_executor"
    assert payload["execution_contract"]["shadow_executable"] is True
    assert "authority_plane_not_migrated" in payload["blockers"]
    assert payload["search_plane_a_transition"]["schema_version"] == "canon_phase1a_search_plane_a_transition_bundle_v1"
