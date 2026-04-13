import start_querylake


class DummyProc:
    def __init__(self):
        self.calls = []
        self.pid = 12345
    def poll(self):
        self.calls.append('poll')
        return None
    def terminate(self):
        self.calls.append('terminate')
    def wait(self, timeout=None):
        self.calls.append(('wait', timeout))
        return 0


def test_shutdown_is_idempotent(monkeypatch):
    calls = []
    proc = DummyProc()
    cluster = start_querylake.RayGPUCluster.__new__(start_querylake.RayGPUCluster)
    cluster._shutdown_started = False
    cluster.cluster_ready = False
    cluster.worker_processes = [proc]
    cluster.head_process = None
    cluster._managed_chandra_vllm_servers = []
    cluster.maybe_stop_chandra_vllm_servers = lambda: calls.append('stop_chandra')

    monkeypatch.setattr(start_querylake.logger, 'info', lambda *args, **kwargs: None)
    monkeypatch.setattr(start_querylake.logger, 'warning', lambda *args, **kwargs: None)
    monkeypatch.setattr(start_querylake.logger, 'error', lambda *args, **kwargs: None)

    start_querylake.RayGPUCluster.shutdown(cluster)
    first_proc_calls = list(proc.calls)
    start_querylake.RayGPUCluster.shutdown(cluster)

    assert 'terminate' in first_proc_calls
    assert proc.calls == first_proc_calls
    assert calls == ['stop_chandra']
