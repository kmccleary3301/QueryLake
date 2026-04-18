from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.authority_projection_access import (  # noqa: E402
    FILE_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
    DOCUMENT_CHUNK_COMPAT_DENSE_PROJECTION_ID,
    DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
    SEGMENT_DENSE_PROJECTION_ID,
    SEGMENT_LEXICAL_PROJECTION_ID,
    build_projection_materialization_target,
    build_projection_source_fetch_target,
    fetch_projection_materialization_records,
    fetch_document_chunk_materialization_provenance,
    fetch_projection_materialization_rows,
    fetch_projection_source_rows,
    fetch_projection_source_target,
    build_projection_hydration_target,
    hydrate_projection_target,
    hydrate_projection_rows,
    resolve_projection_source_fetcher,
    resolve_projection_hydrator,
)


def test_projection_hydration_target_uses_projection_descriptor_metadata():
    target = build_projection_hydration_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        record_ids=["chunk-a", "chunk-b"],
    )
    assert target.projection_id == DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID
    assert target.authority_model == "document_chunk_compatibility"
    assert target.source_scope == "document_chunk"
    assert target.record_ids == ("chunk-a", "chunk-b")


def test_document_chunk_compatibility_projection_resolves_hydrator():
    hydrator = resolve_projection_hydrator(DOCUMENT_CHUNK_COMPAT_DENSE_PROJECTION_ID)
    assert hydrator.__class__.__name__ == "DocumentChunkCompatibilityHydrator"


def test_document_chunk_compatibility_projection_resolves_source_fetcher():
    fetcher = resolve_projection_source_fetcher(DOCUMENT_CHUNK_COMPAT_DENSE_PROJECTION_ID)
    assert fetcher.__class__.__name__ == "DocumentChunkCompatibilitySourceFetcher"


def test_file_chunk_compatibility_projection_resolves_hydrator():
    hydrator = resolve_projection_hydrator(FILE_CHUNK_COMPAT_LEXICAL_PROJECTION_ID)
    assert hydrator.__class__.__name__ == "FileChunkCompatibilityHydrator"


def test_file_chunk_compatibility_projection_resolves_source_fetcher():
    fetcher = resolve_projection_source_fetcher(FILE_CHUNK_COMPAT_LEXICAL_PROJECTION_ID)
    assert fetcher.__class__.__name__ == "FileChunkCompatibilitySourceFetcher"


def test_segment_projection_resolves_hydrator():
    hydrator = resolve_projection_hydrator(SEGMENT_DENSE_PROJECTION_ID)
    assert hydrator.__class__.__name__ == "DocumentSegmentAuthorityHydrator"


def test_segment_projection_resolves_source_fetcher():
    fetcher = resolve_projection_source_fetcher(SEGMENT_LEXICAL_PROJECTION_ID)
    assert fetcher.__class__.__name__ == "DocumentSegmentAuthoritySourceFetcher"


def test_projection_source_fetch_target_uses_projection_descriptor_metadata():
    target = build_projection_source_fetch_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={
            "collection_ids": ["c1"],
            "document_ids": ["doc-a"],
            "metadata": {"force_rebuild": True},
        },
    )
    assert target.projection_id == DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID
    assert target.authority_model == "document_chunk_compatibility"
    assert target.source_scope == "document_chunk"
    assert target.collection_ids == ("c1",)
    assert target.document_ids == ("doc-a",)
    assert target.metadata == {"force_rebuild": True}


def test_segment_projection_source_fetch_target_includes_segment_scope():
    target = build_projection_source_fetch_target(
        projection_id=SEGMENT_LEXICAL_PROJECTION_ID,
        authority_reference={
            "collection_ids": ["c1"],
            "document_ids": ["doc-a"],
            "segment_ids": ["seg-a"],
        },
    )
    assert target.authority_model == "document_segment"
    assert target.source_scope == "segment"
    assert target.collection_ids == ("c1",)
    assert target.document_ids == ("doc-a",)
    assert target.segment_ids == ("seg-a",)


def test_projection_materialization_target_uses_descriptor_and_backend_metadata():
    target = build_projection_materialization_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        projection_version="v7",
        authority_reference={
            "authority_model": "document_chunk_compatibility",
            "collection_ids": ["c1"],
            "document_ids": ["doc-a"],
            "metadata": {"force_rebuild": True},
        },
        target_backend_name="opensearch",
        metadata={"profile_id": "aws_aurora_pg_opensearch_v1"},
    )
    assert target.projection_id == DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID
    assert target.projection_version == "v7"
    assert target.authority_model == "document_chunk_compatibility"
    assert target.source_scope == "document_chunk"
    assert target.record_schema == "LexicalProjectionRecord"
    assert target.target_backend_family == "lexical_index"
    assert target.target_backend_name == "opensearch"
    assert target.authority_reference.collection_ids == ["c1"]
    assert target.metadata["profile_id"] == "aws_aurora_pg_opensearch_v1"


