import json

from scripts.db_compat_local_dense_sidecar_lifecycle_smoke import main


def test_local_dense_sidecar_lifecycle_smoke_passes(capsys):
    assert main(["--enable-ready-profile-projections"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["gate_ok"] is True
    transition = dict(payload["dense_sidecar_lifecycle_transition"])
    assert transition["before"]["lifecycle_state"] == "ready_projection_backed_cache_cold"
    assert transition["after"]["lifecycle_state"] == "ready_cache_warmed"
