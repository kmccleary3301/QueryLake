#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text as sql_text

from QueryLake.database.create_db_session import initialize_database_engine
from QueryLake.runtime.retrieval_view_routing import PUBLIC_VIEW_TO_REPRESENTATION, REPRESENTATION_TO_SEGMENT_VIEW_ALIAS


def collect_frontier_lane_status(database) -> Dict[str, Any]:
    rows = database.exec(sql_text(
        """
        SELECT
            COALESCE(sv.view_alias, '') AS view_alias,
            COUNT(s.id) AS segment_count,
            COUNT(DISTINCT sv.document_version_id) AS document_version_count
        FROM document_segment_view sv
        LEFT JOIN document_segment s ON s.segment_view_id = sv.id
        GROUP BY sv.view_alias
        """
    )).all()
    counts = {
        str(row[0]): {
            "segment_count": int(row[1] or 0),
            "document_version_count": int(row[2] or 0),
        }
        for row in rows
    }
    lanes: List[Dict[str, Any]] = []
    for public_view, representation_type in sorted(PUBLIC_VIEW_TO_REPRESENTATION.items()):
        alias = REPRESENTATION_TO_SEGMENT_VIEW_ALIAS.get(representation_type)
        if alias is None:
            status = "compatibility_lane"
            blocker = None
            count_payload = {"segment_count": None, "document_version_count": None}
        else:
            count_payload = counts.get(alias, {"segment_count": 0, "document_version_count": 0})
            if count_payload["segment_count"] > 0:
                status = "materialized"
                blocker = None
            else:
                status = "demoted_absent_materialization"
                blocker = f"no_current_segment_view_materialization:{alias}"
        lanes.append({
            "public_view": public_view,
            "representation_type": representation_type.value,
            "segment_view_alias": alias,
            "status": status,
            "blocker": blocker,
            **count_payload,
        })
    return {
        "schema_version": "document_decomposition_frontier_lane_status_v1",
        "lanes": lanes,
        "summary": {
            "materialized_noncanonical_lane_count": sum(
                1 for row in lanes
                if row["status"] == "materialized" and row["representation_type"] != "canonical_segment_text"
            ),
            "demoted_absent_materialization_count": sum(1 for row in lanes if row["status"] == "demoted_absent_materialization"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Report materialization status for document decomposition retrieval views.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    database, _ = initialize_database_engine(ensure_sparse_bootstrap=False)
    payload = collect_frontier_lane_status(database)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for row in payload["lanes"]:
            print(f"{row['public_view']}: {row['status']} alias={row['segment_view_alias']} segments={row['segment_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
