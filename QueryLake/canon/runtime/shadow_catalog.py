from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any, Iterable


_SCHEMA_TO_KIND = {
    "canon_shadow_report_v1": "report",
    "canon_shadow_replay_bundle_v1": "replay_bundle",
    "canon_shadow_trace_export_v1": "trace_export",
    "canon_shadow_report_index_v1": "report_index",
}


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _parse_generated_at(value: str | None) -> datetime:
    raw = str(value or "").strip()
    if not raw:
        return datetime.fromtimestamp(0, tz=UTC)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return datetime.fromtimestamp(0, tz=UTC)


def _correlation_key(kind: str, payload: dict[str, Any]) -> str:
    route = str(payload.get("route") or "")
    if kind == "report":
        report_id = str(payload.get("report_id") or "")
        return report_id.removeprefix("canon-shadow-") or report_id or route
    if kind == "replay_bundle":
        bundle_id = str(payload.get("bundle_id") or "")
        return bundle_id.removeprefix("canon-shadow-bundle-") or bundle_id or route
    if kind == "trace_export":
        export_id = str(payload.get("export_id") or "")
        return export_id.removeprefix("canon-shadow-traces-") or export_id or route
    if kind == "report_index":
        return str(payload.get("route") or "index")
    return str(payload.get("route") or "")


