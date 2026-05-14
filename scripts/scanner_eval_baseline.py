#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from QueryLake.scanning.eval_runner import run_mock_eval
from QueryLake.scanning.evaluation import eval_results_to_markdown, load_eval_manifest, summarize_eval_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate CI-safe scanner eval baseline results from mock/injected fixture envelopes.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--json-out", default="")
    parser.add_argument("--markdown-out", default="")
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    args = parser.parse_args()

    cases = load_eval_manifest(args.manifest)
    results = run_mock_eval(cases)
    payload = {
        "schema_version": "scanner_eval_results_v1",
        "mode": "mock_baseline",
        "manifest": args.manifest,
        "summary": summarize_eval_results(results),
        "results": [result.to_payload() for result in results],
    }
    markdown = eval_results_to_markdown(results)

    if args.json_out:
        Path(args.json_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json_out).write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    if args.markdown_out:
        Path(args.markdown_out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.markdown_out).write_text(markdown + "\n", encoding="utf-8")

    if args.format == "json":
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
