import subprocess
import sys
from pathlib import Path


def test_operator_provenance_script_requires_document_or_chunk_target():
    root = Path(__file__).resolve().parent.parent
    proc = subprocess.run(
        [sys.executable, str(root / "scripts" / "document_decomposition_operator_provenance.py"), "--json"],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.returncode != 0
    assert "one of the arguments --document-id --chunk-id is required" in proc.stderr
