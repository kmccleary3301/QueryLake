from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES, build_profile_diagnostics_payload
from QueryLake.runtime.projection_refresh import mark_projection_build_ready
from scripts.db_compat_profile_smoke import temporary_env


def test_gold_profile_smoke_payload_is_boot_ready(monkeypatch):
    monkeypatch.delenv('QUERYLAKE_DB_PROFILE', raising=False)
    payload = build_profile_diagnostics_payload(profile=DEPLOYMENT_PROFILES['paradedb_postgres_gold_v1'])
    assert payload['startup_validation']['boot_ready'] is True
    assert payload['startup_validation']['profile_implemented'] is True
    assert payload['startup_validation']['declared_executable_routes_runtime_ready'] is True


def test_split_stack_smoke_payload_is_not_boot_ready_until_required_projections_exist(monkeypatch):
    env_map = {
        'QUERYLAKE_DB_PROFILE': 'aws_aurora_pg_opensearch_v1',
        'QUERYLAKE_SEARCH_BACKEND_URL': 'https://example-opensearch.local',
        'QUERYLAKE_SEARCH_INDEX_NAMESPACE': 'querylake',
        'QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS': '1024',
    }
    with temporary_env(env_map):
        payload = build_profile_diagnostics_payload(profile=DEPLOYMENT_PROFILES['aws_aurora_pg_opensearch_v1'])
    assert payload['startup_validation']['profile_implemented'] is True
    assert payload['configuration']['ready'] is True
    assert payload['startup_validation']['boot_ready'] is False
    assert payload['startup_validation']['route_execution_ready'] is True
    assert payload['startup_validation']['route_runtime_ready'] is False
    assert payload['startup_validation']['declared_executable_routes_runtime_ready'] is False
    assert payload['startup_validation']['full_route_coverage_ready'] is True
    assert payload['startup_validation']['non_executable_required_routes'] == []
    assert payload['startup_validation']['non_executable_optional_routes'] == []
    assert sorted(payload['startup_validation']['declared_executable_route_ids']) == [
        'search_bm25.document_chunk',
        'search_file_chunks',
        'search_hybrid.document_chunk',
    ]
    assert payload['startup_validation']['declared_optional_route_ids'] == []
    assert payload['route_summary']['declared_executable_route_count'] == 3
    assert payload['route_summary']['declared_optional_route_count'] == 0
    assert payload['route_summary']['declared_executable_runtime_ready_count'] == 0
    assert sorted(payload['route_summary']['declared_executable_runtime_blocked_ids']) == [
        'search_bm25.document_chunk',
        'search_file_chunks',
        'search_hybrid.document_chunk',
    ]
    routes = {entry['route_id']: entry for entry in payload['route_executors']}
    assert routes['search_hybrid.document_chunk']['implemented'] is True
    assert routes['search_bm25.document_chunk']['implemented'] is True
    assert routes['search_file_chunks']['implemented'] is True
    assert routes['search_hybrid.document_chunk']['runtime_blockers'][0]['kind'] == 'projection_not_ready'


def test_split_stack_smoke_payload_becomes_boot_ready_when_required_projections_are_ready(monkeypatch):
    env_map = {
        'QUERYLAKE_DB_PROFILE': 'aws_aurora_pg_opensearch_v1',
        'QUERYLAKE_SEARCH_BACKEND_URL': 'https://example-opensearch.local',
        'QUERYLAKE_SEARCH_INDEX_NAMESPACE': 'querylake',
        'QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS': '1024',
    }
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        metadata_path = tmp.name
    Path(metadata_path).write_text("{}", encoding="utf-8")
    for projection_id, lane_family, revision in [
        ('document_chunk_lexical_projection_v1', 'lexical', 'smoke:lexical'),
        ('document_chunk_dense_projection_v1', 'dense', 'smoke:dense'),
        ('file_chunk_lexical_projection_v1', 'lexical', 'smoke:file'),
    ]:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version='v1',
            profile_id='aws_aurora_pg_opensearch_v1',
            lane_family=lane_family,
            target_backend='opensearch',
            build_revision=revision,
            path=metadata_path,
        )
    with temporary_env(env_map):
        payload = build_profile_diagnostics_payload(
            profile=DEPLOYMENT_PROFILES['aws_aurora_pg_opensearch_v1'],
            metadata_store_path=metadata_path,
        )
    assert payload['startup_validation']['boot_ready'] is True
    assert payload['startup_validation']['route_runtime_ready'] is True
    assert payload['startup_validation']['declared_executable_routes_runtime_ready'] is True
    assert sorted(payload['startup_validation']['declared_executable_runtime_ready_ids']) == [
        'search_bm25.document_chunk',
        'search_file_chunks',
        'search_hybrid.document_chunk',
    ]
    assert payload['route_summary']['declared_executable_runtime_ready_count'] == 3
    assert payload['route_summary']['declared_executable_runtime_blocked_count'] == 0
    routes = {entry['route_id']: entry for entry in payload['route_executors']}
    assert routes['search_hybrid.document_chunk']['runtime_ready'] is True
    assert routes['search_bm25.document_chunk']['runtime_ready'] is True
    assert routes['search_file_chunks']['runtime_ready'] is True


