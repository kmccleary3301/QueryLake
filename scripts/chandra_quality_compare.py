#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple


WORD_RE = re.compile(r"[A-Za-z0-9_]+")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
HTML_IMG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
BLANK_LINES_RE = re.compile(r"\n{3,}")
BULLET_RUN_RE = re.compile(r"^([\-*+]\s+){2,}", re.MULTILINE)


@dataclass
class PageMetrics:
    page: str
    baseline_chars: int
    candidate_chars: int
    char_ratio: float
    sequence_ratio: float
    jaccard_words: float
    code_fence_delta: int
    html_table_delta: int
    html_div_delta: int
    markdown_table_row_delta: int

    def as_dict(self) -> Dict[str, float]:
        return {
            "page": self.page,
            "baseline_chars": self.baseline_chars,
            "candidate_chars": self.candidate_chars,
            "char_ratio": round(self.char_ratio, 6),
            "sequence_ratio": round(self.sequence_ratio, 6),
            "jaccard_words": round(self.jaccard_words, 6),
            "code_fence_delta": self.code_fence_delta,
            "html_table_delta": self.html_table_delta,
            "html_div_delta": self.html_div_delta,
            "markdown_table_row_delta": self.markdown_table_row_delta,
        }


@dataclass
class NormalizationStats:
    markdown_images_removed: int
    html_images_removed: int

    def as_dict(self) -> Dict[str, int]:
        return {
            "markdown_images_removed": self.markdown_images_removed,
            "html_images_removed": self.html_images_removed,
        }


@dataclass
class ComparisonSurface:
    name: str
    results: List[PageMetrics]
    aggregate: Dict[str, float]
    recommendation: Dict[str, str]


def _read_pages(directory: Path) -> Dict[str, str]:
    if not directory.exists() or not directory.is_dir():
        raise FileNotFoundError(f"Directory does not exist: {directory}")
    pages: Dict[str, str] = {}
    for path in sorted(directory.glob("*.md")):
        pages[path.name] = path.read_text(encoding="utf-8", errors="replace")
    if not pages:
        raise ValueError(f"No markdown pages found under: {directory}")
    return pages


def _word_jaccard(a: str, b: str) -> float:
    words_a = set(WORD_RE.findall(a.lower()))
    words_b = set(WORD_RE.findall(b.lower()))
    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0
    overlap = len(words_a.intersection(words_b))
    union = len(words_a.union(words_b))
    return overlap / float(union) if union else 1.0


def _sequence_ratio(a: str, b: str) -> float:
    import difflib

    return difflib.SequenceMatcher(a=a, b=b).ratio()


def _count_markdown_table_rows(text: str) -> int:
    lines = text.splitlines()
    count = 0
    for line in lines:
        if "|" in line and len(line.strip()) >= 3:
            count += 1
    return count


def _page_metrics(page: str, baseline: str, candidate: str) -> PageMetrics:
    baseline_chars = len(baseline)
    candidate_chars = len(candidate)
    char_ratio = (candidate_chars / baseline_chars) if baseline_chars else 1.0
    return PageMetrics(
        page=page,
        baseline_chars=baseline_chars,
        candidate_chars=candidate_chars,
        char_ratio=char_ratio,
        sequence_ratio=_sequence_ratio(baseline, candidate),
        jaccard_words=_word_jaccard(baseline, candidate),
        code_fence_delta=abs(baseline.count("```") - candidate.count("```")),
        html_table_delta=abs(
            (baseline.count("<table") - baseline.count("</table>"))
            - (candidate.count("<table") - candidate.count("</table>"))
        ),
        html_div_delta=abs(
            (baseline.count("<div") - baseline.count("</div>"))
            - (candidate.count("<div") - candidate.count("</div>"))
        ),
        markdown_table_row_delta=abs(
            _count_markdown_table_rows(baseline) - _count_markdown_table_rows(candidate)
        ),
    )


