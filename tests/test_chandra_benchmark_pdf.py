import asyncio
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from PIL import Image

from scripts.chandra_benchmark_pdf import (
    _identify_sparse_feature_indices,
    _normalize_triage_classes,
    _run_document_shape_pass,
    _run_pass,
    _run_sparse_feature_pass,
    _run_tapered_feature_pass,
    _run_subset_pass,
    _run_triaged_pass,
    _resolve_tapered_page_max_image_pixels,
    _summarize_page_complexities,
)


class _BatchRuntime:
    def __init__(self) -> None:
        self.calls = []

    async def transcribe_many(self, images, prompt, max_new_tokens, max_image_pixels, blocked_phrases, profile):
        self.calls.append(
            {
                "kind": "many",
                "images": list(images),
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "max_image_pixels": max_image_pixels,
                "blocked_phrases": list(blocked_phrases or []),
                "profile": profile,
            }
        )
        await asyncio.sleep(0)
        return [f"{prompt}:{idx}" for idx, _ in enumerate(images)]

    async def transcribe(self, image, prompt, max_new_tokens, max_image_pixels, blocked_phrases, profile):
        self.calls.append(
            {
                "kind": "one",
                "image": image,
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "max_image_pixels": max_image_pixels,
                "blocked_phrases": list(blocked_phrases or []),
                "profile": profile,
            }
        )
        await asyncio.sleep(0)
        return f"{prompt}:{image}"


class _SparseRuntime(_BatchRuntime):
    async def transcribe(self, image, prompt, max_new_tokens, max_image_pixels, blocked_phrases, profile):
        self.calls.append(
            {
                "kind": "one",
                "image": image,
                "prompt": prompt,
                "max_new_tokens": max_new_tokens,
                "max_image_pixels": max_image_pixels,
                "blocked_phrases": list(blocked_phrases or []),
                "profile": profile,
            }
        )
        await asyncio.sleep(0)
        if image == "page-2" and max_image_pixels == 393216:
            return "tiny"
        return f"{prompt}:{image}:{max_image_pixels}"


@pytest.mark.asyncio
async def test_run_pass_uses_batched_transport_when_enabled():
    runtime = _BatchRuntime()
    stats = await _run_pass(
        runtime=runtime,
        images=["page-1", "page-2", "page-3"],
        prompt="hello",
        max_new_tokens=128,
        max_image_pixels=256,
        blocked_phrases=["![]()"],
        concurrency=8,
        name="cold",
        profile="balanced",
        use_transcribe_many=True,
    )

    assert stats.outputs == ["hello:0", "hello:1", "hello:2"]
    assert len(runtime.calls) == 1
    assert runtime.calls[0]["kind"] == "many"
    assert runtime.calls[0]["images"] == ["page-1", "page-2", "page-3"]
    assert runtime.calls[0]["blocked_phrases"] == ["![]()"]
    assert stats.metadata == {
        "transport_mode": "batch",
        "latency_semantics": "collective_wall_for_entire_batch",
    }


@pytest.mark.asyncio
async def test_run_subset_pass_uses_batched_transport_when_enabled():
    runtime = _BatchRuntime()
    wall_seconds, latencies, outputs = await _run_subset_pass(
        runtime=runtime,
        images=["page-1", "page-2", "page-3"],
        indices=[0, 2],
        prompt="rerun",
        max_new_tokens=256,
        max_image_pixels=512,
        blocked_phrases=["| --- | --- | --- |"],
        concurrency=8,
        profile="quality",
        use_transcribe_many=True,
    )

    assert wall_seconds >= 0.0
    assert outputs == {0: "rerun:0", 2: "rerun:1"}
    assert set(latencies.keys()) == {0, 2}
    assert len(runtime.calls) == 1
    assert runtime.calls[0]["kind"] == "many"
    assert runtime.calls[0]["images"] == ["page-1", "page-3"]
    assert runtime.calls[0]["blocked_phrases"] == ["| --- | --- | --- |"]


def test_summarize_page_complexities_emits_counts_and_page_rows():
    images = [
        Image.new("RGB", (200, 240), "white"),
        Image.new("RGB", (200, 240), "white"),
    ]

    summary = _summarize_page_complexities(images)

    assert summary["counts"]["simple"] + summary["counts"]["mixed"] + summary["counts"]["complex"] == 2
    assert len(summary["pages"]) == 2
    assert summary["pages"][0]["page_index"] == 1
    assert "class" in summary["pages"][0]


