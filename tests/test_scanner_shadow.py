from __future__ import annotations

import json

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.scanning.adapters import ScannerRunContext
from QueryLake.scanning.shadow import MinerUShadowAdapter, ShadowParserResult


def test_mineru_shadow_availability_is_lazy_and_optional():
    availability = MinerUShadowAdapter().check_available()

    assert availability.backend_id == "mineru_shadow"
    if availability.available:
        assert availability.reason == "available"
    else:
        assert availability.reason == "missing_optional_dependency:mineru"
        assert availability.md["shadow_only"] is True


def test_mineru_shadow_mapping_cannot_emit_chunk_compat_or_selected_route(tmp_path):
    adapter = MinerUShadowAdapter(
        result=ShadowParserResult(
            markdown="Shadow markdown only",
            raw_payload={"blocks": [{"text": "Shadow markdown only"}]},
            page_count=1,
            backend_version="test-mineru",
        )
    )
    store = LocalCASObjectStore(tmp_path / "cas")
    envelope = adapter.scan_shadow_result(
        context=ScannerRunContext(
            run_id="shadow_run_1",
            backend_id="mineru_shadow",
            backend_class="general_local_parser",
            support_tier="shadow",
            file_id="file_1",
            file_version_id="fv_1",
        ),
        store=store,
    )

    assert envelope.scan_run.support_tier == "shadow"
    assert envelope.scan_run.md["shadow_only"] is True
    assert envelope.routing[0].action == "shadowed"
    assert "chunk_compat" not in envelope.contract.projection_kinds
    assert all(projection.md["shadow_only"] is True for projection in envelope.projections)
    raw_artifact = [artifact for artifact in envelope.artifacts if artifact.artifact_type == "scanner_raw_payload"][0]
    assert json.loads(store.get_bytes(raw_artifact.storage_ref).decode("utf-8"))["blocks"][0]["text"] == "Shadow markdown only"
