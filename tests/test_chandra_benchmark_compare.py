import json
import subprocess
import sys
from pathlib import Path


def _write_benchmark(path: Path, *, transport_mode: str, request_shape_version: str, pps: float, wall: float) -> None:
    payload = {
        "benchmark_schema_version": 1,
        "runtime_semantics_version": "chandra_runtime_v1",
        "request_shape_version": request_shape_version,
        "pdf": "sample.pdf",
        "render": {"dpi": 144, "pages": 3, "seconds": 0.1, "cache_dir": None},
        "runtime": {
            "model": "models/chandra",
            "runtime_backend": "vllm_server",
            "profile": "balanced",
            "transport_mode": transport_mode,
            "use_profile_defaults": True,
            "max_batch_size": 24,
            "max_batch_wait_ms": 15,
            "max_new_tokens": None,
            "max_image_pixels": None,
            "concurrency": 24,
            "vllm_server_base_urls": "http://127.0.0.1:8022/v1,http://127.0.0.1:8023/v1",
        },
        "passes": [
            {
                "name": "cold",
                "pages": 3,
                "wall_seconds": wall * 1.1,
                "pages_per_second": pps * 0.9,
                "total_chars": 120,
                "latency_ms": {"mean": 100.0, "median": 95.0, "p95": 140.0, "max": 160.0},
            },
            {
                "name": "warm_1",
                "pages": 3,
                "wall_seconds": wall,
                "pages_per_second": pps,
                "total_chars": 128,
                "latency_ms": {"mean": 90.0, "median": 85.0, "p95": 130.0, "max": 150.0},
                "metadata": {"transport_mode": transport_mode},
            },
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_benchmark_compare_reports_transport_and_primary_delta(tmp_path):
    baseline = tmp_path / "baseline.json"
    candidate = tmp_path / "candidate.json"
    out_json = tmp_path / "compare.json"
    out_md = tmp_path / "compare.md"

    _write_benchmark(baseline, transport_mode="page", request_shape_version="page_request_v1", pps=1.0, wall=3.0)
    _write_benchmark(candidate, transport_mode="batch", request_shape_version="batch_request_v1", pps=1.25, wall=2.4)

    subprocess.run(
        [
            sys.executable,
            "scripts/chandra_benchmark_compare.py",
            "--baseline-json",
            str(baseline),
            "--candidate-json",
            str(candidate),
            "--out-json",
            str(out_json),
            "--out-md",
            str(out_md),
        ],
        cwd=Path(__file__).resolve().parent.parent,
        check=True,
    )

    report = json.loads(out_json.read_text(encoding="utf-8"))
    assert report["transport_changed"] is True
    assert report["recommendation"]["verdict"] == "improve"
    assert report["primary_delta"]["pages_per_second"] == 0.25
    assert report["baseline"]["primary_pass"]["name"] == "warm_1"
    assert report["candidate"]["primary_pass"]["metadata"]["transport_mode"] == "batch"
    assert len(report["common_passes"]) == 2
    assert out_md.read_text(encoding="utf-8").startswith("# Chandra Benchmark Comparison")

