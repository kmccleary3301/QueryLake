from __future__ import annotations

from QueryLake.canon.control.pointer_registry import save_pointer_registry
from QueryLake.canon.control.route_serving_registry import (
    record_route_activation,
    record_route_apply_state,
    record_route_package_certification,
)
from QueryLake.canon.package import build_graph_package_bundle, register_graph_package_bundle
from QueryLake.canon.runtime.route_support_alignment import build_route_slice_support_alignment
from QueryLake.runtime.retrieval_pipeline_runtime import default_pipeline_for_route


def _build_bm25_bundle(revision: str = "rev-target") -> dict:
    import os

    os.environ["QUERYLAKE_SEARCH_INDEX_NAMESPACE"] = "ql"
    os.environ["QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS"] = "1024"
    from QueryLake.canon.compiler.querylake_route_compiler import compile_querylake_route_to_graph

    pipeline = default_pipeline_for_route("search_bm25.document_chunk")
    assert pipeline is not None
    graph = compile_querylake_route_to_graph(
        route="search_bm25.document_chunk",
        pipeline=pipeline,
        options={},
    )
    return build_graph_package_bundle(
        graph=graph,
        route_id="search_bm25.document_chunk",
        pipeline=pipeline,
        package_revision=revision,
        compile_options={},
    )


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


def _write_primary_serving_truth(path, *, bundle: dict) -> None:
    record_route_package_certification(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id=bundle["package_id"],
        package_revision=bundle["package_revision"],
        graph_id=bundle["graph"]["graph_id"],
        certification_state="primary_eligible",
        evidence_ref="evidence://primary",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
        compile_options=bundle["pipeline"]["compile_options"],
    )
    apply_state = record_route_apply_state(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id=bundle["package_id"],
        package_revision=bundle["package_revision"],
        graph_id=bundle["graph"]["graph_id"],
        projection_descriptors=["document_chunk_lexical_projection_v1"],
        config_payload={"namespace": "ql"},
        dependency_payload={"executor_id": "opensearch.search_bm25.document_chunk.v1"},
    )
    record_route_activation(
        registry_path=path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
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