@pytest.mark.asyncio
async def test_run_triaged_pass_routes_simple_pages_to_lower_cap():
    runtime = _BatchRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "class": "simple"},
            {"page_index": 2, "class": "complex"},
            {"page_index": 3, "class": "mixed"},
        ]
    }

    stats = await _run_triaged_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        lowered_max_image_pixels=393216,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        profile="speed",
        use_transcribe_many=True,
        lowered_page_classes=["simple"],
    )

    assert len(runtime.calls) == 2
    assert runtime.calls[0]["max_image_pixels"] == 589824
    assert runtime.calls[1]["max_image_pixels"] == 393216
    assert stats.metadata["triage_mode"] == "page_class_lower_cap_v2"
    assert stats.metadata["lowered_page_count"] == 1
    assert stats.outputs == ["triage:page-1", "triage:0", "triage:1"]


@pytest.mark.asyncio
async def test_run_triaged_pass_can_route_mixed_pages_to_lower_cap():
    runtime = _BatchRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "class": "simple"},
            {"page_index": 2, "class": "complex"},
            {"page_index": 3, "class": "mixed"},
        ]
    }

    stats = await _run_triaged_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        lowered_max_image_pixels=393216,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        profile="speed",
        use_transcribe_many=True,
        lowered_page_classes=["simple", "mixed"],
    )

    assert len(runtime.calls) == 2
    assert runtime.calls[0]["kind"] == "one"
    assert runtime.calls[0]["image"] == "page-2"
    assert runtime.calls[0]["max_image_pixels"] == 589824
    assert runtime.calls[1]["kind"] == "many"
    assert runtime.calls[1]["images"] == ["page-1", "page-3"]
    assert runtime.calls[1]["max_image_pixels"] == 393216
    assert stats.metadata["lowered_page_classes"] == ["simple", "mixed"]
    assert stats.metadata["lowered_page_count"] == 2
    assert stats.outputs == ["triage:0", "triage:page-2", "triage:1"]


@pytest.mark.asyncio
async def test_run_triaged_pass_uses_concurrent_per_page_caps_in_page_mode():
    runtime = _BatchRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "class": "simple"},
            {"page_index": 2, "class": "complex"},
            {"page_index": 3, "class": "mixed"},
        ]
    }

    stats = await _run_triaged_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        lowered_max_image_pixels=393216,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        profile="speed",
        use_transcribe_many=False,
        lowered_page_classes=["simple", "mixed"],
    )

    assert [call["kind"] for call in runtime.calls] == ["one", "one", "one"]
    caps = {call["image"]: call["max_image_pixels"] for call in runtime.calls}
    assert caps == {"page-1": 393216, "page-2": 589824, "page-3": 393216}
    assert stats.metadata["transport_mode"] == "page"
    assert stats.metadata["latency_semantics"] == "per_page_concurrent_requests_with_per_page_cap"


def test_normalize_triage_classes_defaults_and_validates():
    assert _normalize_triage_classes(None) == ["simple"]
    assert _normalize_triage_classes("simple,mixed,simple") == ["simple", "mixed"]
    with pytest.raises(ValueError):
        _normalize_triage_classes("simple,unknown")


def test_identify_sparse_feature_indices_uses_measured_page_metrics():
    page_complexity = {
        "pages": [
            {"page_index": 1, "near_white_fraction": 0.55, "ink_fraction": 0.20, "edge_density": 0.15, "variance": 800.0},
            {"page_index": 2, "near_white_fraction": 0.82, "ink_fraction": 0.010, "edge_density": 0.021, "variance": 58.0},
            {"page_index": 3, "near_white_fraction": 0.78, "ink_fraction": 0.012, "edge_density": 0.022, "variance": 60.0},
        ]
    }
    indices = _identify_sparse_feature_indices(
        page_complexity,
        near_white_threshold=0.74,
        ink_threshold=0.02,
        edge_threshold=0.03,
        variance_threshold=120.0,
    )
    assert indices == [1, 2]


@pytest.mark.asyncio
async def test_run_sparse_feature_pass_can_rerun_only_suspect_sparse_pages():
    runtime = _SparseRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "near_white_fraction": 0.50, "ink_fraction": 0.20, "edge_density": 0.14, "variance": 600.0},
            {"page_index": 2, "near_white_fraction": 0.80, "ink_fraction": 0.010, "edge_density": 0.020, "variance": 55.0},
            {"page_index": 3, "near_white_fraction": 0.79, "ink_fraction": 0.011, "edge_density": 0.022, "variance": 58.0},
        ]
    }

    stats = await _run_sparse_feature_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        lowered_max_image_pixels=393216,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        near_white_threshold=0.74,
        ink_threshold=0.02,
        edge_threshold=0.03,
        variance_threshold=120.0,
        rerun_suspect_pages=True,
        rerun_min_chars=10,
        profile="speed",
        use_transcribe_many=False,
    )

    assert stats.metadata["triage_mode"] == "sparse_feature_lower_cap_v1"
    assert stats.metadata["sparse_page_count"] == 2
    assert stats.metadata["sparse_page_indices"] == [2, 3]
    assert stats.metadata["rerun_page_count"] == 1
    assert stats.metadata["rerun_page_indices"] == [2]
    lowered_calls = [call for call in runtime.calls if call["max_image_pixels"] == 393216]
    default_calls = [call for call in runtime.calls if call["max_image_pixels"] == 589824]
    assert len(lowered_calls) == 2
    assert len(default_calls) == 2  # page-1 default + page-2 rerun
    assert stats.outputs[1] == "triage:page-2:589824"


