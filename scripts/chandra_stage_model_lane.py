#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from huggingface_hub import snapshot_download


REQUIRED_COMMON_FILES = (
    "config.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "preprocessor_config.json",
)


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _snapshot_weight_mode(snapshot_path: Path) -> Optional[str]:
    if (snapshot_path / "model.safetensors").exists():
        return "single"
    index_path = snapshot_path / "model.safetensors.index.json"
    if not index_path.exists():
        return None
    index_payload = _read_json(index_path)
    weight_map = index_payload.get("weight_map") or {}
    if not isinstance(weight_map, dict) or not weight_map:
        return None
    expected_files = {str(name) for name in weight_map.values() if str(name)}
    missing = sorted(name for name in expected_files if not (snapshot_path / name).exists())
    if missing:
        raise RuntimeError(f"Incomplete model shard set in snapshot {snapshot_path}: missing {missing[:5]}")
    return "sharded"


def inspect_snapshot(snapshot_path: str) -> Dict[str, Any]:
    snapshot = Path(snapshot_path).expanduser().resolve()
    if not snapshot.exists():
        return {
            "exists": False,
            "complete": False,
            "snapshot_path": str(snapshot),
            "missing_files": list(REQUIRED_COMMON_FILES),
            "weight_mode": None,
        }
    missing = [name for name in REQUIRED_COMMON_FILES if not (snapshot / name).exists()]
    weight_mode = None
    complete = False
    if not missing:
        weight_mode = _snapshot_weight_mode(snapshot)
        complete = weight_mode is not None
    config = _read_json(snapshot / "config.json") if (snapshot / "config.json").exists() else {}
    return {
        "exists": True,
        "complete": complete,
        "snapshot_path": str(snapshot),
        "missing_files": missing,
        "weight_mode": weight_mode,
        "config": {
            "model_type": config.get("model_type"),
            "architectures": config.get("architectures"),
            "transformers_version": config.get("transformers_version"),
        },
    }


def _write_manifest(lane_path: Path, payload: Dict[str, Any]) -> Path:
    manifest_path = lane_path.parent / f".{lane_path.name}_lane_manifest.json"
    manifest_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest_path


def stage_lane(
    *,
    repo_id: str,
    lane_path: str,
    revision: Optional[str] = None,
    cache_dir: Optional[str] = None,
    force_relink: bool = False,
) -> Dict[str, Any]:
    snapshot_path = Path(
        snapshot_download(
            repo_id=repo_id,
            revision=revision,
            cache_dir=cache_dir,
        )
    ).resolve()
    inspection = inspect_snapshot(str(snapshot_path))
    if not inspection["complete"]:
        raise RuntimeError(f"Downloaded snapshot is not complete: {inspection}")

    lane = Path(lane_path).expanduser()
    lane.parent.mkdir(parents=True, exist_ok=True)
    if lane.exists() or lane.is_symlink():
        if lane.is_symlink():
            current_target = lane.resolve()
            if current_target == snapshot_path:
                manifest = {
                    "repo_id": repo_id,
                    "revision": revision,
                    "lane_path": str(lane),
                    "snapshot_path": str(snapshot_path),
                    "staged_at": datetime.now(timezone.utc).isoformat(),
                    "status": "already_staged",
                    "inspection": inspection,
                }
                manifest_path = _write_manifest(lane, manifest)
                manifest["manifest_path"] = str(manifest_path)
                return manifest
            if not force_relink:
                raise RuntimeError(f"Lane path already exists and points elsewhere: {lane} -> {current_target}")
            lane.unlink()
        else:
            raise RuntimeError(f"Lane path already exists and is not a symlink: {lane}")

    os.symlink(snapshot_path, lane)
    manifest = {
        "repo_id": repo_id,
        "revision": revision,
        "lane_path": str(lane),
        "snapshot_path": str(snapshot_path),
        "staged_at": datetime.now(timezone.utc).isoformat(),
        "status": "staged",
        "inspection": inspection,
    }
    manifest_path = _write_manifest(lane, manifest)
    manifest["manifest_path"] = str(manifest_path)
    return manifest


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Stage a local Chandra model lane from Hugging Face cache/snapshot.")
    parser.add_argument("--repo-id", default="datalab-to/chandra-ocr-2")
    parser.add_argument("--lane-path", default="models/chandra2")
    parser.add_argument("--revision", default=None)
    parser.add_argument("--cache-dir", default=None)
    parser.add_argument("--force-relink", action="store_true")
    parser.add_argument("--inspect-only", action="store_true")
    parser.add_argument("--snapshot-path", default=None, help="Inspect an existing snapshot path instead of downloading.")
    parser.add_argument("--out-json", default=None)
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    if args.inspect_only:
        if not args.snapshot_path:
            raise SystemExit("--snapshot-path is required with --inspect-only")
        result = inspect_snapshot(args.snapshot_path)
    else:
        result = stage_lane(
            repo_id=args.repo_id,
            lane_path=args.lane_path,
            revision=args.revision,
            cache_dir=args.cache_dir,
            force_relink=args.force_relink,
        )
    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.out_json:
        out_path = Path(args.out_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
