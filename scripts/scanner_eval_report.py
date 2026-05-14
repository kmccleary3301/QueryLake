#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.scanning.evaluation import (
    eval_results_to_markdown,
    load_eval_manifest,
    summarize_eval_results,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect scanner eval fixture manifests.")
    parser.add_argument("--manifest", required=True, help="Path to scanner eval manifest JSON.")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    cases = load_eval_manifest(Path(args.manifest))
    payload = {
        "manifest": str(Path(args.manifest)),
        "case_count": len(cases),
        "cases": [case.to_payload() for case in cases],
        "summary": {
            "document_classes": sorted({case.document_class for case in cases}),
            "capture_modes": sorted({case.capture_mode for case in cases}),
            "mime_types": sorted({case.mime_type for case in cases}),
        },
    }

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    lines = [
        "# Scanner Eval Manifest",
        "",
        f"- Manifest: `{payload['manifest']}`",
        f"- Case count: `{payload['case_count']}`",
        f"- Document classes: `{', '.join(payload['summary']['document_classes'])}`",
        f"- Capture modes: `{', '.join(payload['summary']['capture_modes'])}`",
        "",
        "| case_id | document_class | capture_mode | expected_acquisition_modes |",
        "| --- | --- | --- | --- |",
    ]
    for case in cases:
        lines.append(
            f"| {case.case_id} | {case.document_class} | {case.capture_mode} | {', '.join(case.expected_acquisition_modes)} |"
        )
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
