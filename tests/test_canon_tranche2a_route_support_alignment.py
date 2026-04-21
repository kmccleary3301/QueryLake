from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.control.route_serving_registry import (
    record_route_activation,
    record_route_apply_state,
    record_route_package_certification,
)
from QueryLake.canon.package import build_graph_package_bundle, register_graph_package_bundle
from QueryLake.canon.runtime.route_support_alignment import (
    build_route_scoped_support_matrix,
    build_route_slice_support_alignment,
)
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


def _build_bundle(route_id: str = "search_bm25.document_chunk", revision: str = "rev-target", options: dict | None = None) -> dict:
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    from QueryLake.canon.compiler.querylake_route_compiler import compile_querylake_route_to_graph

    pipeline_route = "search_hybrid" if route_id == "search_hybrid.document_chunk" else route_id
    pipeline = default_pipeline_for_route(pipeline_route)
    assert pipeline is not None
    graph = compile_querylake_route_to_graph(
        route=route_id,
        pipeline=pipeline,
        options=dict(options or {}),
    )
    return build_graph_package_bundle(
        graph=graph,
        route_id=route_id,
        pipeline=pipeline,
        package_revision=revision,
        compile_options=dict(options or {}),
    )


def _build_bm25_bundle(revision: str = "rev-target") -> dict:
    return _build_bundle("search_bm25.document_chunk", revision)


def _write_primary_pointer(path, *, bundle: dict) -> None:
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-21T00:00:00+00:00",
            "shadow_pointer": None,
            "candidate_primary_pointer": None,
            "primary_pointer": {
                "pointer_id": "ptr-target-primary",
                "graph_id": bundle["graph"]["graph_id"],
                "package_revision": bundle["package_revision"],
                "profile_id": "planetscale_opensearch_v1",
                "route_ids": ["search_bm25.document_chunk"],
                "mode": "primary",
                "metadata": {
                    "package_bindings": {
                        "search_bm25.document_chunk": {
                            "package_id": bundle["package_id"],
                            "package_revision": bundle["package_revision"],
                            "graph_id": bundle["graph"]["graph_id"],
                        }
                    }
                },
            },
            "history": [],
        },
        path,
    )


def _write_primary_pointer_for_bundles(path, *, bundles: dict[str, dict]) -> None:
    package_bindings = {
        route_id: {
            "package_id": bundle["package_id"],
            "package_revision": bundle["package_revision"],
            "graph_id": bundle["graph"]["graph_id"],
        }
        for route_id, bundle in bundles.items()
    }
    first_bundle = next(iter(bundles.values()))
    save_pointer_registry(
        {
            "schema_version": "canon_pointer_registry_v1",
            "generated_at": "2026-04-21T00:00:00+00:00",
            "shadow_pointer": None,
            "candidate_primary_pointer": None,
            "primary_pointer": {
                "pointer_id": "ptr-target-primary",
                "graph_id": first_bundle["graph"]["graph_id"],
                "package_revision": first_bundle["package_revision"],
                "profile_id": "planetscale_opensearch_v1",
                "route_ids": list(bundles.keys()),
                "mode": "primary",
                "metadata": {"package_bindings": package_bindings},
            },
            "history": [],
        },
        path,
    )


def _route_executor_id(route_id: str) -> str:
    if route_id == "search_file_chunks":
        return "opensearch.search_file_chunks.v1"
    if route_id == "search_hybrid.document_chunk":
        return "opensearch.search_hybrid.document_chunk.v1"
    return "opensearch.search_bm25.document_chunk.v1"


def _route_projection_descriptors(route_id: str) -> list[str]:
    if route_id == "search_file_chunks":
        return ["file_chunk_lexical_projection_v1"]
    if route_id == "search_hybrid.document_chunk":
        return ["document_chunk_lexical_projection_v1", "document_chunk_dense_projection_v1"]
    return ["document_chunk_lexical_projection_v1"]


def _write_primary_serving_truth(path, *, bundle: dict, route_id: str = "search_bm25.document_chunk") -> None:
    record_route_package_certification(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id=route_id,
        package_id=bundle["package_id"],
        package_revision=bundle["package_revision"],
        graph_id=bundle["graph"]["graph_id"],
        certification_state="primary_eligible",
        evidence_ref="evidence://primary",
        target_executor_id=_route_executor_id(route_id),
        compile_options=bundle["pipeline"]["compile_options"],
    )
    apply_state = record_route_apply_state(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id=route_id,
        package_id=bundle["package_id"],
        package_revision=bundle["package_revision"],
        graph_id=bundle["graph"]["graph_id"],
        projection_descriptors=_route_projection_descriptors(route_id),
        config_payload={"namespace": "ql"},
        dependency_payload={"executor_id": _route_executor_id(route_id)},
    )
    record_route_activation(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id=route_id,
        mode="primary",
        pointer_id="ptr-target-primary",
        package_id=bundle["package_id"],
        package_revision=bundle["package_revision"],
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://primary",
        predecessor_pointer_id="ptr-target-candidate",
        rollback_target_pointer_id="ptr-target-candidate",
    )


