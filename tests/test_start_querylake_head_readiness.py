import start_querylake


def test_wait_for_head_cluster_registration_succeeds(monkeypatch):
    state = {"initialized": False}
    init_calls = []
    shutdown_calls = []

    def fake_is_initialized():
        return state["initialized"]

    def fake_init(**kwargs):
        init_calls.append(kwargs)
        state["initialized"] = True

    def fake_shutdown():
        shutdown_calls.append(True)
        state["initialized"] = False

    monkeypatch.setattr(start_querylake.ray, "is_initialized", fake_is_initialized)
    monkeypatch.setattr(start_querylake.ray, "init", fake_init)
    monkeypatch.setattr(start_querylake.ray, "shutdown", fake_shutdown)
    monkeypatch.setattr(start_querylake.ray, "cluster_resources", lambda: {"node:__internal_head__": 1.0})
    monkeypatch.setattr(start_querylake.ray, "nodes", lambda: [{"alive": True}])
    monkeypatch.setattr(start_querylake.time, "sleep", lambda *_args, **_kwargs: None)

    assert start_querylake.wait_for_head_cluster_registration("127.0.0.1:6394", timeout_s=1.0)
    assert len(init_calls) == 1
    assert len(shutdown_calls) == 1


def test_wait_for_head_cluster_registration_times_out_without_head_resource(monkeypatch):
    state = {"initialized": False, "now": 0.0}

    def fake_is_initialized():
        return state["initialized"]

    def fake_init(**kwargs):
        state["initialized"] = True

    def fake_shutdown():
        state["initialized"] = False

    def fake_time():
        state["now"] += 0.6
        return state["now"]

    monkeypatch.setattr(start_querylake.ray, "is_initialized", fake_is_initialized)
    monkeypatch.setattr(start_querylake.ray, "init", fake_init)
    monkeypatch.setattr(start_querylake.ray, "shutdown", fake_shutdown)
    monkeypatch.setattr(start_querylake.ray, "cluster_resources", lambda: {})
    monkeypatch.setattr(start_querylake.ray, "nodes", lambda: [{"alive": True}])
    monkeypatch.setattr(start_querylake.time, "sleep", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(start_querylake.time, "time", fake_time)

    assert not start_querylake.wait_for_head_cluster_registration("127.0.0.1:6394", timeout_s=1.0)
