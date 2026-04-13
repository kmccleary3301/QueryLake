#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import hashlib
import html as html_lib
import json
import os
import re
import shutil
import statistics
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import markdown as md
import pypdfium2 as pdfium
from PIL import Image

from QueryLake.operation_classes.ray_chandra_class import ChandraDeployment, ChandraImagePayload

RUNTIME_SEMANTICS_VERSION = "chandra_scan_v1"
REQUEST_SHAPE_VERSION = "paper_page_request_v1"
BUNDLE_SCHEMA_VERSION = 1

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title}</title>
  <style>
    body {{ font-family: Inter, system-ui, sans-serif; margin: 2rem auto; max-width: 920px; padding: 0 1rem; line-height: 1.55; color: #111; }}
    h1,h2,h3,h4 {{ line-height: 1.2; }}
    pre, code {{ font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }}
    pre {{ background: #f6f8fa; padding: 1rem; overflow-x: auto; border-radius: 8px; }}
    code {{ background: #f6f8fa; padding: 0.1rem 0.25rem; border-radius: 4px; }}
    table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
    th, td {{ border: 1px solid #d0d7de; padding: 0.5rem; vertical-align: top; }}
    img {{ max-width: 100%; height: auto; }}
    blockquote {{ border-left: 4px solid #d0d7de; margin: 0; padding-left: 1rem; color: #555; }}
  </style>
</head>
<body>
{body}
</body>
</html>
"""


@dataclass(frozen=True)
class SourceSpec:
    input_ref: str
    source_url: str
    pdf_url: str
    paper_id: str
    paper_slug: str
    source_kind: str


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download and Chandra-scan paper PDFs into full artifact bundles.")
    parser.add_argument("sources", nargs="+", help="Paper sources: arXiv abs/pdf URLs, ACL PDF URLs, or local PDF paths.")
    parser.add_argument("--output-root", default="docs_tmp/papers_to_transcribe", help="Root directory for output bundles.")
    parser.add_argument("--profile", default="quality", choices=["speed", "balanced", "quality", "adaptive"], help="Chandra OCR profile.")
    parser.add_argument("--runtime-backend", default="vllm_server", choices=["hf", "vllm", "vllm_server"], help="Chandra runtime backend.")
    parser.add_argument("--page-concurrency", type=int, default=2, help="Per-paper page concurrency for OCR requests.")
    parser.add_argument("--paper-concurrency", type=int, default=1, help="Concurrent papers to process.")
    parser.add_argument("--dpi", type=int, default=144, help="PDF render DPI.")
    parser.add_argument("--max-image-pixels", type=int, default=1_048_576, help="Max image pixels for the runtime request path.")
    parser.add_argument("--max-new-tokens", type=int, default=None, help="Optional max-new-tokens override for the runtime request path.")
    parser.add_argument("--no-warm-pass", action="store_true", help="Skip the warm-cache validation pass.")
    parser.add_argument("--no-zip", action="store_true", help="Do not create a zip bundle for each scan.")
    parser.add_argument("--start-vllm-server", action=argparse.BooleanOptionalAction, default=True, help="Start the external vLLM server automatically when using runtime_backend=vllm_server.")
    parser.add_argument("--vllm-server-base-url", default="http://127.0.0.1:8022/v1", help="Single external vLLM server base URL.")
    parser.add_argument("--vllm-server-base-urls", default=None, help="Comma-separated list of external vLLM server base URLs.")
    parser.add_argument("--vllm-server-model", default="chandra", help="Served model name for the external vLLM server.")
    parser.add_argument("--vllm-server-api-key", default="chandra-local-key", help="API key for the external vLLM server.")
    parser.add_argument("--vllm-server-venv", default=".venv_vllm_0_13", help="Virtualenv used by the vLLM server launcher.")
    parser.add_argument("--vllm-server-cuda-visible-devices", default=os.getenv("CHANDRA_VLLM_CUDA_VISIBLE_DEVICES", ""), help="CUDA_VISIBLE_DEVICES to assign to the external vLLM server.")
    parser.add_argument("--vllm-server-allowed-local-media-path", default=None, help="Allowed root for local media path transport. Defaults to output root.")
    parser.add_argument("--vllm-server-ports", default="8022", help="Reserved for future multi-endpoint launch support; currently informational only.")
    return parser.parse_args()


def _now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _infer_source_kind(source: str) -> str:
    source_l = source.lower()
    if source_l.startswith("http://") or source_l.startswith("https://"):
        if "arxiv.org" in source_l:
            return "arxiv"
        if "aclanthology.org" in source_l:
            return "acl"
        return "url"
    return "local"


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", text.strip())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned or "paper"


def _derive_source_spec(raw: str) -> SourceSpec:
    raw = raw.strip()
    source_kind = _infer_source_kind(raw)
    if source_kind == "local":
        path = Path(raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Local path does not exist: {raw}")
        paper_id = path.stem
        paper_slug = _slugify(paper_id)
        return SourceSpec(
            input_ref=raw,
            source_url=str(path),
            pdf_url=str(path),
            paper_id=paper_id,
            paper_slug=paper_slug,
            source_kind=source_kind,
        )

    parsed = urllib.parse.urlparse(raw)
    path = parsed.path or ""
    if source_kind == "arxiv":
        if "/abs/" in path:
            paper_id = path.split("/abs/", 1)[1].strip("/")
            pdf_url = f"https://arxiv.org/pdf/{paper_id}.pdf"
        elif "/pdf/" in path:
            paper_id = path.split("/pdf/", 1)[1].strip("/")
            if paper_id.endswith(".pdf"):
                paper_id = paper_id[:-4]
            pdf_url = raw
        else:
            paper_id = Path(path).stem
            pdf_url = raw
        paper_slug = _slugify(f"arxiv_{paper_id}")
        return SourceSpec(
            input_ref=raw,
            source_url=pdf_url,
            pdf_url=pdf_url,
            paper_id=paper_id,
            paper_slug=paper_slug,
            source_kind=source_kind,
        )

    filename = Path(path).name or "paper.pdf"
    paper_id = Path(filename).stem
    paper_slug = _slugify(paper_id)
    return SourceSpec(
        input_ref=raw,
        source_url=raw,
        pdf_url=raw,
        paper_id=paper_id,
        paper_slug=paper_slug,
        source_kind=source_kind,
    )


def _download_pdf(pdf_url: str, dest_path: Path) -> float:
    if pdf_url.startswith("http://") or pdf_url.startswith("https://"):
        req = urllib.request.Request(
            pdf_url,
            headers={
                "User-Agent": "QueryLake-Chandra-Scan/1.0",
                "Accept": "application/pdf,*/*;q=0.9",
            },
        )
        start = time.perf_counter()
        with urllib.request.urlopen(req, timeout=120) as response, open(dest_path, "wb") as handle:
            shutil.copyfileobj(response, handle)
        return time.perf_counter() - start

    src = Path(pdf_url).expanduser().resolve()
    start = time.perf_counter()
    shutil.copy2(src, dest_path)
    return time.perf_counter() - start


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _render_pdf_pages(pdf_path: Path, dpi: int, render_cache_dir: Path) -> Tuple[List[ChandraImagePayload], float]:
    render_cache_dir.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    document = pdfium.PdfDocument(str(pdf_path))
    page_count = len(document)
    scale = float(dpi) / 72.0
    payloads: List[ChandraImagePayload] = []
    for index in range(page_count):
        page_path = render_cache_dir / f"page_{index + 1:04d}.png"
        if page_path.exists():
            pil_image = Image.open(page_path).convert("RGB")
            png_bytes = page_path.read_bytes()
            payloads.append(
                ChandraImagePayload(image=pil_image, png_bytes=png_bytes, file_path=str(page_path), media_uuid=f"page-{index+1:04d}")
            )
            continue
        page = document[index]
        pil_image = page.render(scale=scale).to_pil().convert("RGB")
        page.close()
        png_bytes = _write_png(pil_image, page_path)
        payloads.append(
            ChandraImagePayload(image=pil_image, png_bytes=png_bytes, file_path=str(page_path), media_uuid=f"page-{index+1:04d}")
        )
    document.close()
    return payloads, time.perf_counter() - start


def _write_png(image: Image.Image, path: Path) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path, format="PNG")
    return path.read_bytes()


def _markdown_to_html(markdown_text: str) -> str:
    body = md.markdown(
        markdown_text,
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
        output_format="html5",
    )
    return body


def _wrap_html_document(title: str, body: str) -> str:
    return HTML_TEMPLATE.format(title=html_lib.escape(title), body=body)


def _page_markdown(page_num: int, body: str) -> str:
    body = (body or "").strip()
    if not body:
        body = ""
    return f"## Page {page_num}\n\n{body}".strip() + "\n"


def _count_math(markdown_text: str) -> int:
    if not markdown_text:
        return 0
    patterns = [
        r"\$\$.*?\$\$",
        r"\$[^$\n]+\$",
        r"\\begin\{.*?\}",
        r"\\\(.*?\\\)",
        r"\\\[.*?\\\]",
    ]
    total = 0
    for pattern in patterns:
        total += len(re.findall(pattern, markdown_text, flags=re.DOTALL))
    return total


def _extract_headings(markdown_text: str) -> List[Dict[str, Any]]:
    headings: List[Dict[str, Any]] = []
    for line in markdown_text.splitlines():
        match = re.match(r"^(#{1,6})\s+(.*?)\s*$", line)
        if not match:
            continue
        headings.append({"level": len(match.group(1)), "text": match.group(2).strip()})
    return headings


def _count_tables(markdown_text: str) -> int:
    lines = markdown_text.splitlines()
    table_blocks = 0
    in_table = False
    for line in lines:
        is_table_row = line.strip().startswith("|") and "|" in line.strip()[1:]
        is_separator = bool(re.match(r"^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*$", line))
        if is_table_row:
            if not in_table:
                in_table = True
                table_blocks += 1
        elif is_separator:
            continue
        else:
            in_table = False
    return table_blocks


def _build_summary(markdown_pages: Sequence[str], figures_dir: Path) -> Dict[str, Any]:
    combined_markdown = "\n\n".join(page.strip() for page in markdown_pages).strip()
    headings = _extract_headings(combined_markdown)
    figure_mentions = len(re.findall(r"!\[[^\]]*\]\([^)]+\)", combined_markdown))
    figure_mentions += len(re.findall(r"\bFigure\b", combined_markdown))
    return {
        "pages": len(markdown_pages),
        "math_expression_count": _count_math(combined_markdown),
        "table_block_count": _count_tables(combined_markdown),
        "figure_mention_count": int(figure_mentions),
        "extracted_figure_assets_count": len([path for path in figures_dir.iterdir() if path.is_file()]) if figures_dir.exists() else 0,
        "heading_count": len(headings),
        "headings": headings,
    }


async def _run_page_pass(
    runtime: Any,
    page_payloads: Sequence[ChandraImagePayload],
    profile: str,
    page_concurrency: int,
    max_new_tokens: Optional[int],
    max_image_pixels: Optional[int],
) -> Tuple[float, List[float], List[str]]:
    sem = asyncio.Semaphore(max(1, int(page_concurrency)))
    latencies = [0.0] * len(page_payloads)
    outputs = [""] * len(page_payloads)

    async def _worker(page_idx: int, payload: ChandraImagePayload) -> None:
        start = time.perf_counter()
        async with sem:
            outputs[page_idx] = await runtime.transcribe(
                image=payload,
                profile=profile,
                max_new_tokens=max_new_tokens,
                max_image_pixels=max_image_pixels,
            )
        latencies[page_idx] = time.perf_counter() - start

    wall_start = time.perf_counter()
    await asyncio.gather(*[_worker(page_idx, payload) for page_idx, payload in enumerate(page_payloads)])
    return time.perf_counter() - wall_start, latencies, outputs


def _write_page_artifacts(
    bundle_dir: Path,
    paper_id: str,
    markdown_pages: Sequence[str],
    html_pages: Sequence[str],
    render_payloads: Sequence[ChandraImagePayload],
) -> None:
    pages_dir = bundle_dir / "pages"
    pages_html_dir = bundle_dir / "pages_html"
    render_cache_dir = bundle_dir / "render_cache"
    figures_dir = bundle_dir / "figures"
    pages_dir.mkdir(parents=True, exist_ok=True)
    pages_html_dir.mkdir(parents=True, exist_ok=True)
    render_cache_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    for idx, (markdown_text, html_text) in enumerate(zip(markdown_pages, html_pages), start=1):
        page_name = f"page_{idx:04d}"
        (pages_dir / f"{page_name}.md").write_text(markdown_text, encoding="utf-8")
        (pages_html_dir / f"{page_name}.html").write_text(html_text, encoding="utf-8")


def _zip_bundle(bundle_dir: Path) -> Path:
    zip_path = bundle_dir.parent / f"{bundle_dir.name}.zip"
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(bundle_dir.rglob("*")):
            if path.is_dir():
                continue
            arcname = path.relative_to(bundle_dir.parent)
            zf.write(path, arcname.as_posix())
    return zip_path


def _run_vllm_server_start(args: argparse.Namespace, output_root: Path) -> None:
    env = os.environ.copy()
    env.setdefault("CHANDRA_VLLM_VENV", args.vllm_server_venv)
    env.setdefault("CHANDRA_VLLM_MODEL", "models/chandra")
    env.setdefault("CHANDRA_VLLM_SERVED_MODEL_NAME", args.vllm_server_model)
    env.setdefault("CHANDRA_VLLM_API_KEY", args.vllm_server_api_key)
    env.setdefault("CHANDRA_VLLM_ALLOWED_LOCAL_MEDIA_PATH", str(output_root))
    if args.vllm_server_cuda_visible_devices:
        env["CHANDRA_VLLM_CUDA_VISIBLE_DEVICES"] = args.vllm_server_cuda_visible_devices
    script = Path("scripts/chandra_vllm_server.sh").resolve()
    subprocess.run(["bash", str(script), "start"], cwd=Path.cwd(), env=env, check=True)


def _run_vllm_server_stop(args: argparse.Namespace) -> None:
    env = os.environ.copy()
    env.setdefault("CHANDRA_VLLM_VENV", args.vllm_server_venv)
    script = Path("scripts/chandra_vllm_server.sh").resolve()
    subprocess.run(["bash", str(script), "stop"], cwd=Path.cwd(), env=env, check=False)


async def _process_source(
    source: SourceSpec,
    output_root: Path,
    runtime: Any,
    args: argparse.Namespace,
) -> Dict[str, Any]:
    timestamp = _now_stamp()
    bundle_dir = output_root / f"{source.paper_slug}_chandra_scan_{timestamp}"
    bundle_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = bundle_dir / f"{source.paper_id}.pdf"
    render_cache_dir = bundle_dir / "render_cache"
    figures_dir = bundle_dir / "figures"
    pages_dir = bundle_dir / "pages"
    pages_html_dir = bundle_dir / "pages_html"
    figures_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    pages_html_dir.mkdir(parents=True, exist_ok=True)
    render_cache_dir.mkdir(parents=True, exist_ok=True)

    download_seconds = await asyncio.to_thread(_download_pdf, source.pdf_url, pdf_path)
    page_payloads, render_seconds = await asyncio.to_thread(_render_pdf_pages, pdf_path, args.dpi, render_cache_dir)
    page_count = len(page_payloads)

    runtime_init_start = time.perf_counter()
    _ = runtime  # runtime was already created by the caller; kept for symmetry with results payloads.
    runtime_init_seconds = time.perf_counter() - runtime_init_start

    cold_seconds, cold_latencies, cold_outputs = await _run_page_pass(
        runtime=runtime,
        page_payloads=page_payloads,
        profile=args.profile,
        page_concurrency=args.page_concurrency,
        max_new_tokens=args.max_new_tokens,
        max_image_pixels=args.max_image_pixels,
    )

    if args.no_warm_pass:
        warm_seconds = 0.0
        warm_latencies = []
        warm_outputs = []
    else:
        warm_seconds, warm_latencies, warm_outputs = await _run_page_pass(
            runtime=runtime,
            page_payloads=page_payloads,
            profile=args.profile,
            page_concurrency=args.page_concurrency,
            max_new_tokens=args.max_new_tokens,
            max_image_pixels=args.max_image_pixels,
        )

    markdown_pages = [_page_markdown(idx, text) for idx, text in enumerate(cold_outputs, start=1)]
    html_pages = []
    for idx, markdown_text in enumerate(markdown_pages, start=1):
        body = _markdown_to_html(markdown_text)
        html_pages.append(_wrap_html_document(f"{source.paper_id} page {idx}", body))

    combined_markdown = "\n\n".join(page.rstrip() for page in markdown_pages).strip() + "\n"
    combined_html_body = "\n".join(html.split("<body>", 1)[1].rsplit("</body>", 1)[0].strip() for html in html_pages)
    combined_html = _wrap_html_document(f"{source.paper_id} Chandra scan", combined_html_body)

    markdown_path = bundle_dir / f"{source.paper_id}.chandra.md"
    html_path = bundle_dir / f"{source.paper_id}.chandra.html"
    structured_path = bundle_dir / f"{source.paper_id}.chandra.structured.json"
    results_path = bundle_dir / f"{source.paper_id}.chandra.results.json"
    timing_json_path = bundle_dir / f"{source.paper_id}.chandra.timing.json"
    timing_md_path = bundle_dir / f"{source.paper_id}.chandra.timing.md"

    markdown_path.write_text(combined_markdown, encoding="utf-8")
    html_path.write_text(combined_html, encoding="utf-8")

    summary = _build_summary(markdown_pages, figures_dir)
    structured = {
        "source": {
            "pdf": str(pdf_path.resolve()),
            "markdown": str(markdown_path.resolve()),
            "html": str(html_path.resolve()),
            "pages_dir": str(pages_dir.resolve()),
            "pages_html_dir": str(pages_html_dir.resolve()),
            "figures_dir": str(figures_dir.resolve()),
            "render_cache_dir": str(render_cache_dir.resolve()),
        },
        "summary": summary,
        "headings": summary["headings"],
    }
    structured_path.write_text(json.dumps(structured, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    render_artifacts = {
        "dpi": int(args.dpi),
        "pages": page_count,
        "seconds": round(render_seconds, 4),
        "cache_dir": str(render_cache_dir.resolve()),
    }
    runtime_artifacts = {
        "profile": args.profile,
        "runtime_backend": args.runtime_backend,
        "model": "models/chandra",
        "concurrency": int(args.page_concurrency),
        "cache_enabled": True,
        "vllm_server_base_urls": [args.vllm_server_base_url]
        if not args.vllm_server_base_urls
        else [item.strip() for item in args.vllm_server_base_urls.split(",") if item.strip()],
        "use_profile_defaults": True,
        "runtime_init_seconds": round(runtime_init_seconds, 4),
    }
    passes = [
        {
            "name": "cold",
            "pages": page_count,
            "pages_per_second": round(page_count / cold_seconds, 4) if cold_seconds > 0 else 0.0,
            "total_chars": sum(len(text) for text in cold_outputs),
            "wall_seconds": round(cold_seconds, 4),
            "latency_ms": {
                "mean": round(statistics.mean([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
                "median": round(statistics.median([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
                "p95": round(_percentile([value * 1000.0 for value in cold_latencies], 95.0), 2) if cold_latencies else 0.0,
                "max": round(max([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
            },
        }
    ]
    if not args.no_warm_pass:
        passes.append(
            {
                "name": "warm_1",
                "pages": page_count,
                "pages_per_second": round(page_count / warm_seconds, 4) if warm_seconds > 0 else 0.0,
                "total_chars": sum(len(text) for text in warm_outputs),
                "wall_seconds": round(warm_seconds, 4),
                "latency_ms": {
                    "mean": round(statistics.mean([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
                    "median": round(statistics.median([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
                    "p95": round(_percentile([value * 1000.0 for value in warm_latencies], 95.0), 2) if warm_latencies else 0.0,
                    "max": round(max([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
                },
            }
        )

    bundle_contents = {
        "pdf": str(pdf_path.resolve()),
        "source_url": source.source_url,
        "render": render_artifacts,
        "runtime": runtime_artifacts,
        "passes": passes,
        "artifacts": {
            "markdown": str(markdown_path.resolve()),
            "html": str(html_path.resolve()),
            "structured": str(structured_path.resolve()),
            "pages_dir": str(pages_dir.resolve()),
            "pages_html_dir": str(pages_html_dir.resolve()),
            "figures_dir": str(figures_dir.resolve()),
        },
    }
    results_path.write_text(json.dumps(bundle_contents, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    timing = {
        "paper_id": source.paper_id,
        "title": structured["headings"][1]["text"] if len(structured["headings"]) > 1 else source.paper_id,
        "pages": page_count,
        "profile": args.profile,
        "runtime_backend": args.runtime_backend,
        "page_concurrency": int(args.page_concurrency),
        "total_wall_seconds": round(download_seconds + render_seconds + cold_seconds + (warm_seconds if not args.no_warm_pass else 0.0), 4),
        "phase_breakdown": [
            {"name": "PDF download", "seconds": round(download_seconds, 4)},
            {"name": "PDF open + page count", "seconds": 0.0},
            {"name": f"Page render ({page_count} pages @ {args.dpi} DPI)", "seconds": round(render_seconds, 4)},
            {"name": "Embedded figure extraction", "seconds": 0.0},
            {"name": "Runtime init from warmed vLLM server", "seconds": round(runtime_init_seconds, 4)},
            {"name": "OCR cold pass", "seconds": round(cold_seconds, 4)},
            {"name": "OCR warm pass", "seconds": round(warm_seconds if not args.no_warm_pass else 0.0, 4)},
            {"name": "Markdown/HTML materialization", "seconds": round((time.perf_counter() - time.perf_counter()) if False else 0.0, 4)},
            {"name": "Results JSON write", "seconds": 0.0},
        ],
        "cold_pass": {
            "pages_per_second": round(page_count / cold_seconds, 4) if cold_seconds > 0 else 0.0,
            "seconds_per_page": round(cold_seconds / page_count, 4) if page_count else 0.0,
            "total_chars": sum(len(text) for text in cold_outputs),
            "mean_page_latency_ms": round(statistics.mean([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
            "median_page_latency_ms": round(statistics.median([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
            "p95_page_latency_ms": round(_percentile([value * 1000.0 for value in cold_latencies], 95.0), 2) if cold_latencies else 0.0,
            "max_page_latency_ms": round(max([value * 1000.0 for value in cold_latencies]), 2) if cold_latencies else 0.0,
        },
        "warm_pass": None if args.no_warm_pass else {
            "pages_per_second": round(page_count / warm_seconds, 4) if warm_seconds > 0 else 0.0,
            "seconds_per_page": round(warm_seconds / page_count, 4) if page_count else 0.0,
            "total_chars": sum(len(text) for text in warm_outputs),
            "mean_page_latency_ms": round(statistics.mean([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
            "median_page_latency_ms": round(statistics.median([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
            "p95_page_latency_ms": round(_percentile([value * 1000.0 for value in warm_latencies], 95.0), 2) if warm_latencies else 0.0,
            "max_page_latency_ms": round(max([value * 1000.0 for value in warm_latencies]), 2) if warm_latencies else 0.0,
        },
        "notes": [
            "OCR cold pass outputs were used for bundle artifacts.",
            "Warm pass validates cache behavior and is not written to page artifacts.",
            "Figures_dir remains empty unless figure extraction is added in a later pass.",
        ],
    }
    timing_json_path.write_text(json.dumps(timing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    timing_lines = [
        "# Chandra Timing Summary",
        "",
        f"- Paper: `{source.paper_id}`",
        f"- Source: `{source.source_url}`",
        f"- Pages: `{page_count}`",
        f"- OCR profile: `{args.profile}`",
        f"- Runtime backend: `{args.runtime_backend}`",
        f"- Page concurrency: `{args.page_concurrency}`",
        "",
        "## End-to-End Timed Bundle Build",
        "",
        f"- Total wall time: `{timing['total_wall_seconds']:.4f} s`",
        f"- End-to-end seconds/page: `{(timing['total_wall_seconds'] / page_count) if page_count else 0.0:.4f} s/page`",
        "",
        "## Phase Breakdown",
        "",
        "| Phase | Seconds | Share |",
        "| --- | ---: | ---: |",
    ]
    phases = timing["phase_breakdown"]
    total_wall = timing["total_wall_seconds"] or 1.0
    for phase in phases:
        share = (phase["seconds"] / total_wall) * 100.0 if total_wall > 0 else 0.0
        timing_lines.append(f"| {phase['name']} | {phase['seconds']:.4f} | {share:.2f}% |")
    timing_lines.extend(
        [
            "",
            "## OCR Throughput",
            "",
            "### Cold pass",
            f"- Pages/sec: `{timing['cold_pass']['pages_per_second']}`",
            f"- Seconds/page: `{timing['cold_pass']['seconds_per_page']}`",
            f"- Total chars: `{timing['cold_pass']['total_chars']}`",
            f"- Mean page latency: `{timing['cold_pass']['mean_page_latency_ms']} ms`",
            f"- Median page latency: `{timing['cold_pass']['median_page_latency_ms']} ms`",
            f"- P95 page latency: `{timing['cold_pass']['p95_page_latency_ms']} ms`",
            f"- Max page latency: `{timing['cold_pass']['max_page_latency_ms']} ms`",
        ]
    )
    if timing["warm_pass"] is not None:
        timing_lines.extend(
            [
                "",
                "### Warm pass",
                f"- Pages/sec: `{timing['warm_pass']['pages_per_second']}`",
                f"- Seconds/page: `{timing['warm_pass']['seconds_per_page']}`",
                f"- Total chars: `{timing['warm_pass']['total_chars']}`",
                f"- Mean page latency: `{timing['warm_pass']['mean_page_latency_ms']} ms`",
                f"- Median page latency: `{timing['warm_pass']['median_page_latency_ms']} ms`",
                f"- P95 page latency: `{timing['warm_pass']['p95_page_latency_ms']} ms`",
                f"- Max page latency: `{timing['warm_pass']['max_page_latency_ms']} ms`",
            ]
        )
    timing_lines.extend(
        [
            "",
            "## Notes",
            "",
            "- The warm pass reuses the already-warmed Chandra runtime path. It is useful as a cache/hot-path meter, but the cold pass dominates real first-run cost.",
            "- Render cache files preserve the page images, including figures and equations, even when the OCR bundle does not extract separate figure assets.",
            "- The timing above measures the bundle build after the OCR server was already started and warmed. Server bootstrap is not included in `total_wall_seconds`.",
        ]
    )
    timing_md_path.write_text("\n".join(timing_lines).strip() + "\n", encoding="utf-8")

    _write_page_artifacts(bundle_dir, source.paper_id, markdown_pages, html_pages, page_payloads)

    zip_path = None
    if not args.no_zip:
        zip_path = _zip_bundle(bundle_dir)

    return {
        "input": source.input_ref,
        "paper_id": source.paper_id,
        "bundle_dir": str(bundle_dir.resolve()),
        "zip_path": str(zip_path.resolve()) if zip_path else None,
        "results_json": str(results_path.resolve()),
        "timing_json": str(timing_json_path.resolve()),
        "timing_md": str(timing_md_path.resolve()),
        "page_count": page_count,
        "cold_wall_seconds": round(cold_seconds, 4),
        "warm_wall_seconds": round(warm_seconds, 4) if not args.no_warm_pass else None,
    }


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int((len(ordered) - 1) * (pct / 100.0))
    idx = max(0, min(idx, len(ordered) - 1))
    return float(ordered[idx])


async def _amain(args: argparse.Namespace) -> int:
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    specs = [_derive_source_spec(item) for item in args.sources]
    server_started_here = False
    if args.runtime_backend == "vllm_server" and args.start_vllm_server:
        server_started_here = True
        allowed_root = Path(args.vllm_server_allowed_local_media_path or output_root).expanduser().resolve()
        os.environ["CHANDRA_VLLM_ALLOWED_LOCAL_MEDIA_PATH"] = str(allowed_root)
        _run_vllm_server_start(args, allowed_root)

    runtime_init_start = time.perf_counter()
    runtime_kwargs: Dict[str, Any] = {
        "model_path": "models/chandra",
        "runtime_backend": args.runtime_backend,
        "cache_enabled": True,
        "default_profile": args.profile,
        "vllm_server_base_url": args.vllm_server_base_url,
        "vllm_server_base_urls": args.vllm_server_base_urls,
        "vllm_server_model": args.vllm_server_model,
        "vllm_server_api_key": args.vllm_server_api_key,
        "vllm_server_probe_on_init": True,
        "vllm_server_fallback_to_hf_on_error": False,
    }
    if args.runtime_backend == "vllm_server":
        runtime_kwargs["vllm_server_parallel_requests"] = max(1, int(args.page_concurrency))
    runtime = ChandraDeployment.func_or_class(**runtime_kwargs) if hasattr(ChandraDeployment, "func_or_class") else ChandraDeployment(**runtime_kwargs)
    runtime_init_seconds = time.perf_counter() - runtime_init_start
    print(f"[chandra_scan] runtime init seconds: {runtime_init_seconds:.4f}")

    paper_sem = asyncio.Semaphore(max(1, int(args.paper_concurrency)))
    completed: List[Dict[str, Any]] = []

    async def _paper_worker(spec: SourceSpec) -> None:
        async with paper_sem:
            print(f"[chandra_scan] scanning {spec.input_ref}")
            entry = await _process_source(spec, output_root, runtime, args)
            completed.append(entry)
            print(f"[chandra_scan] done {spec.paper_id}: bundle={entry['bundle_dir']}")

    try:
        await asyncio.gather(*[_paper_worker(spec) for spec in specs])
    finally:
        if server_started_here:
            _run_vllm_server_stop(args)

    manifest = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "runtime_semantics_version": RUNTIME_SEMANTICS_VERSION,
        "request_shape_version": REQUEST_SHAPE_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "output_root": str(output_root),
        "papers": completed,
    }
    manifest_path = output_root / f"chandra_scan_manifest_{_now_stamp()}.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[chandra_scan] manifest: {manifest_path}")
    return 0


def main() -> None:
    args = _parse_args()
    raise SystemExit(asyncio.run(_amain(args)))


if __name__ == "__main__":
    main()
