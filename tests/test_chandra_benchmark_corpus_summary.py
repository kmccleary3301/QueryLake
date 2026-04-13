import json
import subprocess
import sys
from pathlib import Path


def _write_benchmark(path: Path, *, backend: str, pps: float) -> None:
    payload = {
        "passes": [
            {
                "name": "warm_1",
                "pages": 3,
                "wall_seconds": 3.0 / pps,
                "pages_per_second": pps,
                "total_chars": 42,
                "latency_ms": {"mean": 100.0, "median": 100.0, "p95": 100.0, "max": 100.0},
            }
        ],
        "runtime": {
            "runtime_backend": backend,
            "profile": "balanced",
            "use_profile_defaults": True,
            "max_image_pixels": None,
            "max_new_tokens": None,
            "vllm_server_base_urls": None,
        },
        "render": {"seconds": 0.1, "dpi": 144, "pages": 3, "cache_dir": None},
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_corpus_summary_sorts_top_entries_and_groups_backends(tmp_path):
    bench_dir = tmp_path / "benchmarks"
    bench_dir.mkdir()
    _write_benchmark(bench_dir / "a.json", backend="hf", pps=0.5)
    _write_benchmark(bench_dir / "b.json", backend="vllm_server", pps=1.25)
    _write_benchmark(bench_dir / "c.json", backend="vllm", pps=0.9)
    (bench_dir / "skip.json").write_text(json.dumps({"not": "a benchmark"}), encoding="utf-8")

    out_json = tmp_path / "summary.json"
    subprocess.run(
        [
            sys.executable,
            "scripts/chandra_benchmark_corpus_summary.py",
            "--benchmarks-dir",
            str(bench_dir),
            "--out-json",
            str(out_json),
            "--top-n",
            "2",
        ],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )

    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["benchmark_file_count"] == 3
    assert report["top_overall"][0]["file"] == "b.json"
    assert report["top_vllm_server"][0]["file"] == "b.json"
    assert report["top_hf"][0]["file"] == "a.json"
    assert report["top_vllm"][0]["file"] == "c.json"
    assert report["aggregate"]["pps_max"] == 1.25

