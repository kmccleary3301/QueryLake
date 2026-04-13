import json
from pathlib import Path
import sys
import types

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import chandra_runtime_compatibility_report as report_script


def test_runtime_compatibility_report_classifies_current_lane_and_target_lane(tmp_path: Path, monkeypatch):
    current_model_dir = tmp_path / "models" / "chandra"
    current_model_dir.mkdir(parents=True, exist_ok=True)
    (current_model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_vl",
                "architectures": ["Qwen3VLForConditionalGeneration"],
                "transformers_version": "4.57.1",
            }
        ),
        encoding="utf-8",
    )

    version_map = {
        "torch": "2.10.0",
        "transformers": "4.57.1",
        "vllm": "0.18.0",
        "ray": "2.48.0",
        "pillow": "11.0.0",
        "pypdfium2": "4.30.0",
    }
    monkeypatch.setattr(report_script.importlib_metadata, "version", lambda name: version_map[name.lower()])

    report = report_script.build_report(current_model_path=str(current_model_dir))

    assert report["overall_status"] == "blocked"
    assert report["current_lane"]["status"] == "ready"
    assert report["target_lane"]["status"] == "blocked"
    assert report["target_lane"]["blockers"]
    assert report["package_versions"] == version_map
    assert report["runtime"]["status"] == "unknown"
    assert report["model_paths"]["current"] == str(current_model_dir)
    assert report["model_paths"]["target"] == str(current_model_dir)


def test_runtime_compatibility_report_accepts_separate_target_model_path(tmp_path: Path, monkeypatch):
    current_model_dir = tmp_path / "models" / "chandra"
    current_model_dir.mkdir(parents=True, exist_ok=True)
    (current_model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_vl",
                "architectures": ["Qwen3VLForConditionalGeneration"],
            }
        ),
        encoding="utf-8",
    )
    target_model_dir = tmp_path / "models" / "chandra2"
    target_model_dir.mkdir(parents=True, exist_ok=True)
    (target_model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_5",
                "architectures": ["Qwen3_5ForConditionalGeneration"],
            }
        ),
        encoding="utf-8",
    )

    version_map = {
        "torch": "2.10.0",
        "transformers": "4.57.1",
        "vllm": "0.18.0",
        "ray": "2.48.0",
        "pillow": "11.0.0",
        "pypdfium2": "4.30.0",
    }
    monkeypatch.setattr(report_script.importlib_metadata, "version", lambda name: version_map[name.lower()])

    report = report_script.build_report(
        current_model_path=str(current_model_dir),
        target_model_path=str(target_model_dir),
    )

    assert report["overall_status"] == "ready"
    assert report["current_lane"]["status"] == "ready"
    assert report["target_lane"]["status"] == "ready"
    assert report["current_lane"]["model_path"] == str(current_model_dir)
    assert report["target_lane"]["model_path"] == str(target_model_dir)
    assert report["target_lane"]["observed"]["model_type"] == "qwen3_5"


def test_runtime_compatibility_report_uses_snapshot_when_available(tmp_path: Path, monkeypatch):
    model_dir = tmp_path / "models" / "chandra"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_vl",
                "architectures": ["Qwen3VLForConditionalGeneration"],
            }
        ),
        encoding="utf-8",
    )

    version_map = {
        "torch": "2.10.0",
        "transformers": "4.57.1",
        "vllm": "0.18.0",
        "ray": "2.48.0",
        "pillow": "11.0.0",
        "pypdfium2": "4.30.0",
    }
    monkeypatch.setattr(report_script.importlib_metadata, "version", lambda name: version_map[name.lower()])

    benchmark_json = {
        "runtime": {
            "compatibility_snapshot": {
                "configured_runtime_backend": "vllm_server",
                "effective_runtime_backend": "hf",
                "model_path": str(model_dir),
                "package_versions": version_map,
                "profile_defaults": {"speed_max_image_pixels": 589_824},
                "vllm_server": {"base_urls": ["http://127.0.0.1:8022/v1"]},
                "runtime_state": {"processor_initialized": True, "model_initialized": False, "vllm_llm_initialized": False},
            }
        }
    }

    report = report_script.build_report(current_model_path=str(model_dir), benchmark_json=benchmark_json)

    assert report["benchmark_runtime_snapshot_present"] is True
    assert report["runtime"]["status"] == "degraded"
    assert report["runtime"]["configured_runtime_backend"] == "vllm_server"
    assert report["runtime"]["effective_runtime_backend"] == "hf"
    assert "runtime_backend_fallback:vllm_server->hf" in report["runtime"]["blockers"]


def test_runtime_compatibility_report_can_capture_probe_results(tmp_path: Path, monkeypatch):
    current_model_dir = tmp_path / "models" / "chandra"
    current_model_dir.mkdir(parents=True, exist_ok=True)
    (current_model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_vl",
                "architectures": ["Qwen3VLForConditionalGeneration"],
            }
        ),
        encoding="utf-8",
    )

    version_map = {
        "torch": "2.10.0",
        "transformers": "4.57.1",
        "vllm": "0.18.0",
        "ray": "2.48.0",
        "pillow": "11.0.0",
        "pypdfium2": "4.30.0",
    }
    monkeypatch.setattr(report_script.importlib_metadata, "version", lambda name: version_map[name.lower()])

    def _fake_run(cmd, capture_output, text, check):
        payload = {
            "status": "ok",
            "stage": "generate",
            "timing_seconds": 1.23,
        }
        return types.SimpleNamespace(returncode=0, stdout=json.dumps(payload), stderr="")

    monkeypatch.setattr(report_script.subprocess, "run", _fake_run)

    report = report_script.build_report(
        current_model_path=str(current_model_dir),
        probe_script="scripts/chandra_vllm_probe.py",
        probe_pdf="dummy.pdf",
    )

    assert report["probes"]["current"]["status"] == "ok"
    assert report["probes"]["current"]["stage"] == "generate"
    assert report["probes"]["current"]["_probe_returncode"] == 0
