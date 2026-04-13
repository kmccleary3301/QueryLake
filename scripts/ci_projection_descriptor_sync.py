from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.projection_contracts import (
    DenseProjectionRecord,
    GraphProjectionRecord,
    LexicalProjectionRecord,
    SparseProjectionRecord,
)
from QueryLake.runtime.projection_registry import list_projection_descriptors


KNOWN_SCHEMAS = {
    "LexicalProjectionRecord": LexicalProjectionRecord,
    "DenseProjectionRecord": DenseProjectionRecord,
    "SparseProjectionRecord": SparseProjectionRecord,
    "GraphProjectionRecord": GraphProjectionRecord,
}

EXPECTED_LANE_SCHEMA = {
    "lexical": "LexicalProjectionRecord",
    "dense": "DenseProjectionRecord",
    "sparse": "SparseProjectionRecord",
    "graph": "GraphProjectionRecord",
}


def main() -> int:
    descriptors = list_projection_descriptors()
    if not descriptors:
        raise SystemExit("No projection descriptors registered.")

    for projection_id, descriptor in descriptors.items():
        if descriptor.projection_id != projection_id:
            raise SystemExit(
                f"Projection descriptor key mismatch: key={projection_id} descriptor.projection_id={descriptor.projection_id}"
            )
        if descriptor.record_schema not in KNOWN_SCHEMAS:
            known = ", ".join(sorted(KNOWN_SCHEMAS.keys()))
            raise SystemExit(
                f"Projection descriptor '{projection_id}' references unknown record schema '{descriptor.record_schema}'. Known={known}"
            )
        expected_schema = EXPECTED_LANE_SCHEMA.get(descriptor.lane_family)
        if expected_schema is None:
            known = ", ".join(sorted(EXPECTED_LANE_SCHEMA.keys()))
            raise SystemExit(
                f"Projection descriptor '{projection_id}' uses unknown lane_family '{descriptor.lane_family}'. Known={known}"
            )
        if descriptor.record_schema != expected_schema:
            raise SystemExit(
                f"Projection descriptor '{projection_id}' has schema '{descriptor.record_schema}' but lane_family '{descriptor.lane_family}' expects '{expected_schema}'."
            )

    print(f"Projection descriptor registry matches schemas ({len(descriptors)} descriptors).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
