import json

from scripts.db_compat_local_query_smoke import main


def test_local_query_smoke_executes_declared_slice(capsys):
    assert main(['--json', '--enable-ready-profile-projections']) == 0
    payload = json.loads(capsys.readouterr().out)
    summary = dict(payload['summary'])
    assert summary['all_passed'] is True
    assert summary['dense_sidecar_cache_warmed'] is True
    assert summary['dense_sidecar_cache_warmup_transition_ok'] is True
    transition = dict(payload['dense_sidecar_lifecycle_transition'])
    assert transition['before']['lifecycle_state'] == 'ready_projection_backed_cache_cold'
    assert transition['before']['cache_lifecycle_state'] == 'cache_cold_rebuildable'
    assert transition['after']['lifecycle_state'] == 'ready_cache_warmed'
    assert transition['after']['cache_lifecycle_state'] == 'cache_warmed_process_local'
    assert transition['after']['ready_state_source'] == 'process_local_cache'
    cases = {row['case_id']: dict(row) for row in payload['cases']}
    assert cases['bm25_simple']['top_ids'][0] == 'chunk_a'
    assert cases['bm25_phrase_degraded']['top_ids'][0] == 'chunk_a'
    assert cases['bm25_phrase_degraded']['lexical_support_class'] == 'degraded_supported'
    assert 'chunk_a' in cases['bm25_operator_degraded']['top_ids']
    assert 'chunk_b' in cases['bm25_operator_degraded']['top_ids']
    assert cases['bm25_operator_degraded']['lexical_support_class'] == 'degraded_supported'
    assert cases['hybrid_dense_lexical']['top_ids'][0] == 'chunk_a'
    assert cases['file_chunk_simple']['top_ids'][0] == 'file_a'
    assert cases['bm25_hard_constraint_unsupported']['error']['capability'] == 'retrieval.lexical.hard_constraints'
    assert cases['hybrid_dense_lexical']['dense_sidecar_required'] is True
    assert cases['hybrid_dense_lexical']['dense_sidecar_ready'] is True