def test_local_profile_smoke_payload_is_not_runtime_ready_until_required_projections_exist(monkeypatch):
    env_map = {
        'QUERYLAKE_DB_PROFILE': 'sqlite_fts5_dense_sidecar_local_v1',
    }
    with temporary_env(env_map):
        payload = build_profile_diagnostics_payload(profile=DEPLOYMENT_PROFILES['sqlite_fts5_dense_sidecar_local_v1'])
    assert payload['startup_validation']['profile_implemented'] is True
    assert payload['configuration']['ready'] is True
    assert payload['startup_validation']['boot_ready'] is False
    assert payload['startup_validation']['route_execution_ready'] is True
    assert payload['startup_validation']['route_runtime_ready'] is False
    assert payload['startup_validation']['declared_executable_routes_runtime_ready'] is False
    routes = {entry['route_id']: entry for entry in payload['route_executors']}
    assert routes['search_hybrid.document_chunk']['implemented'] is True
    assert routes['search_hybrid.document_chunk']['support_state'] == 'supported'
    assert routes['search_hybrid.document_chunk']['runtime_blockers'][0]['kind'] == 'projection_not_ready'


def test_local_profile_smoke_payload_becomes_runtime_ready_when_required_projections_are_ready(monkeypatch):
    env_map = {
        'QUERYLAKE_DB_PROFILE': 'sqlite_fts5_dense_sidecar_local_v1',
    }
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        metadata_path = tmp.name
    Path(metadata_path).write_text("{}", encoding="utf-8")
    for projection_id, lane_family, target_backend, revision in [
        ('document_chunk_lexical_projection_v1', 'lexical', 'sqlite_fts5', 'smoke:local-lexical'),
        ('document_chunk_dense_projection_v1', 'dense', 'local_dense_sidecar', 'smoke:local-dense'),
        ('file_chunk_lexical_projection_v1', 'lexical', 'sqlite_fts5', 'smoke:local-file'),
    ]:
        mark_projection_build_ready(
            projection_id=projection_id,
            projection_version='v1',
            profile_id='sqlite_fts5_dense_sidecar_local_v1',
            lane_family=lane_family,
            target_backend=target_backend,
            build_revision=revision,
            path=metadata_path,
        )
    with temporary_env(env_map):
        payload = build_profile_diagnostics_payload(
            profile=DEPLOYMENT_PROFILES['sqlite_fts5_dense_sidecar_local_v1'],
            metadata_store_path=metadata_path,
        )
    assert payload['startup_validation']['profile_implemented'] is True
    assert payload['startup_validation']['boot_ready'] is True
    assert payload['startup_validation']['route_runtime_ready'] is True
    assert payload['startup_validation']['declared_executable_routes_runtime_ready'] is True
    assert sorted(payload['startup_validation']['declared_executable_runtime_ready_ids']) == [
        'search_bm25.document_chunk',
        'search_file_chunks',
        'search_hybrid.document_chunk',
    ]
    routes = {entry['route_id']: entry for entry in payload['route_executors']}
    assert routes['search_hybrid.document_chunk']['runtime_ready'] is True
    assert routes['search_bm25.document_chunk']['runtime_ready'] is True
    assert routes['search_file_chunks']['runtime_ready'] is True
