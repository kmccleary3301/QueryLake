from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, List


PAGE_RE = re.compile(r"^page_(\d{4})\.md$")
SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-+:?\s*(?:\|\s*:?-+:?\s*)+\|?\s*$")
EMPTY_IMAGE_RE = re.compile(r"^\s*!\[[^\]]*\]\(\s*\)\s*$")
ARXIV_RE = re.compile(r"^\s*arXiv:\S+")
SECTIONISH_RE = re.compile(r"^\*{0,2}\s*[A-Z]?\d+(?:\.\d+)*\s*\*{0,2}$")
PAGECELL_RE = re.compile(r"^\*{0,2}\s*\d+\s*\*{0,2}$")


def _strip_empty_images(lines: List[str]) -> List[str]:
    return [line for line in lines if not EMPTY_IMAGE_RE.match(line)]


def _move_arxiv_front(lines: List[str]) -> List[str]:
    arxiv_idx = None
    for i, line in enumerate(lines[:80]):
        if ARXIV_RE.match(line.strip()):
            arxiv_idx = i
            break
    if arxiv_idx is None or arxiv_idx <= 2:
        return lines
    arxiv_line = lines.pop(arxiv_idx)
    insert_at = 0
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1
    return lines[:insert_at] + [arxiv_line, ""] + lines[insert_at:]


def _drop_terminal_page_number(lines: List[str], page_number: int | None) -> List[str]:
    if page_number is None:
        return lines
    end = len(lines) - 1
    while end >= 0 and not lines[end].strip():
        end -= 1
    if end >= 0 and lines[end].strip() == str(page_number):
        del lines[end]
    return lines


def _compact_three_col_outline_tables(lines: List[str]) -> List[str]:
    out: List[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if "|" in line and i + 1 < len(lines) and SEPARATOR_RE.match(lines[i + 1]):
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            rows = [[cell.strip() for cell in row.strip().strip("|").split("|")] for row in table_lines]
            if rows and all(len(row) == 3 for row in rows):
                rewritten: List[str] = []
                can_rewrite = True
                for row_idx, row in enumerate(rows):
                    if row_idx == 1:
                        rewritten.append("| --- | --- |")
                        continue
                    first, second, third = row
                    if row_idx == 0:
                        merged = f"{first} {second}".strip()
                        rewritten.append(f"| {merged} | {third} |")
                        continue
                    if not SECTIONISH_RE.match(first) or not PAGECELL_RE.match(third):
                        can_rewrite = False
                        break
                    merged = f"{first} {second}".strip()
                    rewritten.append(f"| {merged} | {third} |")
                if can_rewrite:
                    out.extend(rewritten)
                    continue
            out.extend(table_lines)
            continue
        out.append(line)
        i += 1
    return out


def _collapse_blank_runs(lines: List[str]) -> List[str]:
    out: List[str] = []
    prev_blank = False
    for line in lines:
        blank = not line.strip()
        if blank and prev_blank:
            continue
        out.append(line.rstrip())
        prev_blank = blank
    while out and not out[-1].strip():
        out.pop()
    return out


def cleanup_text(
    text: str,
    page_number: int | None = None,
    *,
    strip_empty_images: bool = True,
    move_arxiv_front: bool = True,
    drop_terminal_page_number: bool = True,
    compact_outline_tables: bool = True,
) -> str:
    lines = text.splitlines()
    if strip_empty_images:
        lines = _strip_empty_images(lines)
    if move_arxiv_front:
        lines = _move_arxiv_front(lines)
    if drop_terminal_page_number:
        lines = _drop_terminal_page_number(lines, page_number)
    if compact_outline_tables:
        lines = _compact_three_col_outline_tables(lines)
    lines = _collapse_blank_runs(lines)
    return "\n".join(lines).strip() + "\n"


def cleanup_dir(
    src: Path,
    dst: Path,
    *,
    strip_empty_images: bool = True,
    move_arxiv_front: bool = True,
    drop_terminal_page_number: bool = True,
    compact_outline_tables: bool = True,
) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for path in sorted(src.glob("*.md")):
        match = PAGE_RE.match(path.name)
        page_num = int(match.group(1)) if match else None
        (dst / path.name).write_text(
            cleanup_text(
                path.read_text(),
                page_num,
                strip_empty_images=strip_empty_images,
                move_arxiv_front=move_arxiv_front,
                drop_terminal_page_number=drop_terminal_page_number,
                compact_outline_tables=compact_outline_tables,
            )
        )


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Apply structure-aware cleanup to Chandra page outputs.")
    parser.add_argument("src", help="Directory containing per-page markdown files.")
    parser.add_argument("dst", help="Directory where cleaned pages will be written.")
    parser.add_argument("--no-strip-empty-images", action="store_true")
    parser.add_argument("--no-move-arxiv-front", action="store_true")
    parser.add_argument("--no-drop-terminal-page-number", action="store_true")
    parser.add_argument("--no-compact-outline-tables", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)
    cleanup_dir(
        Path(args.src),
        Path(args.dst),
        strip_empty_images=not args.no_strip_empty_images,
        move_arxiv_front=not args.no_move_arxiv_front,
        drop_terminal_page_number=not args.no_drop_terminal_page_number,
        compact_outline_tables=not args.no_compact_outline_tables,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