def test_hydrate_projection_rows_uses_resolved_hydrator(monkeypatch):
    calls = {}

    class _StubHydrator:
        def hydrate(self, database, record_ids):
            calls["database"] = database
            calls["record_ids"] = tuple(record_ids)
            return {"chunk-a": ("chunk-a", "payload")}

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_hydrator",
        lambda projection_id, descriptor=None: _StubHydrator(),
    )

    hydrated = hydrate_projection_rows(
        object(),
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        record_ids=["chunk-a"],
    )

    assert calls["record_ids"] == ("chunk-a",)
    assert hydrated["chunk-a"] == ("chunk-a", "payload")


def test_hydrate_projection_target_uses_target_record_ids(monkeypatch):
    calls = {}

    class _StubHydrator:
        def hydrate(self, database, record_ids):
            calls["database"] = database
            calls["record_ids"] = tuple(record_ids)
            return {"chunk-b": ("chunk-b", "payload-b")}

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_hydrator",
        lambda projection_id, descriptor=None: _StubHydrator(),
    )

    target = build_projection_hydration_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        record_ids=["chunk-b"],
    )
    hydrated = hydrate_projection_target(object(), target=target)

    assert calls["record_ids"] == ("chunk-b",)
    assert hydrated["chunk-b"] == ("chunk-b", "payload-b")


def test_fetch_projection_source_rows_uses_resolved_fetcher(monkeypatch):
    calls = {}

    class _StubFetcher:
        def fetch(self, database, target):
            calls["database"] = database
            calls["projection_id"] = target.projection_id
            calls["collection_ids"] = tuple(target.collection_ids)
            return ["row-a"]

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_source_fetcher",
        lambda projection_id, descriptor=None: _StubFetcher(),
    )

    fetched = fetch_projection_source_rows(
        object(),
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={"collection_ids": ["c1"]},
    )

    assert calls["projection_id"] == DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID
    assert calls["collection_ids"] == ("c1",)
    assert fetched == ["row-a"]


def test_fetch_projection_source_target_uses_target_scope(monkeypatch):
    calls = {}

    class _StubFetcher:
        def fetch(self, database, target):
            calls["database"] = database
            calls["document_ids"] = tuple(target.document_ids)
            return ["row-b"]

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_source_fetcher",
        lambda projection_id, descriptor=None: _StubFetcher(),
    )

    target = build_projection_source_fetch_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={"document_ids": ["doc-b"]},
    )
    fetched = fetch_projection_source_target(object(), target=target)

    assert calls["document_ids"] == ("doc-b",)
    assert fetched == ["row-b"]


def test_fetch_projection_materialization_rows_uses_authority_reference(monkeypatch):
    calls = {}

    class _StubFetcher:
        def fetch(self, database, target):
            calls["projection_id"] = target.projection_id
            calls["collection_ids"] = tuple(target.collection_ids)
            calls["document_ids"] = tuple(target.document_ids)
            return ["row-m"]

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_source_fetcher",
        lambda projection_id, descriptor=None: _StubFetcher(),
    )

    materialization_target = build_projection_materialization_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={
            "authority_model": "document_chunk_compatibility",
            "collection_ids": ["c9"],
            "document_ids": ["doc-z"],
        },
        target_backend_name="opensearch",
    )
    fetched = fetch_projection_materialization_rows(object(), target=materialization_target)

    assert calls["projection_id"] == DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID
    assert calls["collection_ids"] == ("c9",)
    assert calls["document_ids"] == ("doc-z",)
    assert fetched == ["row-m"]


def test_fetch_projection_materialization_records_normalizes_document_chunk_rows(monkeypatch):
    class _StubFetcher:
        def fetch(self, database, target):
            return [
                {
                    "id": "chunk-1",
                    "text": "hello",
                    "document_id": "doc-1",
                    "collection_id": "col-1",
                    "document_name": "paper.pdf",
                    "creation_timestamp": 12.0,
                    "document_chunk_number": 1,
                    "md": {"kind": "chunk"},
                    "document_md": {"source": "doc"},
                    "embedding": [0.1, 0.2],
                }
            ]

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_source_fetcher",
        lambda projection_id, descriptor=None: _StubFetcher(),
    )

    target = build_projection_materialization_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={"collection_ids": ["col-1"]},
        target_backend_name="opensearch",
    )
    fetched = fetch_projection_materialization_records(object(), target=target)

    assert len(fetched) == 1
    assert fetched[0].id == "chunk-1"
    assert fetched[0].document_id == "doc-1"
    assert fetched[0].embedding == [0.1, 0.2]
    assert fetched[0].compatibility_contract == "canonical_segment_compat_projection_v1"
    assert fetched[0].authority_segment_id is None


