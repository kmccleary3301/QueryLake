import asyncio
import json
import types
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.operation_classes import ray_chandra_class
from QueryLake.operation_classes.ray_chandra_class import build_chandra_runtime_compatibility_snapshot
from scripts import chandra_benchmark_pdf


class _FakeRuntime:
    def __init__(self, model_path: str) -> None:
        self._model_path = model_path
        self._configured_runtime_backend = "vllm_server"
        self._runtime_backend = "hf"
        self._processor = object()
        self._model = None
        self._vllm_llm = None
        self._default_profile = "speed"
        self._fixed_max_new_tokens = 768
        self._profile_settings = {
            "speed": {"max_image_pixels": 589_824, "max_new_tokens": 512, "repetition_penalty": 1.05},
            "balanced": {"max_image_pixels": 1_048_576, "max_new_tokens": 768, "repetition_penalty": 1.0},
            "quality": {"max_image_pixels": 2_097_152, "max_new_tokens": 1024, "repetition_penalty": 1.1},
        }
        self._vllm_server_base_urls = ["http://127.0.0.1:8022/v1"]
        self._vllm_server_model = "chandra"
        self._vllm_server_allowed_local_media_path = "/tmp/querylake-chandra-media"
        self._vllm_server_timeout_seconds = 120.0
        self._vllm_server_max_retries = 2
        self._vllm_server_retry_backoff_seconds = 0.5
        self._vllm_server_parallel_requests = 24
        self._vllm_server_probe_on_init = True
        self._vllm_server_fallback_to_hf_on_error = True
        self._vllm_server_circuit_breaker_threshold = 3
        self._vllm_server_circuit_open = False
        self._vllm_server_consecutive_failures = 0
        self._vllm_server_rr_index = 7

    def runtime_compatibility_snapshot(self):
        return build_chandra_runtime_compatibility_snapshot(self)


@pytest.fixture()
def fake_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "models" / "chandra"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text(
        json.dumps(
            {
                "model_type": "qwen3_vl",
                "architectures": ["Qwen3VLForConditionalGeneration"],
                "transformers_version": "4.57.1",
                "base_model_name_or_path": "Qwen/Qwen3-VL-8B-Instruct",
            }
        ),
        encoding="utf-8",
    )
    return model_dir


def test_runtime_compatibility_snapshot_includes_versions_and_model_config(monkeypatch, fake_model_dir: Path):
    version_map = {
        "torch": "2.10.0",
        "transformers": "4.57.1",
        "vllm": "0.18.0",
        "ray": "2.48.0",
        "pillow": "11.0.0",
        "pypdfium2": "4.30.0",
    }

    def _fake_version(package_name: str) -> str:
        return version_map[package_name.lower()]

    monkeypatch.setattr(ray_chandra_class.importlib_metadata, "version", _fake_version)
    runtime = _FakeRuntime(str(fake_model_dir))

    snapshot = build_chandra_runtime_compatibility_snapshot(runtime)

    assert snapshot["snapshot_version"] == 1
    assert snapshot["configured_runtime_backend"] == "vllm_server"
    assert snapshot["effective_runtime_backend"] == "hf"
    assert snapshot["model_path"].endswith("models/chandra")
    assert snapshot["model_path_is_local"] is True
    assert snapshot["model_config"]["model_type"] == "qwen3_vl"
    assert snapshot["model_config"]["architectures"] == ["Qwen3VLForConditionalGeneration"]
    assert snapshot["package_versions"] == version_map
    assert snapshot["runtime_state"] == {
        "processor_initialized": True,
        "model_initialized": False,
        "vllm_llm_initialized": False,
    }
    assert snapshot["profile_defaults"]["speed_max_image_pixels"] == 589_824
    assert snapshot["profile_defaults"]["fixed_max_new_tokens"] == 768
    assert snapshot["profile_defaults"]["speed_max_new_tokens"] == 512
    assert snapshot["profile_defaults"]["balanced_max_new_tokens"] == 768
    assert snapshot["profile_defaults"]["quality_max_new_tokens"] == 1024
    assert snapshot["profile_defaults"]["speed_repetition_penalty"] == 1.05
    assert snapshot["profile_defaults"]["balanced_repetition_penalty"] == 1.0
    assert snapshot["profile_defaults"]["quality_repetition_penalty"] == 1.1
    assert snapshot["vllm_server"]["rr_index"] == 7


