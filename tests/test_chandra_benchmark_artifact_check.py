import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def test_benchmark_artifact_check_can_require_runtime_snapshot(tmp_path: Path) -> None:
    benchmark_path = tmp_path / "benchmark.json"
    benchmark_payload = {
        "benchmark_schema_version": 1,
        "runtime_semantics_version": "chandra_runtime_v1",
        "request_shape_version": "page_request_v1",
        "runtime": {"compatibility_snapshot": {"effective_runtime_backend": "vllm"}},
    }
    benchmark_path.write_text(json.dumps(benchmark_payload), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "chandra_benchmark_artifact_check.py"),
            "--benchmark-json",
            str(benchmark_path),
            "--require-request-shape-version",
            "page_request_v1",
            "--require-runtime-compatibility-snapshot",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    parsed = json.loads(result.stdout)
    assert parsed["pass"] is True
    assert parsed["failures"] == []
