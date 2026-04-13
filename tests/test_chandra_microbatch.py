import asyncio
from pathlib import Path
import sys

import pytest
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.operation_classes.ray_chandra_class import ChandraDeployment, ChandraImagePayload, ChandraRequest, _MicroBatcher

_ChandraImpl = ChandraDeployment.func_or_class


@pytest.mark.asyncio
async def test_microbatcher_batches_requests():
    batches = []

    async def process(requests):
        batches.append(len(requests))
        return [req.prompt for req in requests]

    batcher = _MicroBatcher(process, max_batch_size=4, max_batch_wait_ms=10)
    batcher.start()

    async def submit(prompt):
        return await batcher.submit(ChandraRequest(image="img", prompt=prompt, max_new_tokens=1))

    results = await asyncio.gather(
        submit("a"),
        submit("b"),
        submit("c"),
        submit("d"),
    )
    assert results == ["a", "b", "c", "d"]
    assert batches[0] == 4
    await batcher.shutdown()


@pytest.mark.asyncio
async def test_transcribe_many_preserves_order_and_forwards_args(monkeypatch):
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    seen = []

    async def fake_transcribe(**kwargs):
        await asyncio.sleep(0)
        seen.append(kwargs)
        return f"out:{len(seen)}"

    monkeypatch.setattr(deployment, "transcribe", fake_transcribe)

    outputs = await deployment.transcribe_many(
        images=[Image.new("RGB", (1, 1), color="white"), Image.new("RGB", (1, 1), color="black")],
        profile="balanced",
        prompt="hello",
        blocked_phrases=["![]()", "| --- | --- | --- |"],
    )

    assert outputs == ["out:1", "out:2"]
    assert len(seen) == 2
    assert {item["prompt"] for item in seen} == {"hello"}
    assert {item["profile"] for item in seen} == {"balanced"}
    assert {tuple(item["blocked_phrases"]) for item in seen} == {("![]()", "| --- | --- | --- |")}


def test_filter_vllm_constructor_kwargs_filters_unknown_and_none():
    candidate = {
        "model": "models/chandra",
        "dtype": "auto",
        "max_model_len": 131072,
        "enable_chunked_prefill": None,
        "unknown_key": "drop-me",
    }
    accepted = {"model", "dtype", "max_model_len", "enable_chunked_prefill"}
    filtered = _ChandraImpl._filter_vllm_constructor_kwargs(candidate, accepted)
    assert filtered == {
        "model": "models/chandra",
        "dtype": "auto",
        "max_model_len": 131072,
    }


def test_extract_vllm_output_text_handles_common_shapes():
    class _Output:
        def __init__(self, text):
            self.text = text

    class _WithOutputs:
        def __init__(self, text):
            self.outputs = [_Output(text)]

    assert _ChandraImpl._extract_vllm_output_text(None) == ""
    assert _ChandraImpl._extract_vllm_output_text(_WithOutputs("hello")) == "hello"
    assert _ChandraImpl._extract_vllm_output_text("raw") == "raw"


def test_extract_openai_message_content_handles_string_and_parts():
    assert _ChandraImpl._extract_openai_message_content("hello") == "hello"
    assert _ChandraImpl._extract_openai_message_content(None) == ""
    structured = [
        {"type": "text", "text": "line one"},
        {"type": "output_text", "text": "line two"},
        {"type": "ignored", "content": "line three"},
    ]
    assert _ChandraImpl._extract_openai_message_content(structured) == "line one\nline two\nline three"


def test_runtime_backend_vllm_server_can_initialize_without_probe():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    assert deployment._runtime_backend == "vllm_server"
    assert deployment._vllm_server_base_url.endswith("/v1")


def test_normalize_vllm_server_base_urls_from_csv_and_deduplicate():
    normalized = _ChandraImpl._normalize_vllm_server_base_urls(
        "http://127.0.0.1:8022,http://127.0.0.1:8022/v1,http://127.0.0.1:8023/",
        default_url="http://127.0.0.1:9000/v1",
    )
    assert normalized == [
        "http://127.0.0.1:8022/v1",
        "http://127.0.0.1:8023/v1",
    ]


