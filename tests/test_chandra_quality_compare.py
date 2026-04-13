import json
import subprocess
import sys
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent

_MODULE_PATH = ROOT / 'scripts' / 'chandra_quality_compare.py'
_SPEC = importlib.util.spec_from_file_location('chandra_quality_compare', _MODULE_PATH)
assert _SPEC and _SPEC.loader
_MODULE = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)


def _write_page(directory: Path, name: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_text(text, encoding='utf-8')


def test_quality_compare_emits_raw_and_normalized_surfaces(tmp_path: Path):
    baseline = tmp_path / 'baseline'
    candidate = tmp_path / 'candidate'

    _write_page(baseline, 'page_0001.md', 'Intro\n\n![](fig1.png)\n\n- - bullet\n')
    _write_page(candidate, 'page_0001.md', 'Intro\n\n![](fig2.png)\n\n- bullet\n')

    out_json = tmp_path / 'compare.json'
    subprocess.run(
        [
            sys.executable,
            str(ROOT / 'scripts' / 'chandra_quality_compare.py'),
            '--baseline-dir',
            str(baseline),
            '--candidate-dir',
            str(candidate),
            '--emit-normalized-pages',
            '--out-json',
            str(out_json),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(out_json.read_text(encoding='utf-8'))
    assert 'aggregate' in report
    assert 'normalized_aggregate' in report
    assert 'normalized_recommendation' in report
    assert 'failure_fingerprint' in report
    assert 'normalized_failure_fingerprint' in report
    assert 'normalized_pages' in report
    assert report['normalization']['per_page_stats']['page_0001.md']['baseline']['markdown_images_removed'] == 1
    assert report['normalized_aggregate']['sequence_ratio_mean'] >= report['aggregate']['sequence_ratio_mean']


def test_failure_fingerprint_surfaces_under_generation_and_table_drift():
    _failure_fingerprint = _MODULE._failure_fingerprint
    PageMetrics = _MODULE.PageMetrics

    rows = [
        PageMetrics(
            page='page_0001.md',
            baseline_chars=1000,
            candidate_chars=700,
            char_ratio=0.7,
            sequence_ratio=0.72,
            jaccard_words=0.75,
            code_fence_delta=0,
            html_table_delta=0,
            html_div_delta=0,
            markdown_table_row_delta=4,
        ),
        PageMetrics(
            page='page_0002.md',
            baseline_chars=1000,
            candidate_chars=1300,
            char_ratio=1.3,
            sequence_ratio=0.9,
            jaccard_words=0.8,
            code_fence_delta=0,
            html_table_delta=0,
            html_div_delta=0,
            markdown_table_row_delta=0,
        ),
    ]
    fp = _failure_fingerprint(rows)
    assert fp['under_generated_pages'] == ['page_0001.md']
    assert fp['over_generated_pages'] == ['page_0002.md']
    assert fp['low_sequence_pages'] == ['page_0001.md']
    assert fp['table_expansion_pages'] == ['page_0001.md']
    assert fp['high_structural_drift_pages'] == ['page_0001.md']
    assert fp['counts']['under_generated_pages'] == 1


def test_recommendation_downgrades_expansion_prone_outputs():
    _recommendation = _MODULE._recommendation

    agg = {
        'sequence_ratio_mean': 0.855973,
        'jaccard_words_mean': 0.849699,
        'char_ratio_mean': 1.278185,
        'char_ratio_p10': 1.113063,
        'char_ratio_p90': 1.302061,
        'structure_penalty_mean': 3.2,
        'structure_penalty_max': 8,
    }
    rec = _recommendation(agg)
    assert rec['verdict'] == 'warn'
