#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json

from QueryLake.scanning.eval_diff import diff_eval_results, eval_diff_to_markdown, load_eval_results


def main() -> int:
    parser = argparse.ArgumentParser(description="Diff scanner eval result files and fail on regressions.")
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--format", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--fail-on-regression", action="store_true")
    args = parser.parse_args()

    diff = diff_eval_results(load_eval_results(args.baseline), load_eval_results(args.candidate))
    if args.format == "json":
        print(json.dumps(diff.to_payload(), indent=2, sort_keys=True))
    else:
        print(eval_diff_to_markdown(diff))
    if args.fail_on_regression and not diff.passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
