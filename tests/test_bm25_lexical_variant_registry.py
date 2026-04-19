from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.lexical_variant_registry import (
    DEFAULT_LEXICAL_VARIANT_ID,
    get_lexical_variant_spec,
    list_lexical_variant_specs,
)


def test_default_variant_is_current_heuristic_control():
    spec = get_lexical_variant_spec(None)
    assert spec.variant_id == DEFAULT_LEXICAL_VARIANT_ID == "QL-L1"
    assert spec.proximity_mode == "current"


def test_registry_contains_core_week_one_variants():
    ids = {spec.variant_id for spec in list_lexical_variant_specs()}
    assert {"QL-L0", "QL-L1", "QL-L3", "QL-L4", "QL-L5"}.issubset(ids)

