import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_chandra_closure_check_enforces_versioned_benchmark_semantics(tmp_path: Path):
    benchmark_path = tmp_path / "benchmark.json"
    quality_path = tmp_path / "quality.json"

    benchmark_payload = {
        "benchmark_schema_version": 1,
        "runtime_semantics_version": "chandra_runtime_v1",
        "request_shape_version": "page_request_v1",
        "runtime": {"compatibility_snapshot": {"effective_runtime_backend": "vllm"}},
        "passes": [
            {"name": "cold", "wall_seconds": 12.0, "pages_per_second": 0.08},
            {"name": "warm_1", "wall_seconds": 8.0, "pages_per_second": 0.12},
            {"name": "warm_2", "wall_seconds": 9.0, "pages_per_second": 0.11},
        ],
    }
    quality_payload = {
        "baseline_dir": "docs_tmp/chandra/analysis/20260325_chandra1_speed_quality_10p/chandra1_speed_10p_pages",
        "recommendation": {"verdict": "pass"},
        "normalized_recommendation": {"verdict": "pass"},
    }

    benchmark_path.write_text(json.dumps(benchmark_payload), encoding="utf-8")
    quality_path.write_text(json.dumps(quality_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "chandra_closure_check.py"),
            "--benchmark-json",
            str(benchmark_path),
            "--quality-json",
            str(quality_path),
            "--require-runtime-compatibility-snapshot",
            "--require-baseline-dir",
            "docs_tmp/chandra/analysis/20260325_chandra1_speed_quality_10p/chandra1_speed_10p_pages",
            "--require-normalized-quality-verdict",
            "pass",
            "--warm-min-pages-per-second",
            "0.1",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed["overall_pass"] is True
    assert parsed["benchmark_schema_version"] == 1
    assert parsed["runtime_semantics_version"] == "chandra_runtime_v1"
    assert parsed["request_shape_version"] == "page_request_v1"
    assert parsed["gates"]["runtime_compatibility_snapshot_present"]["pass"] is True
    assert parsed["gates"]["baseline_dir_match"]["pass"] is True
    assert parsed["gates"]["normalized_quality_verdict_match"]["pass"] is True
    assert parsed["gates"]["warm_pages_per_second_geq_threshold"]["pass"] is True


def test_chandra_closure_check_can_gate_on_runtime_compatibility(tmp_path: Path):
    benchmark_path = tmp_path / "benchmark.json"
    quality_path = tmp_path / "quality.json"
    compatibility_path = tmp_path / "compatibility.json"

    benchmark_payload = {
        "benchmark_schema_version": 1,
        "runtime_semantics_version": "chandra_runtime_v1",
        "request_shape_version": "page_request_v1",
        "passes": [
            {"name": "cold", "wall_seconds": 12.0},
            {"name": "warm_1", "wall_seconds": 8.0},
            {"name": "warm_2", "wall_seconds": 9.0},
        ],
    }
    quality_payload = {
        "recommendation": {"verdict": "pass"},
        "normalized_recommendation": {"verdict": "warn"},
    }
    compatibility_payload = {
        "current_lane": {"status": "ready"},
        "target_lane": {"status": "blocked"},
        "runtime": {"status": "unknown"},
    }

    benchmark_path.write_text(json.dumps(benchmark_payload), encoding="utf-8")
    quality_path.write_text(json.dumps(quality_payload), encoding="utf-8")
    compatibility_path.write_text(json.dumps(compatibility_payload), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "chandra_closure_check.py"),
            "--benchmark-json",
            str(benchmark_path),
            "--quality-json",
            str(quality_path),
            "--compatibility-json",
            str(compatibility_path),
            "--require-current-lane-status",
            "ready",
            "--require-target-lane-status",
            "blocked",
            "--require-runtime-backend-status",
            "unknown",
            "--require-normalized-quality-verdict",
            "warn",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed["overall_pass"] is True
    assert parsed["gates"]["current_lane_status_match"]["observed"] == "ready"
    assert parsed["gates"]["target_lane_status_match"]["observed"] == "blocked"
    assert parsed["gates"]["runtime_backend_status_match"]["observed"] == "unknown"
    assert parsed["gates"]["normalized_quality_verdict_match"]["observed"] == "warn"
