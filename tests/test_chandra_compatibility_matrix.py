import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_compatibility_matrix_renders_current_target_runtime_and_packages(tmp_path: Path) -> None:
    compatibility_path = tmp_path / "compatibility.json"
    benchmark_path = tmp_path / "benchmark.json"
    compatibility_payload = {
        "current_lane": {
            "model_path": "models/chandra",
            "observed": {"model_type": "qwen3_vl", "architectures": ["Qwen3VLForConditionalGeneration"]},
            "status": "ready",
        },
        "target_lane": {
            "model_path": "models/chandra2",
            "observed": {"model_type": "qwen3_5", "architectures": ["Qwen3_5ForConditionalGeneration"]},
            "status": "ready",
        },
        "runtime": {
            "configured_runtime_backend": "vllm",
            "effective_runtime_backend": "vllm",
            "status": "ready",
        },
        "package_versions": {
            "torch": "2.10.0",
            "transformers": "4.57.1",
            "vllm": "0.18.0",
            "ray": "2.48.0",
            "pillow": "11.0.0",
            "pypdfium2": "4.30.0",
        },
        "probes": {"current": {"status": "ok"}, "target": {"status": "ok"}},
    }
    benchmark_payload = {
        "runtime_semantics_version": "chandra_runtime_v1",
        "request_shape_version": "page_request_v1",
        "runtime": {"compatibility_snapshot": {"effective_runtime_backend": "vllm"}},
    }
    compatibility_path.write_text(json.dumps(compatibility_payload), encoding="utf-8")
    benchmark_path.write_text(json.dumps(benchmark_payload), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "chandra_compatibility_matrix.py"),
            "--compatibility-json",
            str(compatibility_path),
            "--benchmark-json",
            str(benchmark_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed["current_lane"]["model_type"] == "qwen3_vl"
    assert parsed["target_lane"]["model_type"] == "qwen3_5"
    assert parsed["runtime"]["status"] == "ready"
    assert parsed["runtime"]["configured_backend"] == "vllm"
    assert parsed["runtime"]["effective_backend"] == "vllm"
    assert parsed["benchmark_runtime_snapshot_present"] is True