def test_vllm_server_round_robin_endpoint_selection():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
        vllm_server_base_urls=["http://127.0.0.1:8022", "http://127.0.0.1:8023/v1"],
    )
    sequence = [deployment._next_vllm_server_base_url() for _ in range(5)]
    assert sequence == [
        "http://127.0.0.1:8022/v1",
        "http://127.0.0.1:8023/v1",
        "http://127.0.0.1:8022/v1",
        "http://127.0.0.1:8023/v1",
        "http://127.0.0.1:8022/v1",
    ]


def test_runtime_honors_profile_token_knobs_and_explicit_max_new_tokens():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
        max_new_tokens=64,
        profile_speed_max_new_tokens=128,
        profile_balanced_max_new_tokens=256,
        profile_quality_max_new_tokens=512,
        adaptive_high_max_new_tokens=2048,
    )
    assert deployment._fixed_max_new_tokens == 64
    assert deployment._profile_settings["speed"]["max_new_tokens"] == 128
    assert deployment._profile_settings["balanced"]["max_new_tokens"] == 256
    assert deployment._profile_settings["quality"]["max_new_tokens"] == 512
    assert deployment._adaptive_high_max_new_tokens == 2048


def test_clean_output_removes_empty_markdown_image_placeholders():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    cleaned = deployment._clean_output(
        "![NVIDIA logo]()\n\nTitle\n\n![Warning triangle icon]()\n\nBody",
        prompt="Convert this page into clean Markdown.",
    )
    assert "![NVIDIA logo]()" not in cleaned
    assert "![Warning triangle icon]()" not in cleaned
    assert cleaned == "Title\n\nBody"


def test_clean_output_compacts_contents_tables():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    text = (
        "Scalable Training of Mixture-of-Experts Models with Megatron Core\n"
        "Contents\n\n"
        "| **1** | **Introduction** | **5** |\n"
        "| --- | --- | --- |\n"
        "| 1.1 | Mixture of Experts | 5 |\n"
        "| 1.2 | Challenges in Training Large-Scale MoE Models | 6 |\n"
    )
    cleaned = deployment._clean_output(text, prompt="Convert this page into clean Markdown.")
    assert "| **1** | **Introduction** | **5** |" in cleaned
    assert "| 1.1 Mixture of Experts | 5 |" in cleaned
    assert "| 1.2 Challenges in Training Large-Scale MoE Models | 6 |" in cleaned


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile", "expected_max_new_tokens", "expected_repetition_penalty"),
    [
        ("speed", 512, 1.05),
        ("balanced", 768, 1.0),
        ("quality", 1024, 1.1),
    ],
)
async def test_transcribe_uses_profile_defaults(profile, expected_max_new_tokens, expected_repetition_penalty):
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
        profile_speed_repetition_penalty=1.05,
        profile_balanced_repetition_penalty=1.0,
        profile_quality_repetition_penalty=1.1,
    )
    seen = []

    class _FakeBatcher:
        async def submit(self, request):
            seen.append(request)
            return "ok"

    deployment._batcher = _FakeBatcher()

    result = await deployment.transcribe(
        image=Image.new("RGB", (4, 4), color="white"),
        profile=profile,
        cache_bypass=True,
    )

    assert result == "ok"
    assert len(seen) == 1
    assert seen[0].max_new_tokens == expected_max_new_tokens
    assert seen[0].repetition_penalty == expected_repetition_penalty


@pytest.mark.asyncio
async def test_transcribe_explicit_max_new_tokens_overrides_profile_default():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    seen = []

    class _FakeBatcher:
        async def submit(self, request):
            seen.append(request)
            return "ok"

    deployment._batcher = _FakeBatcher()

    result = await deployment.transcribe(
        image=Image.new("RGB", (4, 4), color="white"),
        profile="speed",
        max_new_tokens=1280,
        cache_bypass=True,
    )

    assert result == "ok"
    assert len(seen) == 1
    assert seen[0].max_new_tokens == 1280
    assert seen[0].escalation_max_new_tokens >= 1280


@pytest.mark.asyncio
async def test_transcribe_forwards_blocked_phrases_into_request():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    seen = []

    class _FakeBatcher:
        async def submit(self, request):
            seen.append(request)
            return "ok"

    deployment._batcher = _FakeBatcher()

    result = await deployment.transcribe(
        image=Image.new("RGB", (4, 4), color="white"),
        profile="speed",
        blocked_phrases=["![]()", "| --- | --- | --- |"],
        cache_bypass=True,
    )

    assert result == "ok"
    assert len(seen) == 1
    assert seen[0].blocked_phrases == ("![]()", "| --- | --- | --- |")


