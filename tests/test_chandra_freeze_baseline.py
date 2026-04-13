import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_chandra_freeze_baseline_captures_page_hashes_and_benchmark_metadata(tmp_path: Path):
    pages_dir = tmp_path / 'pages'
    pages_dir.mkdir()
    (pages_dir / 'page_0001.md').write_text('alpha', encoding='utf-8')
    (pages_dir / 'page_0002.md').write_text('beta', encoding='utf-8')

    benchmark_json = tmp_path / 'benchmark.json'
    benchmark_json.write_text(
        json.dumps(
            {
                'benchmark_schema_version': 1,
                'runtime_semantics_version': 'chandra_runtime_v1',
                'request_shape_version': 'page_request_v1',
                'pdf': 'sample.pdf',
                'runtime': {'runtime_backend': 'vllm', 'profile': 'speed'},
            },
            indent=2,
        ),
        encoding='utf-8',
    )

    out_json = tmp_path / 'baseline.json'
    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'chandra_freeze_baseline.py'),
            '--label',
            'current-chandra1-10p',
            '--pages-dir',
            str(pages_dir),
            '--benchmark-json',
            str(benchmark_json),
            '--notes',
            'canonical test baseline',
            '--out-json',
            str(out_json),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(out_json.read_text(encoding='utf-8'))
    assert payload['artifact_type'] == 'chandra_baseline_v1'
    assert payload['label'] == 'current-chandra1-10p'
    assert payload['page_count'] == 2
    assert payload['benchmark_metadata']['benchmark_schema_version'] == 1
    assert payload['benchmark_metadata']['runtime']['profile'] == 'speed'
    assert len(payload['pages']) == 2
    assert payload['pages'][0]['page'] == 'page_0001.md'
    assert payload['pages_dir_sha256']
    assert payload['benchmark_json_sha256']