def test_benchmark_json_includes_runtime_compatibility_snapshot(monkeypatch, tmp_path: Path):
    class _FakeRuntimeForBenchmark(_FakeRuntime):
        def __init__(self, *args, **kwargs):
            super().__init__(kwargs["model_path"])

        async def transcribe(self, image, prompt, max_new_tokens, max_image_pixels, profile):
            return f"{prompt}:{image}"

    async def _fake_run_pass(*args, **kwargs):
        return chandra_benchmark_pdf.PassStats(
            name="cold",
            wall_seconds=1.0,
            page_latencies=[1.0],
            total_chars=4,
            outputs=["ok"],
        )

    monkeypatch.setattr(chandra_benchmark_pdf, "_render_pdf_pages", lambda *args, **kwargs: ["page-1"])
    monkeypatch.setattr(chandra_benchmark_pdf, "_resolve_runtime_class", lambda: _FakeRuntimeForBenchmark)
    monkeypatch.setattr(chandra_benchmark_pdf, "_run_pass", _fake_run_pass)
    monkeypatch.setattr(chandra_benchmark_pdf, "_run_adaptive_pass", None, raising=False)
    monkeypatch.setattr(ray_chandra_class.importlib_metadata, "version", lambda name: f"{name}-version")

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

    args = types.SimpleNamespace(
        pdf="dummy.pdf",
        model=str(model_dir),
        prompt="Convert",
        dpi=144,
        render_cache_dir=None,
        max_pages=1,
        concurrency=1,
        warm_runs=0,
        max_batch_size=1,
        max_batch_wait_ms=15,
        max_new_tokens=768,
        max_image_pixels=2_097_152,
        profile_speed_repetition_penalty=1.05,
        profile_balanced_repetition_penalty=1.0,
            profile_quality_repetition_penalty=1.1,
            bad_word=[],
            torch_dtype="auto",
        runtime_backend="vllm_server",
        require_effective_runtime_backend="",
        vllm_trust_remote_code=False,
        vllm_tensor_parallel_size=1,
        vllm_data_parallel_size=1,
        vllm_gpu_memory_utilization=0.95,
        vllm_max_model_len=131072,
        vllm_max_num_seqs=8,
        vllm_dtype="auto",
        vllm_enforce_eager=False,
        vllm_disable_log_stats=True,
        vllm_async_scheduling=False,
        vllm_server_base_url="http://127.0.0.1:8022/v1",
        vllm_server_base_urls="",
        vllm_server_model="chandra",
        vllm_server_api_key="",
        vllm_server_timeout_seconds=120.0,
        vllm_server_max_retries=2,
        vllm_server_retry_backoff_seconds=0.5,
        vllm_server_parallel_requests=24,
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=True,
        vllm_server_circuit_breaker_threshold=3,
        profile="speed",
        disable_cache=True,
        use_profile_defaults=False,
        adaptive=False,
        transport_mode="page",
        adaptive_low_tokens=512,
        adaptive_high_tokens=1024,
        adaptive_low_pixels=1_048_576,
        adaptive_high_pixels=2_097_152,
        adaptive_min_chars=450,
        out_json=None,
        out_markdown=None,
        out_pages_dir=None,
        markdown_pass="last",
    )

    result = asyncio.run(chandra_benchmark_pdf._run(args))
    assert result["runtime"]["compatibility_snapshot"]["configured_runtime_backend"] == "vllm_server"
    assert result["runtime"]["compatibility_snapshot"]["model_config"]["model_type"] == "qwen3_vl"


def test_benchmark_run_can_require_effective_runtime_backend(monkeypatch, tmp_path: Path):
    class _FakeRuntimeForBenchmark(_FakeRuntime):
        def __init__(self, *args, **kwargs):
            super().__init__(kwargs["model_path"])

    async def _fake_run_pass(*args, **kwargs):
        return chandra_benchmark_pdf.PassStats(
            name="cold",
            wall_seconds=1.0,
            page_latencies=[1.0],
            total_chars=4,
            outputs=["ok"],
        )

    monkeypatch.setattr(chandra_benchmark_pdf, "_render_pdf_pages", lambda *args, **kwargs: ["page-1"])
    monkeypatch.setattr(chandra_benchmark_pdf, "_resolve_runtime_class", lambda: _FakeRuntimeForBenchmark)
    monkeypatch.setattr(chandra_benchmark_pdf, "_run_pass", _fake_run_pass)

    model_dir = tmp_path / "models" / "chandra"
    model_dir.mkdir(parents=True, exist_ok=True)
    (model_dir / "config.json").write_text(json.dumps({"model_type": "qwen3_vl"}), encoding="utf-8")

    args = types.SimpleNamespace(
        pdf="dummy.pdf",
        model=str(model_dir),
        prompt="Convert",
        dpi=144,
        render_cache_dir=None,
        max_pages=1,
        concurrency=1,
        warm_runs=0,
        max_batch_size=1,
        max_batch_wait_ms=15,
        max_new_tokens=768,
        max_image_pixels=2_097_152,
        profile_speed_repetition_penalty=1.05,
        profile_balanced_repetition_penalty=1.0,
        profile_quality_repetition_penalty=1.1,
        bad_word=[],
        torch_dtype="auto",
        runtime_backend="vllm",
        require_effective_runtime_backend="vllm_server",
        vllm_trust_remote_code=False,
        vllm_tensor_parallel_size=1,
        vllm_data_parallel_size=1,
        vllm_gpu_memory_utilization=0.95,
        vllm_max_model_len=131072,
        vllm_max_num_seqs=8,
        vllm_dtype="auto",
        vllm_enforce_eager=False,
        vllm_disable_log_stats=True,
        vllm_async_scheduling=False,
        vllm_server_base_url="http://127.0.0.1:8022/v1",
        vllm_server_base_urls="",
        vllm_server_model="chandra",
        vllm_server_api_key="",
        vllm_server_timeout_seconds=120.0,
        vllm_server_max_retries=2,
        vllm_server_retry_backoff_seconds=0.5,
        vllm_server_parallel_requests=24,
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=True,
        vllm_server_circuit_breaker_threshold=3,
        profile="speed",
        disable_cache=True,
        use_profile_defaults=False,
        adaptive=False,
        transport_mode="page",
        adaptive_low_tokens=512,
        adaptive_high_tokens=1024,
        adaptive_low_pixels=1_048_576,
        adaptive_high_pixels=2_097_152,
        adaptive_min_chars=450,
        out_json=None,
        out_markdown=None,
        out_pages_dir=None,
        markdown_pass="last",
    )

    with pytest.raises(RuntimeError, match="effective runtime backend"):
        asyncio.run(chandra_benchmark_pdf._run(args))
