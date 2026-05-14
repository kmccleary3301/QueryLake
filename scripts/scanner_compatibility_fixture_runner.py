#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope, validate_scanner_envelope
from QueryLake.scanning.persistence import summarize_scanner_envelope_payload


def _load_manifest(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "scanner_legacy_compat_manifest_v1":
        raise ValueError(f"Unsupported fixture manifest schema: {payload.get('schema_version')}")
    if not isinstance(payload.get("cases"), list) or not payload["cases"]:
        raise ValueError("Fixture manifest must contain a non-empty cases list")
    return payload


def _run_case(case: Dict[str, Any]) -> Dict[str, Any]:
    envelope = materialize_legacy_markdown_envelope(
        run_id=case["run_id"],
        backend_id=case["backend_id"],
        backend_class=case["backend_class"],
        support_tier=case["support_tier"],
        legacy_output_contract=case["legacy_output_contract"],
        markdown=case["markdown"],
        meta=case.get("meta") or {},
        file_id=case.get("file_id"),
        file_version_id=case.get("file_version_id"),
        document_version_id=case.get("document_version_id"),
    )
    validate_scanner_envelope(envelope)
    payload = envelope.to_payload()
    expected = case.get("expected") or {}
    page_modes = [page["acquisition_mode"] for page in payload["pages"]]
    failures: List[str] = []
    if expected.get("acquisition_mode") and payload["contract"]["acquisition_mode"] != expected["acquisition_mode"]:
        failures.append("acquisition_mode")
    if expected.get("raw_backend_contract") and payload["contract"]["raw_backend_contract"] != expected["raw_backend_contract"]:
        failures.append("raw_backend_contract")
    if expected.get("page_modes") and page_modes != expected["page_modes"]:
        failures.append("page_modes")

    return {
        "case_id": case["case_id"],
        "passed": not failures,
        "failures": failures,
        "summary": summarize_scanner_envelope_payload(payload),
        "page_modes": page_modes,
    }


def run_manifest(path: Path) -> Dict[str, Any]:
    manifest = _load_manifest(path)
    results = [_run_case(case) for case in manifest["cases"]]
    return {
        "schema_version": "scanner_legacy_compat_summary_v1",
        "manifest": str(path),
        "case_count": len(results),
        "passed_count": sum(1 for result in results if result["passed"]),
        "failed_count": sum(1 for result in results if not result["passed"]),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scanner legacy compatibility fixtures.")
    parser.add_argument("manifest", type=Path, help="Path to scanner_legacy_compat_manifest_v1 JSON")
    parser.add_argument("--output", type=Path, help="Optional JSON summary output path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args()

    summary = run_manifest(args.manifest)
    indent = 2 if args.pretty else None
    text = json.dumps(summary, indent=indent, sort_keys=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if summary["failed_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
