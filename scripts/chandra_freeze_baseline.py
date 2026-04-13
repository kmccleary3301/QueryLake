#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Dict, List


def _sha256_bytes(data: bytes) -> str:
    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _read_pages(directory: Path) -> List[Dict[str, object]]:
    pages = []
    for path in sorted(directory.glob('*.md')):
        text = path.read_text(encoding='utf-8', errors='replace')
        pages.append(
            {
                'page': path.name,
                'chars': len(text),
                'sha256': _sha256_file(path),
            }
        )
    if not pages:
        raise ValueError(f'No markdown pages found under: {directory}')
    return pages


def _directory_sha256(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.glob('*.md')):
        digest.update(path.name.encode('utf-8'))
        digest.update(b'\0')
        digest.update(path.read_bytes())
        digest.update(b'\0')
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description='Freeze a Chandra baseline pages directory into a machine-readable artifact.')
    parser.add_argument('--label', required=True, help='Human-readable baseline label.')
    parser.add_argument('--pages-dir', required=True, help='Directory containing per-page markdown files.')
    parser.add_argument('--benchmark-json', default=None, help='Optional benchmark JSON for the baseline run.')
    parser.add_argument('--notes', default=None, help='Optional baseline notes.')
    parser.add_argument('--out-json', required=True, help='Output JSON path.')
    args = parser.parse_args()

    pages_dir = Path(args.pages_dir)
    if not pages_dir.exists() or not pages_dir.is_dir():
        raise FileNotFoundError(f'Pages directory does not exist: {pages_dir}')

    benchmark_payload = None
    benchmark_path = None
    benchmark_sha256 = None
    if args.benchmark_json:
        benchmark_path = Path(args.benchmark_json)
        if not benchmark_path.exists():
            raise FileNotFoundError(f'Benchmark JSON does not exist: {benchmark_path}')
        benchmark_payload = json.loads(benchmark_path.read_text(encoding='utf-8'))
        benchmark_sha256 = _sha256_file(benchmark_path)

    pages = _read_pages(pages_dir)
    total_chars = sum(int(page['chars']) for page in pages)

    payload = {
        'artifact_type': 'chandra_baseline_v1',
        'label': args.label,
        'pages_dir': str(pages_dir),
        'pages_dir_sha256': _directory_sha256(pages_dir),
        'page_count': len(pages),
        'total_chars': total_chars,
        'pages': pages,
        'benchmark_json': str(benchmark_path) if benchmark_path else None,
        'benchmark_json_sha256': benchmark_sha256,
        'benchmark_metadata': {
            'benchmark_schema_version': benchmark_payload.get('benchmark_schema_version') if benchmark_payload else None,
            'runtime_semantics_version': benchmark_payload.get('runtime_semantics_version') if benchmark_payload else None,
            'request_shape_version': benchmark_payload.get('request_shape_version') if benchmark_payload else None,
            'pdf': benchmark_payload.get('pdf') if benchmark_payload else None,
            'runtime': benchmark_payload.get('runtime') if benchmark_payload else None,
        },
        'notes': args.notes,
    }

    out_path = Path(args.out_json)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(payload, indent=2))


if __name__ == '__main__':
    main()
