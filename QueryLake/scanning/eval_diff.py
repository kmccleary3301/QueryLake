from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from QueryLake.scanning.evaluation import ScannerEvalResult, summarize_eval_results


@dataclass(frozen=True)
class ScannerEvalDiff:
    passed: bool
    regressions: List[str] = field(default_factory=list)
    baseline_summary: Dict[str, Any] = field(default_factory=dict)
    candidate_summary: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def load_eval_results(path: str | Path) -> List[ScannerEvalResult]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw = payload.get("results", payload if isinstance(payload, list) else [])
    if not isinstance(raw, list):
        raise ValueError("eval results file must be a result list or object with 'results'")
    return [ScannerEvalResult(**item) for item in raw]


def diff_eval_results(baseline: List[ScannerEvalResult], candidate: List[ScannerEvalResult]) -> ScannerEvalDiff:
    baseline_by_case = {result.case_id: result for result in baseline}
    candidate_by_case = {result.case_id: result for result in candidate}
    regressions: List[str] = []
    for case_id, base in baseline_by_case.items():
        cand = candidate_by_case.get(case_id)
        if cand is None:
            regressions.append(f"missing_candidate_case:{case_id}")
            continue
        if base.passed and not cand.passed:
            regressions.append(f"case_regressed:{case_id}")
        for check, base_passed in base.checks.items():
            if base_passed and cand.checks.get(check) is False:
                regressions.append(f"check_regressed:{case_id}:{check}")
    for case_id in sorted(set(candidate_by_case) - set(baseline_by_case)):
        if not candidate_by_case[case_id].passed:
            regressions.append(f"new_failing_case:{case_id}")
    return ScannerEvalDiff(
        passed=not regressions,
        regressions=regressions,
        baseline_summary=summarize_eval_results(baseline),
        candidate_summary=summarize_eval_results(candidate),
    )


def eval_diff_to_markdown(diff: ScannerEvalDiff) -> str:
    lines = [
        "# Scanner Eval Diff",
        "",
        f"- Passed: `{str(diff.passed).lower()}`",
        f"- Regression count: `{len(diff.regressions)}`",
        f"- Baseline pass rate: `{diff.baseline_summary.get('pass_rate', 0.0)}`",
        f"- Candidate pass rate: `{diff.candidate_summary.get('pass_rate', 0.0)}`",
        "",
        "| regression |",
        "| --- |",
    ]
    if diff.regressions:
        lines.extend(f"| {item} |" for item in diff.regressions)
    else:
        lines.append("| none |")
    return "\n".join(lines)
