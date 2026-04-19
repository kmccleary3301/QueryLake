from __future__ import annotations

from QueryLake.canon.runtime import build_phase1a_bootstrap_bundle


def test_phase1a_bootstrap_bundle_plans_without_mutation(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "1024")
    metadata_path = tmp_path / "projection_store.json"

    payload = build_phase1a_bootstrap_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        projection_ids=["document_chunk_lexical_projection_v1"],
        metadata_store_path=str(metadata_path),
        execute=False,
    )

    assert payload["schema_version"] == "canon_phase1a_bootstrap_bundle_v1"
    assert payload["execute"] is False
    assert payload["summary"]["planned_projection_count"] == 1
    assert payload["summary"]["ready_projection_count_before"] == 0
    assert payload["summary"]["ready_projection_count_after"] == 0
    assert payload["bootstrap_report"] is None
    assert "bootstrap_bundle_plans_refresh_without_mutation" in payload["recommendations"]


def test_phase1a_bootstrap_bundle_executes_and_increases_ready_count(monkeypatch, tmp_path):
    monkeypatch.setenv("QUERYLAKE_SEARCH_BACKEND_URL", "https://search.example.com")
    monkeypatch.setenv("QUERYLAKE_SEARCH_INDEX_NAMESPACE", "ql")
    monkeypatch.setenv("QUERYLAKE_SEARCH_DENSE_VECTOR_DIMENSIONS", "2")
    metadata_path = tmp_path / "projection_store.json"

    def _fake_materializations(database, target):
        projection_id = target.projection_id
        if projection_id == "document_chunk_lexical_projection_v1":
            return [
                {
                    "id": "doc-lex-1",
                    "text": "lex body",
                    "document_id": "doc-1",
                    "document_name": "lex.pdf",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 123.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                }
            ]
        if projection_id == "document_chunk_dense_projection_v1":
            return [
                {
                    "id": "doc-dense-1",
                    "text": "dense body",
                    "document_id": "doc-1",
                    "document_name": "dense.pdf",
                    "website_url": None,
                    "collection_id": "col-1",
                    "creation_timestamp": 123.0,
                    "document_chunk_number": 0,
                    "md": {},
                    "document_md": {},
                    "embedding": [0.25, 0.75],
                }
            ]
        return [
            {
                "id": "file-1",
                "text": "file body",
                "md": {},
                "created_at": 123.0,
                "file_version_id": "fv-1",
                "created_by": "user-1",
                "collection_id": "col-1",
            }
        ]

    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers.fetch_projection_materialization_records",
        _fake_materializations,
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_json_request",
        lambda **kwargs: {"ok": True},
    )
    monkeypatch.setattr(
        "QueryLake.runtime.opensearch_projection_writers._perform_opensearch_bulk",
        lambda **kwargs: {"errors": False, "items": []},
    )

    payload = build_phase1a_bootstrap_bundle(
        profile_id="aws_aurora_pg_opensearch_v1",
        metadata_store_path=str(metadata_path),
        execute=True,
        database=object(),
    )

    assert payload["execute"] is True
    assert payload["summary"]["planned_projection_count"] == 3
    assert payload["summary"]["ready_projection_count_before"] == 0
    assert payload["summary"]["ready_projection_count_after"] == 3
    assert payload["bootstrap_report"] is not None
    assert "bootstrap_bundle_increased_ready_projection_count" in payload["recommendations"]
