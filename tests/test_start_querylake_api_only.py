from types import SimpleNamespace

from start_querylake import ports_to_clean_for_default_mode


def test_ports_to_clean_skips_worker_ranges_in_api_only_mode():
    cluster_config = SimpleNamespace(head_port=6394, dashboard_port=8269)
    port_plan = {
        "head_range": (10090, 10101),
        "worker_ranges": [(10102, 10113), (10114, 10125)],
    }
    ports = ports_to_clean_for_default_mode(
        cluster_config=cluster_config,
        port_plan=port_plan,
        api_only=True,
        with_gpu_workers=False,
    )
    assert 6394 in ports
    assert 8269 in ports
    assert 10090 in ports and 10101 in ports
    assert 10102 not in ports
    assert 10125 not in ports


def test_ports_to_clean_keeps_worker_ranges_when_gpu_workers_enabled():
    cluster_config = SimpleNamespace(head_port=6394, dashboard_port=8269)
    port_plan = {
        "head_range": (10090, 10101),
        "worker_ranges": [(10102, 10113)],
    }
    ports = ports_to_clean_for_default_mode(
        cluster_config=cluster_config,
        port_plan=port_plan,
        api_only=True,
        with_gpu_workers=True,
    )
    assert 10102 in ports
    assert 10113 in ports
