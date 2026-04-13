from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.startup_networking import compute_ray_worker_port_plan


def test_compute_ray_worker_port_plan_widens_and_avoids_ephemeral(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.startup_networking.linux_ephemeral_port_range",
        lambda: (32768, 60999),
    )
    plan = compute_ray_worker_port_plan(
        head_port=6394,
        dashboard_port=8269,
        worker_port_base=32000,
        worker_port_step=80,
        gpu_count=4,
    )
    assert plan["step"] >= 512
    head_min, head_max = plan["head_range"]
    assert head_max < 32768
    for min_port, max_port in plan["worker_ranges"]:
        assert max_port < 32768
        assert min_port > head_max


def test_compute_ray_worker_port_plan_avoids_reserved_ports(monkeypatch):
    monkeypatch.setattr(
        "QueryLake.runtime.startup_networking.linux_ephemeral_port_range",
        lambda: (32768, 60999),
    )
    plan = compute_ray_worker_port_plan(
        head_port=10090,
        dashboard_port=10100,
        worker_port_base=10090,
        worker_port_step=512,
        gpu_count=1,
    )
    head_min, head_max = plan["head_range"]
    assert not (head_min <= 10090 <= head_max)
    assert not (head_min <= 10100 <= head_max)
