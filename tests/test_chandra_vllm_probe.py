from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chandra_vllm_probe import _run_generate_probe


class _FakeOutput:
    def __init__(self, text: str) -> None:
        self.outputs = [type("_Generated", (), {"text": text})()]


class _FakeLLM:
    def __init__(self) -> None:
        self.calls = []

    def chat(self, messages, sampling_params):
        image_part = messages[0]["content"][1]
        self.calls.append(image_part["type"])
        if image_part["type"] == "image_pil":
            return [_FakeOutput("ok")]
        raise NotImplementedError("Unknown part type: image")


def test_run_generate_probe_prefers_image_pil_first():
    llm = _FakeLLM()

    result = _run_generate_probe(
        llm=llm,
        image=object(),
        prompt="Convert this page into clean Markdown.",
        max_tokens=64,
    )

    assert result["text"] == "ok"
    assert llm.calls == ["image_pil"]
