from __future__ import annotations

from QueryLake.canon.control.route_serving_registry import (
    build_candidate_canary_evidence_packet,
    build_primary_cutover_evidence_packet,
    build_route_slice_state,
    load_route_serving_registry,
    record_route_activation,
    record_route_apply_state,
    record_route_package_certification,
    resolve_route_serving_state,
)


def test_route_serving_state_requires_certification_apply_and_activation(tmp_path):
    registry_path = tmp_path / "route_serving_registry.json"
    registry = load_route_serving_registry(registry_path)
    payload = resolve_route_serving_state(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="candidate_primary",
    )

    assert payload["resolved"] is False
    assert "route_activation_missing" in payload["blockers"]


def test_route_serving_state_resolves_candidate_and_primary_when_truth_is_persisted(tmp_path):
    registry_path = tmp_path / "route_serving_registry.json"
    certification = record_route_package_certification(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        certification_state="primary_eligible",
        evidence_ref="evidence://bm25-primary",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
        compile_options={"disable_sparse": True},
    )
    apply_state = record_route_apply_state(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        projection_descriptors=["document_chunk_lexical_projection_v1"],
        config_payload={"namespace": "ql"},
        dependency_payload={"executor_id": "opensearch.search_bm25.document_chunk.v1"},
    )
    record_route_activation(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="candidate_primary",
        pointer_id="ptr-target-candidate",
        package_id="pkg-bm25",
        package_revision="rev-target",
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://candidate",
        rollback_target_pointer_id="ptr-shadow",
        candidate_scope={"audience": "internal"},
    )
    record_route_activation(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="primary",
        pointer_id="ptr-target-primary",
        package_id="pkg-bm25",
        package_revision="rev-target",
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://primary",
        predecessor_pointer_id="ptr-target-candidate",
        rollback_target_pointer_id="ptr-target-candidate",
    )

    registry = load_route_serving_registry(registry_path)
    candidate = resolve_route_serving_state(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="candidate_primary",
    )
    primary = resolve_route_serving_state(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="primary",
    )

    assert certification["package_ref"] == primary["certification"]["package_ref"]
    assert candidate["resolved"] is True
    assert primary["resolved"] is True
    assert primary["apply_state"]["apply_state_ref"] == apply_state["apply_state_ref"]


def test_route_slice_state_distinguishes_eligibility_from_candidate_activation(tmp_path):
    registry_path = tmp_path / "route_serving_registry.json"
    record_route_package_certification(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        certification_state="candidate_eligible",
        evidence_ref="evidence://bm25-candidate",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
    )
    apply_state = record_route_apply_state(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        projection_descriptors=["document_chunk_lexical_projection_v1"],
    )

    registry = load_route_serving_registry(registry_path)
    eligible = build_route_slice_state(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )
    assert eligible["state"] == "candidate_primary_eligible"
    assert eligible["activation"] is None

    record_route_activation(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="candidate_primary",
        pointer_id="ptr-target-candidate",
        package_id="pkg-bm25",
        package_revision="rev-target",
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://candidate",
        rollback_target_pointer_id="ptr-shadow",
        candidate_scope={"scope": "internal_canary"},
    )
    registry = load_route_serving_registry(registry_path)
    active = build_route_slice_state(
        registry=registry,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )

    assert active["state"] == "candidate_primary_active"
    assert active["rollback_ready"] is True


def test_candidate_canary_evidence_packet_reports_active_state_and_rollback_target(tmp_path):
    registry_path = tmp_path / "route_serving_registry.json"
    apply_state = record_route_apply_state(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        projection_descriptors=["document_chunk_lexical_projection_v1"],
    )
    record_route_package_certification(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        certification_state="candidate_eligible",
        evidence_ref="evidence://bm25-candidate",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
    )
    record_route_activation(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="candidate_primary",
        pointer_id="ptr-target-candidate",
        package_id="pkg-bm25",
        package_revision="rev-target",
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://candidate",
        predecessor_pointer_id="ptr-shadow-old",
        rollback_target_pointer_id="ptr-shadow-old",
        candidate_scope={"scope": "bounded_internal_canary"},
    )

    packet = build_candidate_canary_evidence_packet(
        registry=load_route_serving_registry(registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )

    assert packet["candidate_primary_active"] is True
    assert packet["rollback_ready"] is True
    assert packet["summary"]["rollback_target_pointer_id"] == "ptr-shadow-old"
    assert packet["candidate_scope"]["scope"] == "bounded_internal_canary"


def test_primary_cutover_evidence_packet_reports_primary_state_and_rollback_target(tmp_path):
    registry_path = tmp_path / "route_serving_registry.json"
    apply_state = record_route_apply_state(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        projection_descriptors=["document_chunk_lexical_projection_v1"],
    )
    record_route_package_certification(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        package_id="pkg-bm25",
        package_revision="rev-target",
        graph_id="graph-target",
        certification_state="primary_eligible",
        evidence_ref="evidence://bm25-primary",
        target_executor_id="opensearch.search_bm25.document_chunk.v1",
    )
    record_route_activation(
        registry_path=registry_path,
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
        mode="primary",
        pointer_id="ptr-target-primary",
        package_id="pkg-bm25",
        package_revision="rev-target",
        apply_state_ref=apply_state["apply_state_ref"],
        approval_ref="approval://primary",
        predecessor_pointer_id="ptr-target-candidate",
        rollback_target_pointer_id="ptr-target-candidate",
    )

    packet = build_primary_cutover_evidence_packet(
        registry=load_route_serving_registry(registry_path),
        profile_id="planetscale_opensearch_v1",
        route_id="search_bm25.document_chunk",
    )

    assert packet["primary_active"] is True
    assert packet["rollback_ready"] is True
    assert packet["summary"]["predecessor_pointer_id"] == "ptr-target-candidate"
    assert packet["summary"]["rollback_target_pointer_id"] == "ptr-target-candidate"
