from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.ci_db_compat_v2_runtime_boundary_sync import main


def test_v2_runtime_boundary_doc_matches_code():
    assert main() == 0