def test_cache_key_changes_when_blocked_phrases_change():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    image = Image.new("RGB", (4, 4), color="white")

    key_plain = deployment._build_cache_key(
        image=image,
        prompt="Convert this page into clean Markdown.",
        max_new_tokens=960,
        repetition_penalty=1.0,
        blocked_phrases=(),
        max_image_pixels=589_824,
        profile="speed",
        allow_escalation=False,
        escalation_max_new_tokens=None,
        escalation_max_image_pixels=None,
    )
    key_blocked = deployment._build_cache_key(
        image=image,
        prompt="Convert this page into clean Markdown.",
        max_new_tokens=960,
        repetition_penalty=1.0,
        blocked_phrases=("![]()",),
        max_image_pixels=589_824,
        profile="speed",
        allow_escalation=False,
        escalation_max_new_tokens=None,
        escalation_max_image_pixels=None,
    )

    assert key_plain is not None
    assert key_blocked is not None
    assert key_plain != key_blocked


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("profile", "expected_max_image_pixels"),
    [
        ("speed", 589_824),
        ("balanced", 1_048_576),
        ("quality", 2_097_152),
    ],
)
async def test_transcribe_uses_profile_image_pixel_defaults(profile, expected_max_image_pixels):
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    seen = []

    class _FakeBatcher:
        async def submit(self, request):
            seen.append(request)
            return "ok"

    deployment._batcher = _FakeBatcher()

    result = await deployment.transcribe(
        image=Image.new("RGB", (4, 4), color="white"),
        profile=profile,
        cache_bypass=True,
    )

    assert result == "ok"
    assert len(seen) == 1
    assert seen[0].max_image_pixels == expected_max_image_pixels


def test_digest_image_input_uses_raw_pixels_and_is_stable():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    image_a = Image.new("RGB", (8, 8), color="white")
    image_b = Image.new("RGB", (8, 8), color="white")
    image_c = Image.new("RGB", (8, 8), color="black")

    digest_a = deployment._digest_image_input(image_a)
    digest_b = deployment._digest_image_input(image_b)
    digest_c = deployment._digest_image_input(image_c)

    assert digest_a is not None
    assert digest_a == digest_b
    assert digest_a != digest_c


def test_image_to_data_url_prefers_payload_png_bytes():
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
    )
    image = Image.new("RGB", (4, 4), color="white")
    payload = ChandraImagePayload(image=image, png_bytes=b"png-bytes-for-test")

    data_url = deployment._image_to_data_url(payload)

    assert data_url == "data:image/png;base64,cG5nLWJ5dGVzLWZvci10ZXN0"


def test_vllm_server_image_content_prefers_local_file_path_when_allowed(tmp_path):
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
        vllm_server_allowed_local_media_path=str(tmp_path),
    )
    image_path = tmp_path / "rendered.png"
    image_path.write_bytes(b"png-bytes-for-test")
    payload = ChandraImagePayload(
        image=Image.new("RGB", (4, 4), color="white"),
        png_bytes=b"png-bytes-for-test",
        file_path=str(image_path),
        media_uuid="media-uuid-123",
    )

    content = deployment._build_vllm_server_image_content(payload)

    assert content["type"] == "image_url"
    assert content["image_url"]["url"] == str(image_path.resolve())
    assert content["uuid"] == "media-uuid-123"


def test_vllm_server_image_content_falls_back_to_data_url_when_path_not_allowed(tmp_path):
    deployment = _ChandraImpl(
        model_path="models/chandra",
        runtime_backend="vllm_server",
        vllm_server_probe_on_init=False,
        vllm_server_fallback_to_hf_on_error=False,
        vllm_server_allowed_local_media_path=str(tmp_path / "allowed"),
    )
    image_path = tmp_path / "rendered.png"
    image_path.write_bytes(b"png-bytes-for-test")
    payload = ChandraImagePayload(
        image=Image.new("RGB", (4, 4), color="white"),
        png_bytes=b"png-bytes-for-test",
        file_path=str(image_path),
        media_uuid="media-uuid-123",
    )

    content = deployment._build_vllm_server_image_content(payload)

    assert content["type"] == "image_url"
    assert content["image_url"]["url"] == "data:image/png;base64,cG5nLWJ5dGVzLWZvci10ZXN0"
    assert content["uuid"] == "media-uuid-123"