def load_shadow_artifacts(root_dir: str | Path) -> list[dict[str, Any]]:
    directory = Path(root_dir)
    artifacts: list[dict[str, Any]] = []
    for path in sorted(directory.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        schema_version = str(payload.get("schema_version") or "")
        kind = _SCHEMA_TO_KIND.get(schema_version)
        if kind is None:
            continue
        payload["_path"] = str(path)
        payload["_artifact_kind"] = kind
        payload["_correlation_key"] = _correlation_key(kind, payload)
        artifacts.append(payload)
    return artifacts


def build_shadow_artifact_catalog(artifacts: Iterable[dict[str, Any]]) -> dict[str, Any]:
    rows = list(artifacts)
    counts = {kind: 0 for kind in sorted(set(_SCHEMA_TO_KIND.values()))}
    by_route: dict[str, dict[str, Any]] = {}
    by_correlation: dict[str, dict[str, Any]] = {}
    latest_generated_at = datetime.fromtimestamp(0, tz=UTC)

    for payload in rows:
        kind = str(payload.get("_artifact_kind") or "")
        route = str(payload.get("route") or "")
        counts[kind] = counts.get(kind, 0) + 1
        generated_at = _parse_generated_at(payload.get("generated_at"))
        if generated_at > latest_generated_at:
            latest_generated_at = generated_at

        correlation_key = str(payload.get("_correlation_key") or "")
        if kind != "report_index":
            linked = by_correlation.setdefault(
                correlation_key,
                {
                    "correlation_key": correlation_key,
                    "route": route,
                    "report_id": None,
                    "bundle_id": None,
                    "trace_export_id": None,
                    "paths": [],
                },
            )
            linked["route"] = linked["route"] or route
            if kind == "report":
                linked["report_id"] = str(payload.get("report_id") or "")
            elif kind == "replay_bundle":
                linked["bundle_id"] = str(payload.get("bundle_id") or "")
            elif kind == "trace_export":
                linked["trace_export_id"] = str(payload.get("export_id") or "")
            linked["paths"].append(str(payload.get("_path") or ""))

        route_row = by_route.setdefault(
            route,
            {
                "route": route,
                "report_count": 0,
                "bundle_count": 0,
                "trace_export_count": 0,
                "index_count": 0,
                "candidate_set_delta_count": 0,
                "analysis_incomplete_count": 0,
                "latest_generated_at": None,
            },
        )
        if kind == "report":
            route_row["report_count"] += 1
            divergence = str(payload.get("shadow_diff", {}).get("divergence_class") or "")
            if divergence == "candidate_set_delta":
                route_row["candidate_set_delta_count"] += 1
            if divergence == "analysis_incomplete":
                route_row["analysis_incomplete_count"] += 1
        elif kind == "replay_bundle":
            route_row["bundle_count"] += 1
        elif kind == "trace_export":
            route_row["trace_export_count"] += 1
        elif kind == "report_index":
            route_row["index_count"] += 1
        current_latest = _parse_generated_at(route_row["latest_generated_at"])
        if generated_at > current_latest:
            route_row["latest_generated_at"] = payload.get("generated_at")

    orphan_correlation_keys = sorted(
        row["correlation_key"]
        for row in by_correlation.values()
        if row["report_id"] is None or row["bundle_id"] is None or row["trace_export_id"] is None
    )

    recommendations: list[str] = []
    if rows and not orphan_correlation_keys:
        recommendations.append("shadow_artifacts_structurally_complete")
    if orphan_correlation_keys:
        recommendations.append("repair_missing_shadow_artifacts")
    if any(route_row["candidate_set_delta_count"] > 0 for route_row in by_route.values()):
        recommendations.append("investigate_candidate_set_deltas")
    if any(route_row["analysis_incomplete_count"] > 0 for route_row in by_route.values()):
        recommendations.append("strengthen_shadow_artifact_capture")

    return {
        "schema_version": "canon_shadow_artifact_catalog_v1",
        "generated_at": _utc_now(),
        "artifact_count": len(rows),
        "counts": counts,
        "latest_generated_at": latest_generated_at.isoformat(),
        "routes": sorted(by_route.values(), key=lambda row: row["route"]),
        "correlated_runs": sorted(by_correlation.values(), key=lambda row: row["correlation_key"]),
        "orphan_correlation_keys": orphan_correlation_keys,
        "recommendations": recommendations,
    }


def build_shadow_retention_plan(
    artifacts: Iterable[dict[str, Any]],
    *,
    keep_latest_per_route: int = 10,
) -> dict[str, Any]:
    rows = [row for row in artifacts if str(row.get("_artifact_kind") or "") == "report"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(str(row.get("route") or ""), []).append(row)

    prune_paths: list[str] = []
    kept_report_ids: list[str] = []
    for route, reports in grouped.items():
        sorted_reports = sorted(
            reports,
            key=lambda payload: _parse_generated_at(payload.get("generated_at")),
            reverse=True,
        )
        keep = sorted_reports[:keep_latest_per_route]
        prune = sorted_reports[keep_latest_per_route:]
        kept_keys = {str(report.get("_correlation_key") or "") for report in keep}
        kept_report_ids.extend(str(report.get("report_id") or "") for report in keep)

        related_rows = [row for row in artifacts if str(row.get("route") or "") == route]
        for related in related_rows:
            if str(related.get("_correlation_key") or "") not in kept_keys and str(related.get("_artifact_kind") or "") != "report_index":
                prune_paths.append(str(related.get("_path") or ""))

    return {
        "schema_version": "canon_shadow_retention_plan_v1",
        "generated_at": _utc_now(),
        "keep_latest_per_route": int(keep_latest_per_route),
        "kept_report_ids": sorted(set(kept_report_ids)),
        "prune_paths": sorted(set(prune_paths)),
        "prune_count": len(set(prune_paths)),
    }


def persist_shadow_artifact_catalog(
    *,
    catalog: dict[str, Any],
    output_path: str | Path,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def persist_shadow_retention_plan(
    *,
    plan: dict[str, Any],
    output_path: str | Path,
) -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return str(path)


def apply_shadow_retention_plan(
    plan: dict[str, Any],
    *,
    dry_run: bool = True,
) -> dict[str, Any]:
    prune_paths = [str(path) for path in plan.get("prune_paths") or []]
    removed: list[str] = []
    missing: list[str] = []
    for raw_path in prune_paths:
        path = Path(raw_path)
        if not path.exists():
            missing.append(str(path))
            continue
        if dry_run:
            continue
        path.unlink()
        removed.append(str(path))
    return {
        "schema_version": "canon_shadow_retention_apply_result_v1",
        "generated_at": _utc_now(),
        "dry_run": bool(dry_run),
        "prune_count": len(prune_paths),
        "removed_count": len(removed),
        "missing_count": len(missing),
        "removed_paths": removed,
        "missing_paths": missing,
    }