def test_fetch_projection_materialization_records_preserves_authority_segment_id(monkeypatch):
    class _StubFetcher:
        def fetch(self, database, target):
            return [
                {
                    "id": "chunk-2",
                    "text": "hello",
                    "document_id": "doc-2",
                    "collection_id": "col-2",
                    "document_name": "paper.pdf",
                    "document_chunk_number": 2,
                    "authority_segment_id": "seg-2",
                    "md": {},
                    "document_md": {},
                }
            ]

    monkeypatch.setattr(
        "QueryLake.runtime.authority_projection_access.resolve_projection_source_fetcher",
        lambda projection_id, descriptor=None: _StubFetcher(),
    )

    target = build_projection_materialization_target(
        projection_id=DOCUMENT_CHUNK_COMPAT_LEXICAL_PROJECTION_ID,
        authority_reference={"collection_ids": ["col-2"]},
        target_backend_name="opensearch",
    )
    fetched = fetch_projection_materialization_records(object(), target=target)

    assert len(fetched) == 1
    assert fetched[0].authority_segment_id == "seg-2"
    assert fetched[0].compatibility_contract == "canonical_segment_compat_projection_v1"


def test_fetch_document_chunk_materialization_provenance_preserves_record_order_and_contract(monkeypatch):
    calls = []

    def _stub_fetch_document_chunk_authority_provenance(database, *, document_id):
        calls.append(document_id)
        payloads = {
            "doc-a": {
                "document_id": "doc-a",
                "records": [
                    {
                        "chunk_id": "chunk-a",
                        "document_chunk_number": 7,
                        "authority_segment_id": "seg-a",
                        "segment_view_id": "sv-a",
                        "segment_view_alias": "default_local_text",
                        "segment_type": "chunk",
                        "segment_index": 7,
                        "member_count": 1,
                        "members": [{"member_index": 0, "unit_id": "u-a"}],
                    }
                ],
            },
            "doc-b": {
                "document_id": "doc-b",
                "records": [
                    {
                        "chunk_id": "chunk-b",
                        "document_chunk_number": 2,
                        "authority_segment_id": "seg-b",
                        "segment_view_id": "sv-b",
                        "segment_view_alias": "default_local_text",
                        "segment_type": "chunk",
                        "segment_index": 2,
                        "member_count": 2,
                        "members": [{"member_index": 0, "unit_id": "u-b1"}, {"member_index": 1, "unit_id": "u-b2"}],
                    }
                ],
            },
        }
        return payloads[document_id]

    monkeypatch.setattr(
        'QueryLake.runtime.authority_projection_access.fetch_document_chunk_authority_provenance',
        _stub_fetch_document_chunk_authority_provenance,
    )

    records = [
        {
            "id": "chunk-b",
            "document_id": "doc-b",
            "document_chunk_number": 2,
            "authority_segment_id": "seg-b",
            "compatibility_contract": "canonical_segment_compat_projection_v1",
            "text": "beta",
        },
        {
            "id": "chunk-a",
            "document_id": "doc-a",
            "document_chunk_number": 7,
            "authority_segment_id": "seg-a",
            "compatibility_contract": "canonical_segment_compat_projection_v1",
            "text": "alpha",
        },
    ]

    payload = fetch_document_chunk_materialization_provenance(object(), records=records)

    assert calls == ["doc-b", "doc-a"]
    assert [row["chunk_id"] for row in payload] == ["chunk-b", "chunk-a"]
    assert payload[0]["compatibility_contract"] == "canonical_segment_compat_projection_v1"
    assert payload[0]["canonical_authority_segment_id"] == "seg-b"
    assert payload[0]["authority_segment_consistent"] is True
    assert payload[0]["member_count"] == 2
    assert payload[1]["canonical_authority_segment_id"] == "seg-a"
    assert payload[1]["segment_view_alias"] == "default_local_text"


def test_fetch_document_chunk_materialization_provenance_surfaces_missing_canonical_row(monkeypatch):
    monkeypatch.setattr(
        'QueryLake.runtime.authority_projection_access.fetch_document_chunk_authority_provenance',
        lambda database, *, document_id: {"document_id": document_id, "records": []},
    )

    payload = fetch_document_chunk_materialization_provenance(
        object(),
        records=[
            {
                "id": "chunk-missing",
                "document_id": "doc-missing",
                "document_chunk_number": 0,
                "authority_segment_id": "seg-missing",
                "text": "orphan",
            }
        ],
    )

    assert len(payload) == 1
    assert payload[0]["chunk_id"] == "chunk-missing"
    assert payload[0]["materialized_authority_segment_id"] == "seg-missing"
    assert payload[0]["canonical_authority_segment_id"] is None
    assert payload[0]["authority_segment_consistent"] is False
    assert payload[0]["member_count"] == 0
