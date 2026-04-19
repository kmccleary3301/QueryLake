from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable


def load_shadow_reports(report_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(report_dir)
    reports: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if payload.get("schema_version") == "canon_shadow_report_v1":
            payload["_path"] = str(path)
            reports.append(payload)
    return reports


def build_shadow_report_index(reports: Iterable[dict[str, Any]]) -> dict[str, Any]:
    report_rows = list(reports)
    divergence_counts: dict[str, int] = {}
    by_route: dict[str, dict[str, Any]] = {}

    for report in report_rows:
        route = str(report.get("route") or "")
        divergence = str(report.get("shadow_diff", {}).get("divergence_class") or "unknown")
        divergence_counts[divergence] = divergence_counts.get(divergence, 0) + 1
        route_row = by_route.setdefault(
            route,
            {
                "route": route,
                "report_count": 0,
                "divergence_counts": {},
                "report_ids": [],
            },
        )
        route_row["report_count"] += 1
        route_row["report_ids"].append(str(report.get("report_id") or ""))
        route_divergence = route_row["divergence_counts"]
        route_divergence[divergence] = route_divergence.get(divergence, 0) + 1

    recommendations: list[str] = []
    if report_rows and divergence_counts.get("candidate_set_delta", 0) == 0:
        recommendations.append("safe_to_expand_shadow_coverage")
    if divergence_counts.get("candidate_set_delta", 0) > 0:
        recommendations.append("investigate_candidate_set_deltas")
    if divergence_counts.get("analysis_incomplete", 0) > 0:
        recommendations.append("strengthen_shadow_artifact_capture")

    return {
        "schema_version": "canon_shadow_report_index_v1",
        "report_count": len(report_rows),
        "divergence_counts": divergence_counts,
        "routes": sorted(by_route.values(), key=lambda row: row["route"]),
        "recommendations": recommendations,
    }


def persist_shadow_report_index(
    *,
    index_payload: dict[str, Any],
    output_path: str | Path,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)
