from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from QueryLake.scanning.persistence import write_scanner_envelope


ROOT = Path(__file__).resolve().parents[1]


def test_scanner_envelope_summary_script_reads_local_cas(tmp_path):
    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = materialize_legacy_markdown_envelope(
        run_id="summary_run",
        backend_id="chandra_1",
        backend_class="incumbent_continuity",
        support_tier="first_class",
        legacy_output_contract="ocr_markdown",
        markdown="summary text",
        meta={"engine": "chandra", "pages": 1, "page_source_by_page": {"0001": "ocr"}},
    )
    persisted = write_scanner_envelope(store, envelope)

    proc = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "scanner_envelope_summary.py"),
            "--store-dir",
            str(tmp_path / "cas"),
            "--cas",
            str(persisted.envelope_ref.storage_ref),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    summary = json.loads(proc.stdout)
    assert summary["run_id"] == "summary_run"
    assert summary["backend_id"] == "chandra_1"
    assert summary["legacy_output_contract"] == "ocr_markdown"
    assert summary["page_count"] == 1