@pytest.mark.asyncio
async def test_run_document_shape_pass_can_lower_whole_doc_and_rerun_suspect_pages():
    runtime = _SparseRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "near_white_fraction": 0.80, "ink_fraction": 0.010, "edge_density": 0.020, "variance": 55.0},
            {"page_index": 2, "near_white_fraction": 0.79, "ink_fraction": 0.011, "edge_density": 0.022, "variance": 58.0},
            {"page_index": 3, "near_white_fraction": 0.20, "ink_fraction": 0.25, "edge_density": 0.12, "variance": 300.0},
        ]
    }

    stats = await _run_document_shape_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        lowered_max_image_pixels=393216,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        near_white_threshold=0.74,
        ink_threshold=0.02,
        edge_threshold=0.03,
        variance_threshold=120.0,
        min_sparse_ratio=0.5,
        rerun_suspect_pages=True,
        rerun_min_chars=10,
        profile="speed",
        use_transcribe_many=False,
    )

    assert stats.metadata["triage_mode"] == "document_shape_lower_cap_v1"
    assert stats.metadata["document_lowered_first_pass"] is True
    assert stats.metadata["sparse_page_count"] == 2
    assert stats.metadata["document_sparse_ratio"] == pytest.approx(2 / 3)
    assert stats.metadata["rerun_page_count"] == 1
    assert stats.metadata["rerun_page_indices"] == [2]
    lowered_calls = [call for call in runtime.calls if call["max_image_pixels"] == 393216]
    default_calls = [call for call in runtime.calls if call["max_image_pixels"] == 589824]
    assert len(lowered_calls) == 3
    assert len(default_calls) == 1
    assert stats.outputs[1] == "triage:page-2:589824"


def test_resolve_tapered_page_max_image_pixels_routes_sparse_pages_lower():
    page_complexity = {
        "pages": [
            {"page_index": 1, "near_white_fraction": 0.56, "ink_fraction": 0.18, "edge_density": 0.14, "variance": 620.0},
            {"page_index": 2, "near_white_fraction": 0.80, "ink_fraction": 0.010, "edge_density": 0.020, "variance": 55.0},
            {"page_index": 3, "near_white_fraction": 0.73, "ink_fraction": 0.040, "edge_density": 0.050, "variance": 180.0},
        ]
    }

    routed = _resolve_tapered_page_max_image_pixels(
        page_complexity,
        default_max_image_pixels=589824,
        min_max_image_pixels=327680,
        medium_max_image_pixels=458752,
    )

    assert routed[0] == 589824
    assert routed[1] == 327680
    assert routed[2] == 458752


@pytest.mark.asyncio
async def test_run_tapered_feature_pass_uses_per_page_caps():
    runtime = _BatchRuntime()
    images = ["page-1", "page-2", "page-3"]
    page_complexity = {
        "pages": [
            {"page_index": 1, "near_white_fraction": 0.56, "ink_fraction": 0.18, "edge_density": 0.14, "variance": 620.0},
            {"page_index": 2, "near_white_fraction": 0.80, "ink_fraction": 0.010, "edge_density": 0.020, "variance": 55.0},
            {"page_index": 3, "near_white_fraction": 0.73, "ink_fraction": 0.040, "edge_density": 0.050, "variance": 180.0},
        ]
    }

    stats = await _run_tapered_feature_pass(
        runtime=runtime,
        images=images,
        page_complexity=page_complexity,
        prompt="triage",
        max_new_tokens=128,
        default_max_image_pixels=589824,
        min_max_image_pixels=327680,
        medium_max_image_pixels=458752,
        blocked_phrases=[],
        concurrency=4,
        name="cold",
        profile="speed",
    )

    caps = {call["image"]: call["max_image_pixels"] for call in runtime.calls}
    assert caps == {"page-1": 589824, "page-2": 327680, "page-3": 458752}
    assert stats.metadata["triage_mode"] == "feature_tapered_cap_v1"
    assert stats.metadata["bucket_counts"] == {"589824": 1, "327680": 1, "458752": 1}
