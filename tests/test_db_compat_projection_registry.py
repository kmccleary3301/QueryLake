from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.projection_registry import get_projection_descriptor, list_projection_descriptors


def test_projection_registry_contains_expected_descriptors():
    descriptors = list_projection_descriptors()
    assert set(descriptors.keys()) == {
        "file_chunk_lexical_projection_v1",
        "document_chunk_lexical_projection_v1",
        "document_chunk_dense_projection_v1",
        "document_chunk_sparse_projection_v1",
        "segment_lexical_projection_v1",
        "segment_dense_projection_v1",
        "segment_sparse_projection_v1",
        "segment_graph_projection_v1",
    }


def test_projection_descriptor_round_trip_lookup():
    descriptor = get_projection_descriptor("segment_dense_projection_v1")
    assert descriptor.lane_family == "dense"
    assert descriptor.record_schema == "DenseProjectionRecord"
    assert descriptor.authority_model == "document_segment"


def test_document_chunk_compatibility_projection_descriptor_is_explicit():
    descriptor = get_projection_descriptor("document_chunk_lexical_projection_v1")
    assert descriptor.lane_family == "lexical"
    assert descriptor.record_schema == "LexicalProjectionRecord"
    assert descriptor.authority_model == "document_chunk_compatibility"
    assert descriptor.source_scope == "document_chunk"


def test_file_chunk_compatibility_projection_descriptor_is_explicit():
    descriptor = get_projection_descriptor("file_chunk_lexical_projection_v1")
    assert descriptor.lane_family == "lexical"
    assert descriptor.record_schema == "LexicalProjectionRecord"
    assert descriptor.authority_model == "file_chunk_compatibility"
    assert descriptor.source_scope == "file_chunk"
