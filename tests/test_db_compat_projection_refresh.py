from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    bootstrap_profile_projections,
    build_authority_reference,
    build_projection_diagnostics_payload,
    build_projection_reference,
    build_projection_refresh_plan,
    default_bootstrap_projection_ids,
    execute_projection_refresh_plan,
    explain_projection_refresh_plan,
    get_projection_build_state,
    invalidate_projection_build_states,
    list_projection_build_states,
    mark_projection_build_failed,
    mark_projection_build_ready,
    mark_projection_build_started,
)


def test_projection_reference_is_authority_agnostic():
    ref = build_projection_reference(
        projection_record_id="proj-1",
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        projection_backend="paradedb",
        source_document_id="doc-1",
        source_segment_id="seg-1",
        metadata={"tenant": "personal"},
    )
    assert ref.projection_record_id == "proj-1"
    assert ref.source_document_id == "doc-1"
    assert ref.metadata["tenant"] == "personal"


def test_projection_refresh_plan_for_gold_profile(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="segment_lexical_projection_v1",
            lane_families=["lexical", "dense", "sparse"],
            collection_ids=["c1"],
            metadata={"embedding_revision": "emb-1"},
        ),
        metadata_store_path=str(metadata_path),
    )
    assert plan.profile_id == "paradedb_postgres_gold_v1"
    assert plan.projection_descriptor["projection_id"] == "segment_lexical_projection_v1"
    action_map = {action.lane_family: action for action in plan.actions}
    assert action_map["lexical"].implemented is True
    assert action_map["lexical"].mode == "rebuild"
    assert "collection_scope_changed" in action_map["lexical"].invalidated_by
    assert "embedding_revision_changed" in action_map["lexical"].invalidated_by
    assert action_map["dense"].adapter_backend == "pgvector_halfvec"
    assert action_map["sparse"].support_state == "supported"


def test_projection_refresh_plan_for_planned_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="segment_dense_projection_v1",
            lane_families=["dense", "sparse"],
        ),
        metadata_store_path=str(metadata_path),
    )
    assert plan.profile_id == "aws_aurora_pg_opensearch_v1"
    action_map = {action.lane_family: action for action in plan.actions}
    assert action_map["dense"].implemented is True
    assert action_map["dense"].writer_implemented is True
    assert action_map["dense"].mode == "rebuild"
    assert action_map["dense"].support_state == "supported"
    assert action_map["sparse"].implemented is False
    assert action_map["sparse"].mode == "planned"
    assert action_map["sparse"].support_state == "unsupported"


def test_projection_refresh_plan_for_split_stack_dense_document_chunk_is_rebuildable(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="document_chunk_dense_projection_v1",
            lane_families=["dense"],
            collection_ids=["c1"],
            metadata={"force_rebuild": True},
        ),
        metadata_store_path=str(metadata_path),
    )
    action = plan.actions[0]
    assert action.lane_family == "dense"
    assert action.implemented is True
    assert action.writer_implemented is True
    assert action.mode == "rebuild"


