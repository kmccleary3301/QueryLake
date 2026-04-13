from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.retrieval_adapter_interfaces import (
    DenseRetrievalAdapterProtocol,
    GoldDenseRetrievalAdapter,
    GoldLexicalRetrievalAdapter,
    GoldSparseRetrievalAdapter,
    LexicalRetrievalAdapterProtocol,
    SparseRetrievalAdapterProtocol,
    get_gold_adapter_bundle,
)


def test_gold_adapter_bundle_exposes_expected_ids():
    bundle = get_gold_adapter_bundle()
    assert bundle["lexical"].adapter_id == "paradedb_bm25_v1"
    assert bundle["dense"].adapter_id == "pgvector_halfvec_v1"
    assert bundle["sparse"].adapter_id == "pgvector_sparsevec_v1"


def test_gold_adapters_satisfy_protocols():
    assert isinstance(GoldLexicalRetrievalAdapter(), LexicalRetrievalAdapterProtocol)
    assert isinstance(GoldDenseRetrievalAdapter(), DenseRetrievalAdapterProtocol)
    assert isinstance(GoldSparseRetrievalAdapter(), SparseRetrievalAdapterProtocol)
