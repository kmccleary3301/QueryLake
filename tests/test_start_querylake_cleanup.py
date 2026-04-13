from types import SimpleNamespace

import start_querylake


class DummyResult:
    def __init__(self, returncode=0, stdout='', stderr=''):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_listening_pids_by_port_parses_lsof_machine_output(monkeypatch):
    def fake_run(*args, **kwargs):
        return DummyResult(
            returncode=0,
            stdout='p123\nnTCP *:6394 (LISTEN)\np456\nnTCP 127.0.0.1:8269 (LISTEN)\np789\nnTCP *:9999 (LISTEN)\n',
        )

    monkeypatch.setattr(start_querylake.subprocess, 'run', fake_run)
    assert start_querylake.listening_pids_by_port([6394, 8269, 10090]) == {
        6394: ['123'],
        8269: ['456'],
    }


def test_cleanup_ports_uses_bulk_kill(monkeypatch):
    calls = []

    def fake_listening(ports):
        calls.append(('listening', tuple(ports)))
        return {6394: ['111'], 8269: ['111', '222']}

    def fake_run(cmd, **kwargs):
        calls.append(('run', tuple(cmd)))
        return DummyResult(returncode=0, stdout='', stderr='')

    monkeypatch.setattr(start_querylake, 'listening_pids_by_port', fake_listening)
    monkeypatch.setattr(start_querylake.subprocess, 'run', fake_run)
    monkeypatch.setattr(start_querylake.time, 'sleep', lambda *_args, **_kwargs: None)

    cluster = SimpleNamespace()
    start_querylake.RayGPUCluster.cleanup_ports(cluster, [6394, 8269, 6394])

    assert calls[0] == ('listening', (6394, 8269))
    assert calls[1] == ('run', ('kill', '-9', '111', '222'))
