import start_querylake


class DummyRef:
    pass


class DummyController:
    def __init__(self):
        self.calls = []
        self.graceful_shutdown = self
    def remote(self):
        self.calls.append('remote')
        return DummyRef()


class DummyClient:
    def __init__(self):
        self.controller = DummyController()
        self._controller = self.controller
        self.handles_shutdown = 0
    def shutdown_cached_handles(self):
        self.handles_shutdown += 1


class DummyApi:
    def __init__(self, client):
        self.client = client
        self.set_calls = []
    def _get_global_client(self, **kwargs):
        return self.client
    def _set_global_client(self, value):
        self.set_calls.append(value)


def test_shutdown_serve_best_effort_success(monkeypatch):
    client = DummyClient()
    api = DummyApi(client)

    monkeypatch.setitem(__import__('sys').modules, 'ray.serve._private.api', api)
    monkeypatch.setattr(start_querylake.ray, 'get', lambda ref, timeout=None: None)

    infos = []
    warns = []
    monkeypatch.setattr(start_querylake.logger, 'info', lambda *args, **kwargs: infos.append(args[0] % args[1:] if args[1:] else args[0]))
    monkeypatch.setattr(start_querylake.logger, 'warning', lambda *args, **kwargs: warns.append(args[0] % args[1:] if args[1:] else args[0]))

    start_querylake.shutdown_serve_best_effort(timeout_s=1.0)

    assert client.handles_shutdown == 1
    assert client.controller.calls == ['remote']
    assert api.set_calls == [None]
    assert any('Serve controller shutdown complete.' in msg for msg in infos)
    assert not warns


def test_shutdown_serve_best_effort_timeout(monkeypatch):
    client = DummyClient()
    api = DummyApi(client)

    monkeypatch.setitem(__import__('sys').modules, 'ray.serve._private.api', api)

    def raise_timeout(ref, timeout=None):
        raise TimeoutError()

    monkeypatch.setattr(start_querylake.ray, 'get', raise_timeout)

    warns = []
    monkeypatch.setattr(start_querylake.logger, 'info', lambda *args, **kwargs: None)
    monkeypatch.setattr(start_querylake.logger, 'warning', lambda *args, **kwargs: warns.append(args[0] % args[1:] if args[1:] else args[0]))

    start_querylake.shutdown_serve_best_effort(timeout_s=1.0)

    assert client.handles_shutdown == 1
    assert api.set_calls == [None]
    assert any('Serve controller did not shut down within 1.0s' in msg for msg in warns)
