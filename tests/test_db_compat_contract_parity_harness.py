from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import DEPLOYMENT_PROFILES
from scripts.db_compat_contract_parity import (
    _projection_metadata_fixture_path,
    evaluate_cases,
    load_cases,
)


def test_contract_parity_harness_reports_partial_split_stack_execution():
    cases = load_cases(Path('tests/fixtures/db_compat_contract_parity_cases.json'))
    payload = evaluate_cases(
        cases=cases,
        profiles=[
            DEPLOYMENT_PROFILES['paradedb_postgres_gold_v1'],
            DEPLOYMENT_PROFILES['aws_aurora_pg_opensearch_v1'],
        ],
    )
    metrics = payload['metrics']
    assert metrics['case_count'] == 6
    assert metrics['gold_executable_count'] == 6
    assert metrics['split_executable_count'] == 5
    assert metrics['split_runtime_ready_count'] == 0
    assert metrics['unsupported_case_count'] >= 1
    by_id = {entry['case_id']: entry for entry in payload['cases']}
    assert by_id['bm25_simple']['summary']['split_executable'] is True
    assert by_id['hybrid_dense_lexical']['summary']['split_executable'] is True
    assert by_id['hybrid_three_lane']['summary']['split_executable'] is False
    assert by_id['file_chunk_simple']['summary']['split_executable'] is True
    assert by_id['file_chunk_simple']['summary']['split_runtime_ready'] is False
    assert by_id['bm25_phrase']['profiles']['aws_aurora_pg_opensearch_v1']['lexical_plan']['degraded_capabilities'] == [
        'retrieval.lexical.advanced_operators',
        'retrieval.lexical.phrase_boost',
    ]


def test_contract_parity_harness_can_report_ready_split_stack_runtime():
    cases = load_cases(Path('tests/fixtures/db_compat_contract_parity_cases.json'))
    profiles = [
        DEPLOYMENT_PROFILES['paradedb_postgres_gold_v1'],
        DEPLOYMENT_PROFILES['aws_aurora_pg_opensearch_v1'],
    ]
    payload = evaluate_cases(cases=cases, profiles=profiles, metadata_store_path=None)
    assert payload['metrics']['split_runtime_ready_count'] == 0

    metadata_path = _projection_metadata_fixture_path(
        profiles=profiles,
        enable_ready_split_stack=True,
    )
    ready_payload = evaluate_cases(
        cases=cases,
        profiles=profiles,
        metadata_store_path=metadata_path,
    )
    assert ready_payload['metrics']['case_count'] == 6
    assert ready_payload['metrics']['split_runtime_ready_count'] == 4
    assert ready_payload['metrics']['runtime_ready_overlap_count'] == 4
    by_id = {entry['case_id']: entry for entry in ready_payload['cases']}
    assert by_id['bm25_simple']['summary']['split_runtime_ready'] is True
    assert by_id['bm25_phrase']['summary']['split_runtime_ready'] is True
    assert by_id['hybrid_dense_lexical']['summary']['split_runtime_ready'] is True
    assert by_id['file_chunk_simple']['summary']['split_runtime_ready'] is True
