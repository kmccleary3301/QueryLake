from scripts.ci_local_profile_support_sync import main


def test_local_profile_support_sync_script_passes():
    assert main() == 0