def test_projection_refresh_execution_updates_semi_persistent_state(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    request = ProjectionRefreshRequest(
        projection_id="segment_lexical_projection_v1",
        lane_families=["lexical"],
        collection_ids=["c1"],
        metadata={"force_rebuild": True},
    )
    plan = build_projection_refresh_plan(request, metadata_store_path=str(metadata_path))
    report = execute_projection_refresh_plan(plan, metadata_store_path=str(metadata_path))
    assert len(report.executed_actions) == 1
    state = get_projection_build_state(
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        profile_id="paradedb_postgres_gold_v1",
        path=str(metadata_path),
    )
    assert state is not None
    assert state.status == "ready"
    assert state.target_backend == "paradedb"
    assert state.last_build_revision == "v1:lexical"


def test_projection_build_state_lifecycle_helpers(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    started = mark_projection_build_started(
        projection_id="segment_dense_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_family="dense",
        target_backend="pgvector_halfvec",
        build_revision="v1:dense",
        metadata={"job_id": "job-1"},
        path=str(metadata_path),
    )
    assert started.status == "building"
    ready = mark_projection_build_ready(
        projection_id="segment_dense_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_family="dense",
        target_backend="pgvector_halfvec",
        build_revision="v1:dense",
        metadata={"job_id": "job-1"},
        path=str(metadata_path),
    )
    assert ready.status == "ready"
    failed = mark_projection_build_failed(
        projection_id="segment_dense_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_family="dense",
        target_backend="pgvector_halfvec",
        error_summary="boom",
        path=str(metadata_path),
    )
    assert failed.status == "failed"
    assert failed.error_summary == "boom"


def test_projection_build_state_invalidation_marks_existing_state_stale(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    mark_projection_build_ready(
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_family="lexical",
        target_backend="paradedb",
        build_revision="v1:lexical",
        metadata={"job_id": "job-1"},
        path=str(metadata_path),
    )
    invalidated = invalidate_projection_build_states(
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        profile_id="paradedb_postgres_gold_v1",
        lane_families=["lexical"],
        invalidated_by=["document_scope_changed"],
        path=str(metadata_path),
    )
    assert len(invalidated) == 1
    assert invalidated[0].status == "stale"
    assert invalidated[0].metadata["invalidated_by"] == ["document_scope_changed"]


def test_projection_plan_explain_includes_descriptor_and_status(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    explain = explain_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="segment_sparse_projection_v1",
            lane_families=["sparse"],
            document_ids=["doc-1"],
        ),
        metadata_store_path=str(metadata_path),
    )
    assert explain.descriptor["projection_id"] == "segment_sparse_projection_v1"
    assert explain.actions[0]["lane_family"] == "sparse"
    assert explain.status_snapshot[0]["status"] == "absent"


def test_authority_reference_uses_projection_descriptor(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    request = ProjectionRefreshRequest(
        projection_id="segment_graph_projection_v1",
        segment_ids=["seg-1", "seg-2"],
        metadata={"operator_revision": "ops-1"},
    )
    authority_ref = build_authority_reference(request)
    assert authority_ref.authority_model == "document_segment"
    assert authority_ref.segment_ids == ["seg-1", "seg-2"]
    assert authority_ref.metadata["projection_id"] == "segment_graph_projection_v1"


def test_projection_refresh_plan_includes_projection_target_contract(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="document_chunk_lexical_projection_v1",
            lane_families=["lexical"],
            collection_ids=["c1"],
        ),
        metadata_store_path=str(metadata_path),
    )
    target = dict(plan.metadata["projection_target"])
    assert target["projection_id"] == "document_chunk_lexical_projection_v1"
    assert target["authority_model"] == "document_chunk_compatibility"
    assert target["record_schema"] == "LexicalProjectionRecord"
    assert target["target_backend_name"] == "opensearch"
    assert target["authority_reference"]["collection_ids"] == ["c1"]


def test_list_projection_build_states_filters_by_projection(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="segment_dense_projection_v1",
            lane_families=["dense"],
            document_ids=["doc-1"],
            metadata={"force_rebuild": True},
        ),
        metadata_store_path=str(metadata_path),
    )
    execute_projection_refresh_plan(plan, metadata_store_path=str(metadata_path))
    states = list_projection_build_states(
        projection_id="segment_dense_projection_v1",
        profile_id="paradedb_postgres_gold_v1",
        path=str(metadata_path),
    )
    assert len(states) == 1
    assert states[0].lane_family == "dense"


def test_projection_diagnostics_payload_includes_projection_items(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"
    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="segment_dense_projection_v1",
            lane_families=["dense"],
            document_ids=["doc-1"],
            metadata={"force_rebuild": True},
        ),
        metadata_store_path=str(metadata_path),
    )
    execute_projection_refresh_plan(plan, metadata_store_path=str(metadata_path))

    payload = build_projection_diagnostics_payload(metadata_store_path=str(metadata_path))
    assert payload["profile_id"] == "paradedb_postgres_gold_v1"
    item_map = {item["projection_id"]: item for item in payload["projection_items"]}
    assert item_map["segment_dense_projection_v1"]["executable"] is True
    assert item_map["segment_dense_projection_v1"]["build_status"] == "ready"
    assert item_map["segment_dense_projection_v1"]["materialization_target"]["authority_model"] == "document_segment"
    assert item_map["segment_dense_projection_v1"]["materialization_target"]["source_scope"] == "segment"
    assert item_map["segment_dense_projection_v1"]["materialization_target"]["target_backend_name"] == "pgvector_halfvec"
    assert payload["metadata"]["projection_count"] >= 1
    assert payload["metadata"]["support_state_counts"]["supported"] >= 1


