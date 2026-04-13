#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from importlib import metadata as importlib_metadata


CURRENT_EXPECTED_MODEL_TYPE = "qwen3_vl"
CURRENT_EXPECTED_ARCHITECTURES = ["Qwen3VLForConditionalGeneration"]
TARGET_EXPECTED_MODEL_TYPE = "qwen3_5"
TARGET_EXPECTED_ARCHITECTURES = ["Qwen3_5ForConditionalGeneration"]


@dataclass(frozen=True)
class LaneStatus:
    name: str
    status: str
    blockers: List[str]
    observed: Dict[str, Any]
    expected: Dict[str, Any]


def _load_json(path: str) -> Dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_package_version(package_name: str) -> Optional[str]:
    try:
        return importlib_metadata.version(package_name)
    except Exception:
        return None


def _read_local_model_config(model_path: str) -> Optional[Dict[str, Any]]:
    if not model_path:
        return None
    model_config_path = Path(model_path).expanduser() / "config.json"
    if not model_config_path.exists():
        return None
    try:
        raw = json.loads(model_config_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _normalize_architectures(raw: Any) -> List[str]:
    if raw is None:
        return []
    if isinstance(raw, str):
        return [raw]
    if isinstance(raw, Sequence):
        return [str(item) for item in raw if str(item)]
    return [str(raw)]


def _evaluate_lane(
    name: str,
    model_config: Optional[Dict[str, Any]],
    expected_model_type: str,
    expected_architectures: Sequence[str],
) -> LaneStatus:
    observed_model_type = str((model_config or {}).get("model_type") or "")
    observed_architectures = _normalize_architectures((model_config or {}).get("architectures"))
    blockers: List[str] = []
    if not observed_model_type:
        blockers.append("missing_model_type")
    elif observed_model_type != expected_model_type:
        blockers.append(f"model_type_mismatch:{observed_model_type}->{expected_model_type}")

    if not observed_architectures:
        blockers.append("missing_architectures")
    else:
        expected_set = {str(item) for item in expected_architectures if str(item)}
        observed_set = set(observed_architectures)
        if expected_set and not expected_set.issubset(observed_set):
            blockers.append(
                "architectures_mismatch:" + ",".join(sorted(observed_set)) + "->" + ",".join(sorted(expected_set))
            )

    status = "ready" if not blockers else "blocked"
    return LaneStatus(
        name=name,
        status=status,
        blockers=blockers,
        observed={
            "model_type": observed_model_type or None,
            "architectures": observed_architectures,
        },
        expected={
            "model_type": expected_model_type,
            "architectures": list(expected_architectures),
        },
    )


def _runtime_snapshot_from_benchmark(benchmark: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not benchmark:
        return None
    runtime = benchmark.get("runtime") if isinstance(benchmark, dict) else None
    if not isinstance(runtime, dict):
        return None
    snapshot = runtime.get("compatibility_snapshot")
    return snapshot if isinstance(snapshot, dict) else None


def _runtime_alignment_status(snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if not snapshot:
        return {
            "status": "unknown",
            "blockers": [],
            "configured_runtime_backend": None,
            "effective_runtime_backend": None,
        }
    configured = str(snapshot.get("configured_runtime_backend") or "")
    effective = str(snapshot.get("effective_runtime_backend") or "")
    blockers: List[str] = []
    if not configured:
        blockers.append("missing_configured_runtime_backend")
    if not effective:
        blockers.append("missing_effective_runtime_backend")
    if configured and effective and configured != effective:
        blockers.append(f"runtime_backend_fallback:{configured}->{effective}")
    status = "ready" if not blockers else "degraded"
    return {
        "status": status,
        "blockers": blockers,
        "configured_runtime_backend": configured or None,
        "effective_runtime_backend": effective or None,
        "model_path": snapshot.get("model_path"),
        "model_config": snapshot.get("model_config"),
        "package_versions": snapshot.get("package_versions"),
        "profile_defaults": snapshot.get("profile_defaults"),
        "vllm_server": snapshot.get("vllm_server"),
        "runtime_state": snapshot.get("runtime_state"),
    }


def _run_probe(
    *,
    probe_script: str,
    model_path: str,
    probe_pdf: str,
    page: int,
    max_tokens: int,
    tensor_parallel_size: int,
    gpu_memory_utilization: float,
    max_num_seqs: int,
    max_model_len: Optional[int],
    dtype: str,
    trust_remote_code: bool,
    enforce_eager: bool,
    worker_timeout_seconds: int,
) -> Dict[str, Any]:
    cmd = [
        sys.executable,
        probe_script,
        "--model",
        model_path,
        "--pdf",
        probe_pdf,
        "--page",
        str(page),
        "--max-tokens",
        str(max_tokens),
        "--tensor-parallel-size",
        str(tensor_parallel_size),
        "--gpu-memory-utilization",
        str(gpu_memory_utilization),
        "--max-num-seqs",
        str(max_num_seqs),
        "--dtype",
        str(dtype),
        "--worker-timeout-seconds",
        str(worker_timeout_seconds),
    ]
    if max_model_len is not None:
        cmd.extend(["--max-model-len", str(max_model_len)])
    if trust_remote_code:
        cmd.append("--trust-remote-code")
    if enforce_eager:
        cmd.append("--enforce-eager")
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    parsed: Dict[str, Any]
    try:
        parsed = json.loads(proc.stdout)
    except Exception:
        parsed = {
            "status": "failed",
            "stage": "probe_wrapper",
            "error_type": "ProbeOutputParseError",
            "error_message": "Probe output was not valid JSON.",
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "returncode": proc.returncode,
        }
    parsed["_probe_returncode"] = proc.returncode
    return parsed


def build_report(
    *,
    current_model_path: str,
    target_model_path: Optional[str] = None,
    current_expected_model_type: str = CURRENT_EXPECTED_MODEL_TYPE,
    current_expected_architectures: Sequence[str] = CURRENT_EXPECTED_ARCHITECTURES,
    target_expected_model_type: str = TARGET_EXPECTED_MODEL_TYPE,
    target_expected_architectures: Sequence[str] = TARGET_EXPECTED_ARCHITECTURES,
    benchmark_json: Optional[Dict[str, Any]] = None,
    probe_script: Optional[str] = None,
    probe_pdf: Optional[str] = None,
    probe_page: int = 1,
    probe_max_tokens: int = 256,
    probe_tensor_parallel_size: int = 1,
    probe_gpu_memory_utilization: float = 0.85,
    probe_max_num_seqs: int = 8,
    probe_max_model_len: Optional[int] = 131072,
    probe_dtype: str = "auto",
    probe_trust_remote_code: bool = False,
    probe_enforce_eager: bool = False,
    probe_worker_timeout_seconds: int = 240,
) -> Dict[str, Any]:
    current_model_config = _read_local_model_config(current_model_path)
    resolved_target_model_path = target_model_path or current_model_path
    target_model_config = _read_local_model_config(resolved_target_model_path)
    current_lane = _evaluate_lane(
        "current",
        current_model_config,
        current_expected_model_type,
        current_expected_architectures,
    )
    target_lane = _evaluate_lane(
        "target",
        target_model_config,
        target_expected_model_type,
        target_expected_architectures,
    )
    runtime_snapshot = _runtime_snapshot_from_benchmark(benchmark_json)
    runtime_alignment = _runtime_alignment_status(runtime_snapshot)
    package_versions = {
        "torch": _safe_package_version("torch"),
        "transformers": _safe_package_version("transformers"),
        "vllm": _safe_package_version("vllm"),
        "ray": _safe_package_version("ray"),
        "pillow": _safe_package_version("Pillow"),
        "pypdfium2": _safe_package_version("pypdfium2"),
    }

    overall_status = "blocked" if target_lane.status != "ready" else current_lane.status
    blockers = list(target_lane.blockers)
    if runtime_alignment["status"] == "degraded":
        blockers.extend(runtime_alignment["blockers"])

    recommendation = {
        "current_lane": current_lane.status,
        "target_lane": target_lane.status,
        "action": (
            "stage a dedicated Chandra-2 runtime lane and keep the current lane as reference"
            if target_lane.status != "ready"
            else "current model family matches target; benchmark and retune the active lane"
        ),
        "next_step": (
            "runtime compatibility workstream"
            if target_lane.status != "ready"
            else "benchmark the target lane under the existing quality harness"
        ),
    }

    probes: Dict[str, Any] = {}
    if probe_script and probe_pdf:
        probes["current"] = _run_probe(
            probe_script=probe_script,
            model_path=current_model_path,
            probe_pdf=probe_pdf,
            page=probe_page,
            max_tokens=probe_max_tokens,
            tensor_parallel_size=probe_tensor_parallel_size,
            gpu_memory_utilization=probe_gpu_memory_utilization,
            max_num_seqs=probe_max_num_seqs,
            max_model_len=probe_max_model_len,
            dtype=probe_dtype,
            trust_remote_code=probe_trust_remote_code,
            enforce_eager=probe_enforce_eager,
            worker_timeout_seconds=probe_worker_timeout_seconds,
        )
        if resolved_target_model_path != current_model_path:
            probes["target"] = _run_probe(
                probe_script=probe_script,
                model_path=resolved_target_model_path,
                probe_pdf=probe_pdf,
                page=probe_page,
                max_tokens=probe_max_tokens,
                tensor_parallel_size=probe_tensor_parallel_size,
                gpu_memory_utilization=probe_gpu_memory_utilization,
                max_num_seqs=probe_max_num_seqs,
                max_model_len=probe_max_model_len,
                dtype=probe_dtype,
                trust_remote_code=probe_trust_remote_code,
                enforce_eager=probe_enforce_eager,
                worker_timeout_seconds=probe_worker_timeout_seconds,
            )

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "model_paths": {
            "current": current_model_path,
            "target": resolved_target_model_path,
        },
        "current_lane": {
            "status": current_lane.status,
            "blockers": current_lane.blockers,
            "observed": current_lane.observed,
            "expected": current_lane.expected,
            "model_path": current_model_path,
        },
        "target_lane": {
            "status": target_lane.status,
            "blockers": target_lane.blockers,
            "observed": target_lane.observed,
            "expected": target_lane.expected,
            "model_path": resolved_target_model_path,
        },
        "runtime": runtime_alignment,
        "package_versions": package_versions,
        "benchmark_runtime_snapshot_present": bool(runtime_snapshot),
        "probes": probes,
        "overall_status": overall_status,
        "blockers": blockers,
        "recommendation": recommendation,
        "target_expectations": {
            "model_type": target_expected_model_type,
            "architectures": list(target_expected_architectures),
        },
        "current_expectations": {
            "model_type": current_expected_model_type,
            "architectures": list(current_expected_architectures),
        },
    }


def _render_markdown(report: Dict[str, Any]) -> str:
    current_lane = report["current_lane"]
    target_lane = report["target_lane"]
    runtime = report["runtime"]
    package_versions = report["package_versions"]
    lines = [
        "# Chandra Runtime Compatibility Report",
        "",
        f"- Timestamp: `{report['timestamp']}`",
        f"- Current model path: `{report['model_paths']['current']}`",
        f"- Target model path: `{report['model_paths']['target']}`",
        f"- Overall status: `{report['overall_status']}`",
        f"- Current lane: `{current_lane['status']}`",
        f"- Target lane: `{target_lane['status']}`",
        f"- Runtime backend status: `{runtime['status']}`",
        f"- Probes captured: `{bool(report.get('probes'))}`",
        "",
        "## Current Lane",
        f"- Model path: `{current_lane['model_path']}`",
        f"- Expected model type: `{current_lane['expected']['model_type']}`",
        f"- Observed model type: `{current_lane['observed']['model_type']}`",
        f"- Expected architectures: `{', '.join(current_lane['expected']['architectures'])}`",
        f"- Observed architectures: `{', '.join(current_lane['observed']['architectures'])}`",
        f"- Blockers: `{', '.join(current_lane['blockers']) or 'none'}`",
        "",
        "## Target Lane",
        f"- Model path: `{target_lane['model_path']}`",
        f"- Expected model type: `{target_lane['expected']['model_type']}`",
        f"- Observed model type: `{target_lane['observed']['model_type']}`",
        f"- Expected architectures: `{', '.join(target_lane['expected']['architectures'])}`",
        f"- Observed architectures: `{', '.join(target_lane['observed']['architectures'])}`",
        f"- Blockers: `{', '.join(target_lane['blockers']) or 'none'}`",
        "",
        "## Runtime",
        f"- Configured backend: `{runtime.get('configured_runtime_backend')}`",
        f"- Effective backend: `{runtime.get('effective_runtime_backend')}`",
        f"- Runtime blockers: `{', '.join(runtime.get('blockers') or []) or 'none'}`",
        "",
        "## Package Versions",
    ]
    for name, version in package_versions.items():
        lines.append(f"- {name}: `{version}`")
    probes = report.get("probes") or {}
    if probes:
        lines.extend(
            [
                "",
                "## Probes",
            ]
        )
        for lane_name, probe in probes.items():
            lines.append(f"- {lane_name}: status=`{probe.get('status')}` stage=`{probe.get('stage')}` returncode=`{probe.get('_probe_returncode')}`")
    lines.extend(
        [
            "",
            "## Recommendation",
            f"- Action: {report['recommendation']['action']}",
            f"- Next step: {report['recommendation']['next_step']}",
        ]
    )
    return "\n".join(lines) + "\n"


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a machine-readable Chandra runtime compatibility report.")
    parser.add_argument("--current-model-path", default="models/chandra", help="Path to the current/reference Chandra model checkpoint.")
    parser.add_argument(
        "--target-model-path",
        default=None,
        help="Optional path to the target Chandra-2 checkpoint. Defaults to the current model path when omitted.",
    )
    parser.add_argument(
        "--current-expected-model-type",
        default=CURRENT_EXPECTED_MODEL_TYPE,
        help="Expected model_type for the current lane.",
    )
    parser.add_argument(
        "--current-expected-architectures",
        nargs="+",
        default=list(CURRENT_EXPECTED_ARCHITECTURES),
        help="Expected architectures for the current lane.",
    )
    parser.add_argument(
        "--target-expected-model-type",
        default=TARGET_EXPECTED_MODEL_TYPE,
        help="Expected model_type for the target Chandra-2 lane.",
    )
    parser.add_argument(
        "--target-expected-architectures",
        nargs="+",
        default=list(TARGET_EXPECTED_ARCHITECTURES),
        help="Expected architectures for the target Chandra-2 lane.",
    )
    parser.add_argument(
        "--benchmark-json",
        default=None,
        help="Optional benchmark JSON that already embeds a compatibility snapshot.",
    )
    parser.add_argument("--probe-script", default="scripts/chandra_vllm_probe.py", help="Path to the vLLM probe script.")
    parser.add_argument("--probe-pdf", default=None, help="Optional PDF path to probe each lane with.")
    parser.add_argument("--probe-page", type=int, default=1)
    parser.add_argument("--probe-max-tokens", type=int, default=256)
    parser.add_argument("--probe-tensor-parallel-size", type=int, default=1)
    parser.add_argument("--probe-gpu-memory-utilization", type=float, default=0.85)
    parser.add_argument("--probe-max-num-seqs", type=int, default=8)
    parser.add_argument("--probe-max-model-len", type=int, default=131072)
    parser.add_argument("--probe-dtype", default="auto")
    parser.add_argument("--probe-trust-remote-code", action="store_true")
    parser.add_argument("--probe-enforce-eager", action="store_true")
    parser.add_argument("--probe-worker-timeout-seconds", type=int, default=240)
    parser.add_argument("--out-json", default=None, help="Write the report JSON to this path.")
    parser.add_argument("--out-md", default=None, help="Write the report Markdown to this path.")
    return parser


def main() -> None:
    parser = _build_arg_parser()
    args = parser.parse_args()
    benchmark_json = _load_json(args.benchmark_json) if args.benchmark_json else None
    report = build_report(
        current_model_path=args.current_model_path,
        target_model_path=args.target_model_path,
        current_expected_model_type=args.current_expected_model_type,
        current_expected_architectures=args.current_expected_architectures,
        target_expected_model_type=args.target_expected_model_type,
        target_expected_architectures=args.target_expected_architectures,
        benchmark_json=benchmark_json,
        probe_script=args.probe_script,
        probe_pdf=args.probe_pdf,
        probe_page=args.probe_page,
        probe_max_tokens=args.probe_max_tokens,
        probe_tensor_parallel_size=args.probe_tensor_parallel_size,
        probe_gpu_memory_utilization=args.probe_gpu_memory_utilization,
        probe_max_num_seqs=args.probe_max_num_seqs,
        probe_max_model_len=args.probe_max_model_len,
        probe_dtype=args.probe_dtype,
        probe_trust_remote_code=args.probe_trust_remote_code,
        probe_enforce_eager=args.probe_enforce_eager,
        probe_worker_timeout_seconds=args.probe_worker_timeout_seconds,
    )
    rendered_json = json.dumps(report, indent=2, sort_keys=True)
    print(rendered_json)
    if args.out_json:
        out_json = Path(args.out_json)
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(rendered_json + "\n", encoding="utf-8")
    if args.out_md:
        out_md = Path(args.out_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(_render_markdown(report), encoding="utf-8")


if __name__ == "__main__":
    main()
