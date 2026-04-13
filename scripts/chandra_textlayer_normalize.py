#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List


PAGE_RE = re.compile(r"^page_(\d{4})\.md$")
URL_RE = re.compile(r"^https?://\S+$", re.IGNORECASE)
DOI_LINE_RE = re.compile(r"^(?:https?://doi\.org/\S+|doi:\S+)$", re.IGNORECASE)
ARXIV_RE = re.compile(r"^arXiv:\S+", re.IGNORECASE)
DATE_RE = re.compile(r"^\d{4}-\d{1,2}-\d{1,2}$")
TITLEISH_RE = re.compile(r"^[A-Z0-9][A-Za-z0-9,:;()\-–—/ ]{12,}$")
AUTHORISH_RE = re.compile(r".*(?:@|Corresponding authors|©\d{4}|Received:|Accepted:|Published online:).*")
CONTENTS_ROW_RE = re.compile(r"^((?:\d+(?:\.\d+)*(?:\s+[A-Za-z][A-Za-z0-9\-:,&' ]*)?|[A-Z][A-Za-z][A-Za-z0-9\-:,&' ]+))\s+(\d+)$")
BLANK_RUN_RE = re.compile(r"\n{3,}")
SOFT_HYPHEN_BREAK_RE = re.compile(r"(\w)-\n([a-z])")
MULTISPACE_RE = re.compile(r"[ \t\u2009\u200a\u202f]+")


def _normalize_chars(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    text = text.replace("\u2009", " ").replace("\u200a", " ").replace("\u202f", " ")
    text = text.replace(" ", " ").replace("–", "-").replace("—", "-")
    text = SOFT_HYPHEN_BREAK_RE.sub(r"\1\2", text)
    text = MULTISPACE_RE.sub(" ", text)
    return text


def _strip_source_banner(lines: List[str]) -> List[str]:
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if i < 8:
            if not line:
                i += 1
                continue
            if URL_RE.match(line) and "doi.org" not in line.lower():
                i += 1
                continue
            if DATE_RE.match(line):
                i += 1
                continue
            if line.lower() in {"nature methods", "nature"}:
                i += 1
                continue
        out.append(lines[i])
        i += 1
    return out


def _title_block_to_heading(lines: List[str]) -> List[str]:
    if not lines:
        return lines
    prefix: List[str] = []
    rest = lines[:]

    while rest and not rest[0].strip():
        prefix.append(rest.pop(0))

    title_lines: List[str] = []
    while rest and len(title_lines) < 3:
        candidate = rest[0].strip()
        if not candidate:
            break
        if AUTHORISH_RE.match(candidate) or candidate.lower() in {"abstract", "contents", "technical report", "brief communication"}:
            break
        if not TITLEISH_RE.match(candidate):
            break
        title_lines.append(candidate)
        rest.pop(0)

    if not title_lines:
        return lines

    title = " ".join(title_lines).strip()
    if len(title) < 16:
        return lines

    heading = [title, "=" * len(title), ""]
    return prefix + heading + rest


def _format_known_labels(lines: List[str]) -> List[str]:
    out: List[str] = []
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if line.lower() == "technical report":
            out.extend(["Technical Report", "----------------", ""])
            continue
        if line.lower() == "abstract":
            out.extend(["### Abstract", ""])
            continue
        if line.lower() == "contents":
            out.extend(["Contents", "--------", ""])
            continue
        if DOI_LINE_RE.match(line):
            out.append(f"<{line}>")
            continue
        if line.lower() == "brief communication":
            out.extend(["**Brief Communication**", ""])
            continue
        out.append(raw)
    return out


def _looks_like_toc_block(lines: List[str]) -> bool:
    matches = 0
    for line in lines[:20]:
        if CONTENTS_ROW_RE.match(line.strip()):
            matches += 1
    return matches >= 4


def _convert_toc_block(lines: List[str]) -> List[str]:
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if CONTENTS_ROW_RE.match(line):
            block: List[tuple[str, str]] = []
            while i < len(lines):
                candidate = lines[i].strip()
                match = CONTENTS_ROW_RE.match(candidate)
                if not match:
                    break
                block.append((match.group(1).strip(), match.group(2).strip()))
                i += 1
            if len(block) >= 4:
                out.append("| Section | Page |")
                out.append("| --- | --- |")
                for title, page in block:
                    out.append(f"| {title} | {page} |")
                out.append("")
                continue
            for title, page in block:
                out.append(f"{title} {page}")
            continue
        out.append(lines[i])
        i += 1
    return out


def _unwrap_paragraphs(lines: List[str]) -> List[str]:
    out: List[str] = []
    buffer: List[str] = []

    def flush() -> None:
        nonlocal buffer
        if buffer:
            out.append(" ".join(part.strip() for part in buffer if part.strip()).strip())
            buffer = []

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            flush()
            out.append("")
            continue
        if (
            stripped.startswith("#")
            or stripped.startswith("|")
            or stripped.startswith("<")
            or stripped.startswith("**")
            or re.match(r"^[-=]{3,}$", stripped)
            or stripped.startswith("- ")
            or stripped.startswith("* ")
            or URL_RE.match(stripped)
            or ARXIV_RE.match(stripped)
            or re.match(r"^\d+(?:\.\d+)*\s", stripped)
        ):
            flush()
            out.append(stripped)
            continue
        buffer.append(stripped)

    flush()
    return out


def normalize_textlayer_page(text: str) -> str:
    text = _normalize_chars(text)
    lines = text.splitlines()
    lines = _strip_source_banner(lines)
    lines = _format_known_labels(lines)
    lines = _title_block_to_heading(lines)
    if _looks_like_toc_block(lines):
        lines = _convert_toc_block(lines)
    lines = _unwrap_paragraphs(lines)
    rendered = "\n".join(line.rstrip() for line in lines)
    rendered = BLANK_RUN_RE.sub("\n\n", rendered).strip()
    return rendered + "\n"


def normalize_dir(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*.md")):
        (dst / path.name).write_text(normalize_textlayer_page(path.read_text(encoding="utf-8", errors="replace")), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize text-layer markdown toward OCR-style structure.")
    parser.add_argument("src")
    parser.add_argument("dst")
    args = parser.parse_args(list(argv) if argv is not None else None)
    normalize_dir(Path(args.src), Path(args.dst))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
