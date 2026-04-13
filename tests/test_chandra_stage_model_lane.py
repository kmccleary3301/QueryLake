import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts import chandra_stage_model_lane as stage_script


def _write_complete_single_snapshot(snapshot_path: Path, *, model_type: str, architecture: str) -> None:
    snapshot_path.mkdir(parents=True, exist_ok=True)
    (snapshot_path / "config.json").write_text(
        json.dumps(
            {
                "model_type": model_type,
                "architectures": [architecture],
                "transformers_version": "4.57.1",
            }
        ),
        encoding="utf-8",
    )
    for name in (
        "tokenizer.json",
        "tokenizer_config.json",
        "preprocessor_config.json",
        "model.safetensors",
    ):
        (snapshot_path / name).write_text("x", encoding="utf-8")


def test_inspect_snapshot_reports_complete_single_file_snapshot(tmp_path: Path):
    snapshot = tmp_path / "snapshot"
    _write_complete_single_snapshot(
        snapshot,
        model_type="qwen3_5",
        architecture="Qwen3_5ForConditionalGeneration",
    )

    report = stage_script.inspect_snapshot(str(snapshot))

    assert report["exists"] is True
    assert report["complete"] is True
    assert report["weight_mode"] == "single"
    assert report["config"]["model_type"] == "qwen3_5"


def test_stage_lane_symlinks_to_downloaded_snapshot(tmp_path: Path, monkeypatch):
    snapshot = tmp_path / "hf-cache" / "snapshot"
    _write_complete_single_snapshot(
        snapshot,
        model_type="qwen3_5",
        architecture="Qwen3_5ForConditionalGeneration",
    )
    monkeypatch.setattr(stage_script, "snapshot_download", lambda **kwargs: str(snapshot))

    lane = tmp_path / "models" / "chandra2"
    result = stage_script.stage_lane(
        repo_id="datalab-to/chandra-ocr-2",
        lane_path=str(lane),
    )

    assert lane.is_symlink()
    assert lane.resolve() == snapshot.resolve()
    assert result["status"] == "staged"
    assert Path(result["manifest_path"]).exists()


def test_stage_lane_reuses_existing_matching_symlink(tmp_path: Path, monkeypatch):
    snapshot = tmp_path / "hf-cache" / "snapshot"
    _write_complete_single_snapshot(
        snapshot,
        model_type="qwen3_5",
        architecture="Qwen3_5ForConditionalGeneration",
    )
    monkeypatch.setattr(stage_script, "snapshot_download", lambda **kwargs: str(snapshot))

    lane = tmp_path / "models" / "chandra2"
    lane.parent.mkdir(parents=True, exist_ok=True)
    lane.symlink_to(snapshot)

    result = stage_script.stage_lane(
        repo_id="datalab-to/chandra-ocr-2",
        lane_path=str(lane),
    )

    assert result["status"] == "already_staged"
    assert lane.resolve() == snapshot.resolve()
