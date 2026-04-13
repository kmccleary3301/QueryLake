from __future__ import annotations

import os
import socket
from typing import Dict, List, Tuple


SAFE_RAY_WORKER_PORT_STEP = 512
SAFE_RAY_WORKER_PORT_BASE = 10090


def preferred_ray_node_ip() -> str:
    override = (os.getenv("QUERYLAKE_RAY_NODE_IP") or "").strip()
    if override:
        return override
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            resolved = sock.getsockname()[0]
            if resolved:
                return resolved
    except OSError:
        pass
    try:
        hostname_ip = socket.gethostbyname(socket.gethostname())
        if hostname_ip and not hostname_ip.startswith("127."):
            return hostname_ip
    except OSError:
        pass
    return "127.0.0.1"


def linux_ephemeral_port_range() -> Tuple[int, int]:
    try:
        with open("/proc/sys/net/ipv4/ip_local_port_range", "r", encoding="utf-8") as handle:
            raw = handle.read().strip().split()
        if len(raw) == 2:
            start, end = int(raw[0]), int(raw[1])
            if 0 < start < end:
                return (start, end)
    except Exception:
        pass
    return (32768, 60999)


def compute_ray_worker_port_plan(
    *,
    head_port: int,
    dashboard_port: int,
    worker_port_base: int,
    worker_port_step: int,
    gpu_count: int,
) -> Dict[str, object]:
    step = max(int(worker_port_step), SAFE_RAY_WORKER_PORT_STEP)
    total_slots = max(int(gpu_count), 0) + 1
    ephemeral_start, ephemeral_end = linux_ephemeral_port_range()
    reserved = {int(head_port), int(dashboard_port)}

    def _range_overlaps_reserved(candidate_base: int) -> bool:
        candidate_end = candidate_base + step * total_slots - 1
        return any(candidate_base <= port <= candidate_end for port in reserved)

    max_base_below_ephemeral = ephemeral_start - (step * total_slots) - 32
    preferred_base = max(int(worker_port_base), SAFE_RAY_WORKER_PORT_BASE)

    if max_base_below_ephemeral >= SAFE_RAY_WORKER_PORT_BASE:
        search_start = min(preferred_base, max_base_below_ephemeral)
        candidate = search_start
        while candidate <= max_base_below_ephemeral:
            if not _range_overlaps_reserved(candidate):
                base = candidate
                break
            candidate += step
        else:
            candidate = SAFE_RAY_WORKER_PORT_BASE
            base = candidate
            while candidate <= max_base_below_ephemeral:
                if not _range_overlaps_reserved(candidate):
                    base = candidate
                    break
                candidate += step
    else:
        base = max(preferred_base, ephemeral_end + 1024)
        while _range_overlaps_reserved(base):
            base += step

    head_range = (base, base + step - 1)
    worker_ranges: List[Tuple[int, int]] = []
    for index in range(max(int(gpu_count), 0)):
        min_port = base + ((index + 1) * step)
        worker_ranges.append((min_port, min_port + step - 1))
    return {
        "base": base,
        "step": step,
        "head_range": head_range,
        "worker_ranges": worker_ranges,
        "ephemeral_range": (ephemeral_start, ephemeral_end),
    }
