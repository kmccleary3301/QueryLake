from pathlib import Path

from scripts.document_decomposition_segment_retrieval_parity import compare_ranked_ids


def test_compare_ranked_ids_reports_overlap_and_drift():
    payload = compare_ranked_ids(
        baseline_ids=["s1", "s2", "s3"],
        candidate_ids=["s2", "s4", "s3"],
        k=3,
    )
    assert payload["overlap_count"] == 2
    assert payload["overlap_at_k"] == 2 / 3
    assert payload["recall_against_baseline_at_k"] == 2 / 3
    assert payload["missing_from_candidate"] == ["s1"]
    assert payload["candidate_only"] == ["s4"]


def test_compare_ranked_ids_handles_empty_baseline():
    payload = compare_ranked_ids(baseline_ids=[], candidate_ids=["s1"], k=5)
    assert payload["baseline_count"] == 0
    assert payload["recall_against_baseline_at_k"] == 1.0
    assert payload["candidate_only"] == ["s1"]


def test_segment_retrieval_parity_uses_persisted_segment_tsvector():
    text = Path("scripts/document_decomposition_segment_retrieval_parity.py").read_text(encoding="utf-8")
    assert "s.ts_content @@ q.query" in text
    assert "ts_rank_cd(s.ts_content, q.query)" in text
    assert "to_tsvector('english', s.text)" not in text
