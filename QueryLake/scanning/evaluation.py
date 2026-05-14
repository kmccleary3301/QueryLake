from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from QueryLake.scanning.contracts import ScannerEnvelope, validate_scanner_envelope


@dataclass(frozen=True)
class ScannerEvalCase:
    case_id: str
    document_class: str
    capture_mode: str
    source_ref: str
    mime_type: str = "application/pdf"
    expected_acquisition_modes: List[str] = field(default_factory=list)
    required_projection_kinds: List[str] = field(default_factory=lambda: ["canonical_text"])
    required_artifact_types: List[str] = field(default_factory=list)
    notes: str = ""

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScannerEvalResult:
    case_id: str
    backend_id: str
    passed: bool
    checks: Dict[str, bool]
    metrics: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def load_eval_manifest(path: str | Path) -> List[ScannerEvalCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise ValueError("scanner eval manifest must contain a 'cases' list")
    cases = [ScannerEvalCase(**case) for case in raw_cases]
    validate_eval_cases(cases)
    return cases


def validate_eval_cases(cases: Iterable[ScannerEvalCase]) -> None:
    seen: set[str] = set()
    for case in cases:
        if not case.case_id:
            raise ValueError("eval case_id must be non-empty")
        if case.case_id in seen:
            raise ValueError(f"duplicate eval case_id: {case.case_id}")
        seen.add(case.case_id)
        if not case.document_class:
            raise ValueError(f"{case.case_id}: document_class is required")
        if not case.capture_mode:
            raise ValueError(f"{case.case_id}: capture_mode is required")
        if not case.source_ref:
            raise ValueError(f"{case.case_id}: source_ref is required")


def evaluate_scanner_envelope_contract(
    envelope: ScannerEnvelope,
    case: ScannerEvalCase,
) -> ScannerEvalResult:
    errors: List[str] = []
    try:
        validate_scanner_envelope(envelope)
        envelope_valid = True
    except Exception as exc:
        envelope_valid = False
        errors.append(str(exc))

    projection_kinds = {projection.projection_kind for projection in envelope.projections}
    artifact_types = {artifact.artifact_type for artifact in envelope.artifacts}
    acquisition_modes = {page.acquisition_mode for page in envelope.pages}
    if envelope.contract.acquisition_mode:
        acquisition_modes.add(envelope.contract.acquisition_mode)

    checks = {
        "envelope_valid": envelope_valid,
        "canonical_text_present": bool(envelope.canonical_text().strip()),
        "required_projection_kinds_present": set(case.required_projection_kinds).issubset(projection_kinds),
        "required_artifact_types_present": set(case.required_artifact_types).issubset(artifact_types),
        "expected_acquisition_mode_present": (
            not case.expected_acquisition_modes
            or bool(set(case.expected_acquisition_modes).intersection(acquisition_modes))
        ),
        "page_count_nonzero": len(envelope.pages) > 0,
    }
    return ScannerEvalResult(
        case_id=case.case_id,
        backend_id=envelope.scan_run.backend_id,
        passed=all(checks.values()),
        checks=checks,
        metrics={
            "document_class": case.document_class,
            "capture_mode": case.capture_mode,
            "page_count": len(envelope.pages),
            "projection_kinds": sorted(projection_kinds),
            "artifact_types": sorted(artifact_types),
            "acquisition_modes": sorted(acquisition_modes),
        },
        errors=errors,
    )


def summarize_eval_results(results: Iterable[ScannerEvalResult]) -> Dict[str, Any]:
    rows = list(results)
    passed = sum(1 for result in rows if result.passed)
    by_backend: Dict[str, Dict[str, int]] = {}
    for result in rows:
        bucket = by_backend.setdefault(result.backend_id, {"passed": 0, "failed": 0, "total": 0})
        bucket["total"] += 1
        if result.passed:
            bucket["passed"] += 1
        else:
            bucket["failed"] += 1
    return {
        "total": len(rows),
        "passed": passed,
        "failed": len(rows) - passed,
        "pass_rate": round(float(passed) / float(len(rows)), 4) if rows else 0.0,
        "by_backend": by_backend,
    }


def eval_results_to_markdown(results: Iterable[ScannerEvalResult]) -> str:
    rows = list(results)
    summary = summarize_eval_results(rows)
    lines = [
        "# Scanner Eval Report",
        "",
        f"- Total: `{summary['total']}`",
        f"- Passed: `{summary['passed']}`",
        f"- Failed: `{summary['failed']}`",
        f"- Pass rate: `{summary['pass_rate']}`",
        "",
        "| case_id | backend_id | passed | failed_checks |",
        "| --- | --- | --- | --- |",
    ]
    for result in rows:
        failed_checks = [
            name for name, passed in result.checks.items() if not passed
        ]
        lines.append(
            f"| {result.case_id} | {result.backend_id} | {str(result.passed).lower()} | {', '.join(failed_checks) or ''} |"
        )
    return "\n".join(lines)

@dataclass(frozen=True)
class ScannerPromotionThresholds:
    min_contract_pass_rate: float = 1.0
    min_cases: int = 1
    max_failure_count: int = 0

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ScannerPromotionDecision:
    backend_id: str
    promotable: bool
    reason: str
    summary: Dict[str, Any]
    thresholds: ScannerPromotionThresholds

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


def decide_backend_promotion(
    backend_id: str,
    results: Iterable[ScannerEvalResult],
    thresholds: Optional[ScannerPromotionThresholds] = None,
) -> ScannerPromotionDecision:
    thresholds = thresholds or ScannerPromotionThresholds()
    backend_results = [result for result in results if result.backend_id == backend_id]
    summary = summarize_eval_results(backend_results)
    if summary["total"] < thresholds.min_cases:
        return ScannerPromotionDecision(
            backend_id=backend_id,
            promotable=False,
            reason="insufficient_cases",
            summary=summary,
            thresholds=thresholds,
        )
    if summary["failed"] > thresholds.max_failure_count:
        return ScannerPromotionDecision(
            backend_id=backend_id,
            promotable=False,
            reason="failure_count_exceeded",
            summary=summary,
            thresholds=thresholds,
        )
    if summary["pass_rate"] < thresholds.min_contract_pass_rate:
        return ScannerPromotionDecision(
            backend_id=backend_id,
            promotable=False,
            reason="contract_pass_rate_below_threshold",
            summary=summary,
            thresholds=thresholds,
        )
    return ScannerPromotionDecision(
        backend_id=backend_id,
        promotable=True,
        reason="thresholds_met",
        summary=summary,
        thresholds=thresholds,
    )


def promotion_decisions_to_markdown(decisions: Iterable[ScannerPromotionDecision]) -> str:
    rows = list(decisions)
    lines = [
        "# Scanner Promotion Report",
        "",
        "| backend_id | promotable | reason | total | pass_rate |",
        "| --- | --- | --- | ---: | ---: |",
    ]
    for decision in rows:
        lines.append(
            f"| {decision.backend_id} | {str(decision.promotable).lower()} | {decision.reason} | {decision.summary.get('total', 0)} | {decision.summary.get('pass_rate', 0.0)} |"
        )
    return "\n".join(lines)