def test_projection_diagnostics_payload_marks_split_stack_sparse_as_unavailable(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    payload = build_projection_diagnostics_payload(metadata_store_path=str(tmp_path / "projection_meta.json"))
    item_map = {item["projection_id"]: item for item in payload["projection_items"]}
    assert item_map["document_chunk_lexical_projection_v1"]["support_state"] == "supported"
    assert item_map["document_chunk_lexical_projection_v1"]["executable"] is True
    assert item_map["document_chunk_lexical_projection_v1"]["action_mode"] == "rebuild"
    assert item_map["document_chunk_sparse_projection_v1"]["support_state"] == "unsupported"
    assert item_map["document_chunk_sparse_projection_v1"]["executable"] is False
    assert item_map["file_chunk_lexical_projection_v1"]["support_state"] == "supported"
    assert item_map["document_chunk_lexical_projection_v1"]["materialization_target"]["target_backend_name"] == "opensearch"
    assert item_map["document_chunk_lexical_projection_v1"]["materialization_target"]["authority_model"] == "document_chunk_compatibility"


def test_projection_refresh_execution_marks_split_stack_segment_dense_ready_with_real_writer(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "3")
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.opensearch_projection_writers as writers_mod

    monkeypatch.setattr(writers_mod, "_ensure_index", lambda index_name, payload=None: None)
    monkeypatch.setattr(writers_mod, "_clear_index", lambda index_name: {"deleted": 0})
    monkeypatch.setattr(
        writers_mod,
        "fetch_projection_materialization_rows",
        lambda database, target: [
            (
                "segment-1",
                "hello world",
                {"lang": "en"},
                1.0,
                "paragraph",
                0,
                "dv-1",
                None,
                "doc-1",
                "Doc One",
                None,
                "col-1",
                [0.1, 0.2, 0.3],
                None,
            ),
            (
                "segment-2",
                "no vector",
                {},
                2.0,
                "paragraph",
                1,
                "dv-1",
                "segment-1",
                "doc-1",
                "Doc One",
                None,
                "col-1",
                None,
                None,
            ),
        ],
    )

    captured = {}

    def _fake_bulk(*, path, lines):
        captured["path"] = path
        captured["lines"] = list(lines)
        return {"errors": False, "items": []}

    monkeypatch.setattr(writers_mod, "_perform_opensearch_bulk", _fake_bulk)

    request = ProjectionRefreshRequest(
        projection_id="segment_dense_projection_v1",
        lane_families=["dense"],
        document_ids=["doc-1"],
    )
    plan = build_projection_refresh_plan(request, metadata_store_path=str(metadata_path))
    report = execute_projection_refresh_plan(plan, database=object(), metadata_store_path=str(metadata_path))

    assert len(report.executed_actions) == 1
    assert report.executed_actions[0].lane_family == "dense"
    state = get_projection_build_state(
        projection_id="segment_dense_projection_v1",
        projection_version="v1",
        lane_family="dense",
        profile_id="aws_aurora_pg_opensearch_v1",
        path=str(metadata_path),
    )
    assert state is not None
    assert state.status == "ready"
    assert state.target_backend == "opensearch"
    assert state.metadata["documents_indexed"] == 2
    assert state.metadata["documents_with_dense_vectors"] == 1
    assert state.metadata["documents_missing_dense_vectors"] == 1
    assert captured["path"] == "_bulk"
    assert captured["lines"][0]["index"]["_id"] == "segment-1"
    assert captured["lines"][1]["embedding"] == [0.1, 0.2, 0.3]
    assert captured["lines"][1]["segment_type"] == "paragraph"
    assert captured["lines"][1]["segment_index"] == 0
    assert captured["lines"][3]["parent_segment_id"] == "segment-1"
    assert "embedding" not in captured["lines"][3]


def test_projection_refresh_execution_marks_split_stack_lexical_ready_with_real_writer(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.opensearch_projection_writers as writers_mod

    monkeypatch.setattr(writers_mod, "_ensure_index", lambda index_name, payload=None: None)
    monkeypatch.setattr(writers_mod, "_clear_index", lambda index_name: {"deleted": 0})
    monkeypatch.setattr(
        writers_mod,
        "fetch_projection_materialization_rows",
        lambda database, target: [
            type(
                "DocRow",
                (),
                {
                    "id": "chunk-1",
                    "text": "hello world",
                    "document_id": "doc-1",
                    "document_name": "Doc One",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 1.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                },
            )()
        ],
    )

    captured = {}

    def _fake_bulk(*, path, lines):
        captured["path"] = path
        captured["lines"] = list(lines)
        return {"errors": False, "items": []}

    monkeypatch.setattr(writers_mod, "_perform_opensearch_bulk", _fake_bulk)

    request = ProjectionRefreshRequest(
        projection_id="document_chunk_lexical_projection_v1",
        lane_families=["lexical"],
        collection_ids=["col-1"],
        metadata={"force_rebuild": True},
    )
    plan = build_projection_refresh_plan(request, metadata_store_path=str(metadata_path))
    report = execute_projection_refresh_plan(plan, database=object(), metadata_store_path=str(metadata_path))

    assert len(report.executed_actions) == 1
    assert report.executed_actions[0].lane_family == "lexical"
    state = get_projection_build_state(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        profile_id="aws_aurora_pg_opensearch_v1",
        path=str(metadata_path),
    )
    assert state is not None
    assert state.status == "ready"
    assert state.target_backend == "opensearch"
    assert state.metadata["documents_indexed"] == 1
    assert captured["path"] == "_bulk"
    assert captured["lines"][0]["index"]["_id"] == "chunk-1"
    assert captured["lines"][1]["text"] == "hello world"


def test_projection_refresh_execution_marks_split_stack_dense_ready_with_real_writer(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "3")
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.opensearch_projection_writers as writers_mod

    monkeypatch.setattr(writers_mod, "_ensure_index", lambda index_name, payload=None: None)
    monkeypatch.setattr(writers_mod, "_clear_index", lambda index_name: {"deleted": 0})
    monkeypatch.setattr(
        writers_mod,
        "fetch_projection_materialization_rows",
        lambda database, target: [
            type(
                "DocRow",
                (),
                {
                    "id": "chunk-1",
                    "text": "hello world",
                    "document_id": "doc-1",
                    "document_name": "Doc One",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 1.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                    "embedding": [0.1, 0.2, 0.3],
                },
            )(),
            type(
                "DocRow",
                (),
                {
                    "id": "chunk-2",
                    "text": "no vector",
                    "document_id": "doc-1",
                    "document_name": "Doc One",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 2.0,
                    "document_chunk_number": 1,
                    "md": {},
                    "document_md": {},
                    "embedding": None,
                },
            )(),
        ],
    )

    captured = {}

    def _fake_bulk(*, path, lines):
        captured["path"] = path
        captured["lines"] = list(lines)
        return {"errors": False, "items": []}

    monkeypatch.setattr(writers_mod, "_perform_opensearch_bulk", _fake_bulk)

    request = ProjectionRefreshRequest(
        projection_id="document_chunk_dense_projection_v1",
        lane_families=["dense"],
        collection_ids=["col-1"],
        metadata={"force_rebuild": True},
    )
    plan = build_projection_refresh_plan(request, metadata_store_path=str(metadata_path))
    report = execute_projection_refresh_plan(plan, database=object(), metadata_store_path=str(metadata_path))

    assert len(report.executed_actions) == 1
    assert report.executed_actions[0].lane_family == "dense"
    state = get_projection_build_state(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        lane_family="dense",
        profile_id="aws_aurora_pg_opensearch_v1",
        path=str(metadata_path),
    )
    assert state is not None
    assert state.status == "ready"
    assert state.target_backend == "opensearch"
    assert state.metadata["documents_indexed"] == 2
    assert state.metadata["documents_with_dense_vectors"] == 1
    assert state.metadata["documents_missing_dense_vectors"] == 1
    assert captured["path"] == "_bulk"
    assert captured["lines"][0]["index"]["_id"] == "chunk-1"
    assert captured["lines"][1]["embedding"] == [0.1, 0.2, 0.3]
    assert "embedding" not in captured["lines"][3]


def test_default_bootstrap_projection_ids_for_split_stack_profile(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    projection_ids = default_bootstrap_projection_ids()
    assert projection_ids == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "file_chunk_lexical_projection_v1",
    ]


def test_bootstrap_profile_projections_executes_required_split_stack_writers_idempotently(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "3")
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.opensearch_projection_writers as writers_mod

    monkeypatch.setattr(writers_mod, "_ensure_index", lambda index_name, payload=None: None)
    monkeypatch.setattr(writers_mod, "_clear_index", lambda index_name: {"deleted": 0})

    def _fake_rows(database, target):
        projection_id = target.projection_id
        if projection_id == "file_chunk_lexical_projection_v1":
            return [
                ("file-row-1", "file content", {}, 1.0, "fv-1", "user-1", "col-1"),
            ]
        if projection_id == "document_chunk_dense_projection_v1":
            return [
                type(
                    "DocRow",
                    (),
                    {
                        "id": "chunk-1",
                        "text": "hello world",
                        "document_id": "doc-1",
                        "document_name": "Doc One",
                        "website_url": None,
                        "collection_id": "col-1",
                        "creation_timestamp": 1.0,
                        "document_chunk_number": 0,
                        "md": {},
                        "document_md": {},
                        "embedding": [0.1, 0.2, 0.3],
                    },
                )()
            ]
        return [
            type(
                "DocRow",
                (),
                {
                    "id": "chunk-1",
                    "text": "hello world",
                    "document_id": "doc-1",
                    "document_name": "Doc One",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 1.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                },
            )()
        ]

    monkeypatch.setattr(writers_mod, "fetch_projection_materialization_rows", _fake_rows)

    captured = {"calls": []}

    def _fake_bulk(*, path, lines):
        captured["calls"].append((path, list(lines)))
        return {"errors": False, "items": []}

    monkeypatch.setattr(writers_mod, "_perform_opensearch_bulk", _fake_bulk)

    report_one = bootstrap_profile_projections(
        database=object(),
        metadata_store_path=str(metadata_path),
    )
    assert report_one.projection_ids == [
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "file_chunk_lexical_projection_v1",
    ]
    assert len(report_one.executed_actions) == 3
    assert report_one.skipped_actions == []
    assert sorted(report_one.ready_projection_ids) == sorted(report_one.projection_ids)
    assert report_one.metadata["lifecycle_outcome_counts"]["materialized_from_absent"] == 3
    assert sorted(report_one.metadata["materialized_projection_ids"]) == sorted(report_one.projection_ids)
    assert len(captured["calls"]) == 3

    report_two = bootstrap_profile_projections(
        database=object(),
        metadata_store_path=str(metadata_path),
    )
    assert report_two.executed_actions == []
    assert len(report_two.skipped_actions) == 3
    assert sorted(report_two.ready_projection_ids) == sorted(report_two.projection_ids)
    assert report_two.metadata["lifecycle_outcome_counts"]["unchanged_ready"] == 3
    assert sorted(report_two.metadata["unchanged_ready_projection_ids"]) == sorted(report_two.projection_ids)
    assert len(captured["calls"]) == 3


def test_bootstrap_profile_projections_includes_per_projection_items(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "aws_aurora_pg_opensearch_v1")
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_meta.json"

    report = bootstrap_profile_projections(
        database=None,
        profile=None,
        projection_ids=["document_chunk_sparse_projection_v1"],
        metadata_store_path=str(metadata_path),
    )
    assert report.metadata["projection_count"] == 1
    assert len(report.projection_items) == 1
    item = report.projection_items[0]
    assert item.projection_id == "document_chunk_sparse_projection_v1"
    assert item.status_before == "absent"
    assert item.status_after == "absent"
    assert item.executed_action_count == 0
    assert item.skipped_action_count == 1
    assert item.runtime_executable is False
    assert item.support_state == "unsupported"
    assert item.lifecycle_outcome == "not_buildable"
    assert report.metadata["lifecycle_outcome_counts"]["not_buildable"] == 1


def test_bootstrap_profile_projections_marks_failed_item_when_execution_raises(monkeypatch, tmp_path):
    monkeypatch.delenv("QUERYLAKE_DB_PROFILE", raising=False)
    metadata_path = tmp_path / "projection_meta.json"

    import QueryLake.runtime.projection_refresh as refresh_mod

    def _boom(*args, **kwargs):
        raise RuntimeError("bootstrap failed")

    monkeypatch.setattr(refresh_mod, "execute_projection_refresh_plan", _boom)

    report = bootstrap_profile_projections(
        database=None,
        profile=None,
        projection_ids=["segment_lexical_projection_v1"],
        metadata_store_path=str(metadata_path),
    )
    assert report.failed_projection_ids == ["segment_lexical_projection_v1"]
    item = report.projection_items[0]
    assert item.status_after == "failed"
    assert item.error_summary == "bootstrap failed"
    assert item.lifecycle_outcome == "failed"
    assert report.metadata["lifecycle_outcome_counts"]["failed"] == 1
    state = get_projection_build_state(
        projection_id="segment_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        profile_id="paradedb_postgres_gold_v1",
        path=str(metadata_path),
    )
    assert state is not None
    assert state.status == "failed"
    assert state.error_summary == "bootstrap failed"
