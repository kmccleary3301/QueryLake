from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.package import build_graph_package_bundle, register_graph_package_bundle
from QueryLake.canon.runtime.search_plane_a_execution import (
    build_search_plane_a_execution_contract,
    resolve_search_plane_a_execution_contract,
)
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


def _build_bundle(route: str, revision: str, *, options: dict | None = None) -> dict:
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    pipeline = default_pipeline_for_route("search_hybrid" if route == "search_hybrid.document_chunk" else route)
    assert pipeline is not None
    from QueryLake.canon.compiler.querylake_route_compiler import compile_querylake_route_to_graph

    graph = compile_querylake_route_to_graph(route=route, pipeline=pipeline, options=options or {})
    return build_graph_package_bundle(
        graph=graph,
        route_id=route,
        pipeline=pipeline,
        package_revision=revision,
        compile_options=options,
    )


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


def test_target_profile_search_plane_execution_contract_is_shadow_executable(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle = _build_bundle("search_bm25.document_chunk", "rev-target")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    _write_shadow_pointer(
        pointer_registry_path,
        bundle=bundle,
        route_id="search_bm25.document_chunk",
        profile_id="planetscale_opensearch_v1",
    )

    payload = build_search_plane_a_execution_contract(
        route_id="search_bm25.document_chunk",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=registry_path,
        pointer_registry_path=pointer_registry_path,
    )

    assert payload["execution_mode"] == "canon_target_profile_shadow_executor"
    assert payload["shadow_executable"] is True
    assert payload["primary_ready"] is False
    assert payload["executor_id"] == "opensearch.search_bm25.document_chunk.v1"
    assert "authority_plane_not_migrated" in payload["authority_blockers"]
    assert "control_plane_not_migrated" in payload["authority_blockers"]


def test_target_profile_shadow_execution_contract_can_delegate_to_search_plane(monkeypatch, tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle = _build_bundle("search_bm25.document_chunk", "rev-delegate")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    _write_shadow_pointer(
        pointer_registry_path,
        bundle=bundle,
        route_id="search_bm25.document_chunk",
        profile_id="planetscale_opensearch_v1",
    )

    def _fake_execute(database, **kwargs):
        class _Plan:
            formatted_query = "q"
            quoted_phrases = []

        return _Plan(), [{"id": "doc-1"}]

    monkeypatch.setattr(
        "QueryLake.runtime.retrieval_route_executors.execute_opensearch_document_chunk_bm25_search",
        _fake_execute,
    )

    resolved = resolve_search_plane_a_execution_contract(
        route_id="search_bm25.document_chunk",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=registry_path,
        pointer_registry_path=pointer_registry_path,
    )
    execution = resolved.execute(
        None,
        query="q",
        collection_ids=[],
        sort_by="score",
        sort_dir="desc",
        limit=10,
        offset=0,
        return_statement=False,
    )

    assert execution.formatted_query == "q"
    assert execution.rows_or_statement == [{"id": "doc-1"}]


def test_target_profile_hybrid_execution_contract_blocks_sparse_enabled_package(tmp_path):
    registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    bundle = _build_bundle("search_hybrid.document_chunk", "rev-sparse-default")
    register_graph_package_bundle(bundle=bundle, registry_path=registry_path)
    _write_shadow_pointer(
        pointer_registry_path,
        bundle=bundle,
        route_id="search_hybrid.document_chunk",
        profile_id="planetscale_opensearch_v1",
    )

    payload = build_search_plane_a_execution_contract(
        route_id="search_hybrid.document_chunk",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=registry_path,
        pointer_registry_path=pointer_registry_path,
    )

    assert payload["execution_mode"] == "blocked"
    assert payload["shadow_executable"] is False
    assert "route_executor_not_implemented_on_search_plane_source_profile" in payload["search_plane_blockers"]
