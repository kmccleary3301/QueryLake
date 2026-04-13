from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import get_deployment_profile
from QueryLake.runtime.local_dense_sidecar import LOCAL_DENSE_SIDECAR_ADAPTER
from QueryLake.runtime.local_projection_writers import SQLiteLocalProjectionWriter
from QueryLake.runtime.projection_contracts import DocumentChunkMaterializationRecord
from QueryLake.runtime.projection_writers import get_projection_writer_runtime, resolve_projection_writer
from QueryLake.runtime.projection_refresh import (
    ProjectionRefreshRequest,
    build_projection_refresh_plan,
    execute_projection_refresh_plan,
    get_projection_build_state,
)


def test_local_profile_projection_writer_resolution_exposes_local_writer_ids(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()

    lexical = resolve_projection_writer("document_chunk_lexical_projection_v1", profile=profile)
    file_lexical = resolve_projection_writer("file_chunk_lexical_projection_v1", profile=profile)
    dense = resolve_projection_writer("document_chunk_dense_projection_v1", profile=profile)

    assert lexical.writer_id == "sqlite_local.projection_writer.lexical.document_chunk_lexical_projection_v1.v1"
    assert lexical.mode == "local_materialize"
    assert lexical.backend == "sqlite_fts5"
    assert lexical.implemented is True

    assert file_lexical.writer_id == "sqlite_local.projection_writer.lexical.file_chunk_lexical_projection_v1.v1"
    assert file_lexical.mode == "local_materialize"
    assert file_lexical.backend == "sqlite_fts5"

    assert dense.writer_id == "sqlite_local.projection_writer.dense.document_chunk.v1"
    assert dense.mode == "local_materialize"
    assert dense.backend == "local_dense_sidecar"


def test_local_profile_projection_writer_runtime_uses_local_scaffold(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()

    resolution = resolve_projection_writer("document_chunk_lexical_projection_v1", profile=profile)
    runtime = get_projection_writer_runtime(resolution)

    assert isinstance(runtime, SQLiteLocalProjectionWriter)
    execution = runtime.execute(
        database=None,
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        adapter_backend="sqlite_fts5",
        authority_reference={"collection_ids": ["c1"]},
        request_metadata={"profile_id": profile.id},
        invalidated_by=["bootstrap"],
    )
    assert execution.implemented is True
    assert execution.mode == "local_materialize"
    assert execution.writer_id == runtime.writer_id
    assert execution.build_revision is not None


def test_local_profile_projection_refresh_plan_is_buildable_and_marks_ready(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    metadata_store_path = tmp_path / "local_projection_store.json"

    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="document_chunk_lexical_projection_v1",
            projection_version="v1",
            collection_ids=["c1"],
        ),
        profile=profile,
        metadata_store_path=str(metadata_store_path),
    )
    assert plan.actions[0].implemented is True
    assert plan.actions[0].writer_implemented is True
    assert plan.actions[0].mode == "rebuild"

    report = execute_projection_refresh_plan(plan, database=None, metadata_store_path=str(metadata_store_path))
    assert len(report.executed_actions) == 1
    build_state = get_projection_build_state(
        projection_id="document_chunk_lexical_projection_v1",
        projection_version="v1",
        lane_family="lexical",
        profile_id=profile.id,
        path=str(metadata_store_path),
    )
    assert build_state is not None
    assert build_state.status == "ready"


def test_local_dense_projection_refresh_warms_sidecar_and_persists_stats(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_DB_PROFILE", "sqlite_fts5_dense_sidecar_local_v1")
    profile = get_deployment_profile()
    metadata_store_path = tmp_path / "local_dense_projection_store.json"
    LOCAL_DENSE_SIDECAR_ADAPTER.reset()
    monkeypatch.setattr(
        "QueryLake.runtime.local_dense_sidecar.fetch_projection_materialization_records",
        lambda database, target: [
            DocumentChunkMaterializationRecord(id="chunk_a", text="alpha", embedding=[1.0, 0.0, 0.0]),
            DocumentChunkMaterializationRecord(id="chunk_b", text="beta", embedding=[0.0, 1.0, 0.0]),
        ],
    )

    plan = build_projection_refresh_plan(
        ProjectionRefreshRequest(
            projection_id="document_chunk_dense_projection_v1",
            projection_version="v1",
            collection_ids=["c1"],
        ),
        profile=profile,
        metadata_store_path=str(metadata_store_path),
    )

    report = execute_projection_refresh_plan(
        plan,
        database=object(),
        metadata_store_path=str(metadata_store_path),
    )

    assert len(report.executed_actions) == 1
    build_state = get_projection_build_state(
        projection_id="document_chunk_dense_projection_v1",
        projection_version="v1",
        lane_family="dense",
        profile_id=profile.id,
        path=str(metadata_store_path),
    )
    assert build_state is not None
    assert build_state.status == "ready"
    assert build_state.metadata["dense_sidecar"]["cache_warmed"] is True
    assert build_state.metadata["dense_sidecar"]["record_count"] == 2
    assert build_state.metadata["dense_sidecar"]["embedding_dimension"] == 3