def _percentile(values: List[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = max(0, min(len(ordered) - 1, int(math.floor((len(ordered) - 1) * pct / 100.0))))
    return ordered[rank]


def _aggregate(results: List[PageMetrics]) -> Dict[str, float]:
    sequence = [m.sequence_ratio for m in results]
    jaccard = [m.jaccard_words for m in results]
    char_ratio = [m.char_ratio for m in results]
    structure_penalty = [
        (m.code_fence_delta + m.html_table_delta + m.html_div_delta + m.markdown_table_row_delta)
        for m in results
    ]
    return {
        "pages": len(results),
        "sequence_ratio_mean": round(statistics.mean(sequence), 6) if sequence else 0.0,
        "sequence_ratio_p10": round(_percentile(sequence, 10.0), 6),
        "jaccard_words_mean": round(statistics.mean(jaccard), 6) if jaccard else 0.0,
        "jaccard_words_p10": round(_percentile(jaccard, 10.0), 6),
        "char_ratio_mean": round(statistics.mean(char_ratio), 6) if char_ratio else 1.0,
        "char_ratio_p10": round(_percentile(char_ratio, 10.0), 6),
        "char_ratio_p90": round(_percentile(char_ratio, 90.0), 6),
        "structure_penalty_mean": round(statistics.mean(structure_penalty), 6) if structure_penalty else 0.0,
        "structure_penalty_max": max(structure_penalty) if structure_penalty else 0,
    }


def _failure_fingerprint(results: List[PageMetrics]) -> Dict[str, object]:
    under_generated_pages = [m.page for m in results if m.char_ratio < 0.8]
    over_generated_pages = [m.page for m in results if m.char_ratio > 1.2]
    low_sequence_pages = [m.page for m in results if m.sequence_ratio < 0.75]
    table_expansion_pages = [m.page for m in results if m.markdown_table_row_delta >= 3]
    structural_pages = [
        m.page
        for m in results
        if (m.code_fence_delta + m.html_table_delta + m.html_div_delta + m.markdown_table_row_delta) >= 4
    ]
    return {
        "under_generated_pages": under_generated_pages,
        "over_generated_pages": over_generated_pages,
        "low_sequence_pages": low_sequence_pages,
        "table_expansion_pages": table_expansion_pages,
        "high_structural_drift_pages": structural_pages,
        "counts": {
            "under_generated_pages": len(under_generated_pages),
            "over_generated_pages": len(over_generated_pages),
            "low_sequence_pages": len(low_sequence_pages),
            "table_expansion_pages": len(table_expansion_pages),
            "high_structural_drift_pages": len(structural_pages),
        },
    }


def _recommendation(agg: Dict[str, float]) -> Dict[str, str]:
    seq = agg["sequence_ratio_mean"]
    jac = agg["jaccard_words_mean"]
    char_mean = agg["char_ratio_mean"]
    p10 = agg["char_ratio_p10"]
    p90 = agg["char_ratio_p90"]
    structure_mean = agg["structure_penalty_mean"]
    structure = agg["structure_penalty_max"]
    if (
        seq >= 0.84
        and jac >= 0.78
        and char_mean <= 1.12
        and p10 >= 0.65
        and p90 <= 1.45
        and structure_mean <= 2.5
        and structure <= 12
    ):
        verdict = "pass"
        note = "Candidate is close enough to baseline for default traffic with manual spot-check."
    elif (
        seq >= 0.75
        and jac >= 0.68
        and char_mean <= 1.35
        and p10 >= 0.55
        and structure_mean <= 6.0
        and structure <= 24
    ):
        verdict = "warn"
        note = "Candidate is likely usable for latency-priority mode but not as default."
    else:
        verdict = "fail"
        note = "Candidate diverges too much from baseline; keep behind opt-in only."
    return {"verdict": verdict, "note": note}


def _normalize_text(text: str) -> Tuple[str, NormalizationStats]:
    markdown_images_removed = len(MARKDOWN_IMAGE_RE.findall(text))
    html_images_removed = len(HTML_IMG_RE.findall(text))
    normalized = MARKDOWN_IMAGE_RE.sub("[IMAGE]", text)
    normalized = HTML_IMG_RE.sub("[IMAGE]", normalized)
    normalized = BULLET_RUN_RE.sub("- ", normalized)
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")
    normalized = BLANK_LINES_RE.sub("\n\n", normalized)
    normalized = "\n".join(line.rstrip() for line in normalized.splitlines()).strip()
    return normalized, NormalizationStats(
        markdown_images_removed=markdown_images_removed,
        html_images_removed=html_images_removed,
    )


def _build_surface(name: str, baseline_pages: Dict[str, str], candidate_pages: Dict[str, str], shared_pages: List[str]) -> ComparisonSurface:
    rows: List[PageMetrics] = []
    for page in shared_pages:
        rows.append(_page_metrics(page, baseline_pages[page], candidate_pages[page]))
    aggregate = _aggregate(rows)
    recommendation = _recommendation(aggregate)
    return ComparisonSurface(name=name, results=rows, aggregate=aggregate, recommendation=recommendation)


def _directory_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.glob("*.md")):
        digest.update(path.name.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare Chandra per-page markdown outputs.")
    parser.add_argument("--baseline-dir", required=True, help="Directory of baseline per-page markdown files.")
    parser.add_argument("--candidate-dir", required=True, help="Directory of candidate per-page markdown files.")
    parser.add_argument("--out-json", default=None, help="Optional JSON output path.")
    parser.add_argument(
        "--emit-normalized-pages",
        action="store_true",
        help="Include normalized per-page metrics in the JSON output.",
    )
    args = parser.parse_args()

    baseline_dir = Path(args.baseline_dir)
    candidate_dir = Path(args.candidate_dir)
    baseline_pages = _read_pages(baseline_dir)
    candidate_pages = _read_pages(candidate_dir)

    shared_pages = sorted(set(baseline_pages).intersection(candidate_pages))
    if not shared_pages:
        raise ValueError("No overlapping page filenames between baseline and candidate directories.")

    missing_from_candidate = sorted(set(baseline_pages).difference(candidate_pages))
    missing_from_baseline = sorted(set(candidate_pages).difference(baseline_pages))

    raw_surface = _build_surface("raw", baseline_pages, candidate_pages, shared_pages)

    normalized_baseline_pages: Dict[str, str] = {}
    normalized_candidate_pages: Dict[str, str] = {}
    normalization_stats: Dict[str, Dict[str, Dict[str, int]]] = {}
    for page in shared_pages:
        normalized_baseline, baseline_stats = _normalize_text(baseline_pages[page])
        normalized_candidate, candidate_stats = _normalize_text(candidate_pages[page])
        normalized_baseline_pages[page] = normalized_baseline
        normalized_candidate_pages[page] = normalized_candidate
        normalization_stats[page] = {
            "baseline": baseline_stats.as_dict(),
            "candidate": candidate_stats.as_dict(),
        }

    normalized_surface = _build_surface(
        "normalized",
        normalized_baseline_pages,
        normalized_candidate_pages,
        shared_pages,
    )

    report = {
        "baseline_dir": str(baseline_dir),
        "candidate_dir": str(candidate_dir),
        "shared_pages": len(shared_pages),
        "missing_from_candidate": missing_from_candidate,
        "missing_from_baseline": missing_from_baseline,
        "baseline_dir_sha256": _directory_sha256(baseline_dir),
        "candidate_dir_sha256": _directory_sha256(candidate_dir),
        "aggregate": raw_surface.aggregate,
        "recommendation": raw_surface.recommendation,
        "failure_fingerprint": _failure_fingerprint(raw_surface.results),
        "pages": [row.as_dict() for row in raw_surface.results],
        "normalized_aggregate": normalized_surface.aggregate,
        "normalized_recommendation": normalized_surface.recommendation,
        "normalized_failure_fingerprint": _failure_fingerprint(normalized_surface.results),
        "normalization": {
            "strategy": {
                "markdown_images": "replace with [IMAGE] placeholder",
                "html_images": "replace with [IMAGE] placeholder",
                "bullet_runs": "collapse repeated list markers to '- '",
                "blank_lines": "collapse 3+ blank lines to 2",
                "line_endings": "normalize to LF and trim trailing spaces",
            },
            "per_page_stats": normalization_stats,
        },
    }
    if args.emit_normalized_pages:
        report["normalized_pages"] = [row.as_dict() for row in normalized_surface.results]

    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