def test_route_slice_support_alignment_reports_route_scope_without_profile_support(tmp_path):
    package_registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    bundle = _build_bm25_bundle()
    register_graph_package_bundle(bundle=bundle, registry_path=package_registry_path)
    _write_primary_pointer(pointer_registry_path, bundle=bundle)
    _write_primary_serving_truth(route_serving_registry_path, bundle=bundle)

    payload = build_route_slice_support_alignment(
        route_id="search_bm25.document_chunk",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=str(package_registry_path),
        pointer_registry_path=str(pointer_registry_path),
        route_serving_registry_path=str(route_serving_registry_path),
        mode="primary",
    )

    assert payload["runtime_support_state"] == "route_slice_supported"
    assert payload["route_slice_supported"] is True
    assert payload["global_profile_supported"] is False
    assert payload["support_claim_scope"] == "route_slice_only"
    assert "profile_global_support_state_remains_planned" in payload["blockers"]
    assert payload["execution_contract"]["authoritative"] is True


def test_route_slice_support_alignment_reports_file_chunks_route_scope(tmp_path):
    package_registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    bundle = _build_bundle("search_file_chunks", "rev-file-target")
    register_graph_package_bundle(bundle=bundle, registry_path=package_registry_path)
    _write_primary_pointer_for_bundles(pointer_registry_path, bundles={"search_file_chunks": bundle})
    _write_primary_serving_truth(route_serving_registry_path, bundle=bundle, route_id="search_file_chunks")

    payload = build_route_slice_support_alignment(
        route_id="search_file_chunks",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=str(package_registry_path),
        pointer_registry_path=str(pointer_registry_path),
        route_serving_registry_path=str(route_serving_registry_path),
        mode="primary",
    )

    assert payload["variant_label"] == "default"
    assert payload["runtime_support_state"] == "route_slice_supported"
    assert payload["route_slice_supported"] is True
    assert payload["global_profile_supported"] is False
    assert payload["execution_contract"]["executor_id"] == "opensearch.search_file_chunks.v1"


def test_route_slice_support_alignment_reports_sparse_disabled_hybrid_route_scope(tmp_path):
    package_registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    bundle = _build_bundle("search_hybrid.document_chunk", "rev-hybrid-target", {"disable_sparse": True})
    register_graph_package_bundle(bundle=bundle, registry_path=package_registry_path)
    _write_primary_pointer_for_bundles(pointer_registry_path, bundles={"search_hybrid.document_chunk": bundle})
    _write_primary_serving_truth(route_serving_registry_path, bundle=bundle, route_id="search_hybrid.document_chunk")

    payload = build_route_slice_support_alignment(
        route_id="search_hybrid.document_chunk",
        profile_id="planetscale_opensearch_v1",
        package_registry_path=str(package_registry_path),
        pointer_registry_path=str(pointer_registry_path),
        route_serving_registry_path=str(route_serving_registry_path),
        mode="primary",
    )

    assert payload["variant_label"] == "hybrid_sparse_disabled"
    assert payload["runtime_support_state"] == "route_slice_supported"
    assert payload["route_slice_supported"] is True
    assert payload["global_profile_supported"] is False
    assert payload["execution_contract"]["executor_id"] == "opensearch.search_hybrid.document_chunk.v1"
    assert payload["execution_contract"]["compile_options"]["disable_sparse"] is True


def test_route_scoped_support_matrix_reports_only_banked_v5_claims(tmp_path):
    package_registry_path = tmp_path / "package_registry.json"
    pointer_registry_path = tmp_path / "pointer_registry.json"
    route_serving_registry_path = tmp_path / "route_serving_registry.json"
    bundles = {
        "search_bm25.document_chunk": _build_bundle("search_bm25.document_chunk", "rev-bm25-target"),
        "search_file_chunks": _build_bundle("search_file_chunks", "rev-file-target"),
        "search_hybrid.document_chunk": _build_bundle(
            "search_hybrid.document_chunk",
            "rev-hybrid-target",
            {"disable_sparse": True},
        ),
    }
    for bundle in bundles.values():
        register_graph_package_bundle(bundle=bundle, registry_path=package_registry_path)
    _write_primary_pointer_for_bundles(pointer_registry_path, bundles=bundles)
    for route_id, bundle in bundles.items():
        _write_primary_serving_truth(route_serving_registry_path, bundle=bundle, route_id=route_id)

    matrix = build_route_scoped_support_matrix(
        profile_id="planetscale_opensearch_v1",
        package_registry_path=str(package_registry_path),
        pointer_registry_path=str(pointer_registry_path),
        route_serving_registry_path=str(route_serving_registry_path),
        mode="primary",
    )

    assert matrix["schema_version"] == "canon_route_scoped_support_matrix_v1"
    assert matrix["global_profile_supported"] is False
    assert matrix["support_claim_scope"] == "route_slice_only"
    assert matrix["supported_route_claim_count"] == 3
    assert matrix["deferred_route_variant_count"] == 1
    rows = {
        (row["route_id"], row["variant_label"]): row
        for row in matrix["rows"]
    }
    assert rows[("search_bm25.document_chunk", "default")]["route_slice_supported"] is True
    assert rows[("search_file_chunks", "default")]["route_slice_supported"] is True
    assert rows[("search_hybrid.document_chunk", "hybrid_sparse_disabled")]["route_slice_supported"] is True
    sparse_enabled = rows[("search_hybrid.document_chunk", "hybrid_sparse_enabled")]
    assert sparse_enabled["route_slice_supported"] is False
    assert sparse_enabled["deferred"] is True
    assert sparse_enabled["support_claim_scope"] == "not_claimed"
    assert "route_variant_deferred_to_future_phase" in sparse_enabled["blockers"]
