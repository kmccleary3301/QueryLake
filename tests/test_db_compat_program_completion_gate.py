from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.db_compat_program_completion_gate import main


def test_db_compat_program_completion_gate_emits_complete_payload(tmp_path):
    output_path = tmp_path / "db_compat_program_completion_gate.json"
    assert main(["--output", str(output_path)]) == 0
    payload = output_path.read_text(encoding="utf-8")
    assert '"program_complete": true' in payload
    assert '"paradedb_postgres_gold_v1"' in payload
    assert '"postgres_pgvector_light_v1"' in payload
    assert '"aws_aurora_pg_opensearch_v1"' in payload
    assert '"future_scope_required_for_completion": false' in payload
