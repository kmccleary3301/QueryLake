from pathlib import Path
import os
import shutil
import asyncio
import time
from types import SimpleNamespace

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.files.object_store import LocalCASObjectStore
from QueryLake.files.service import FileEvent, FilesRuntimeService
from QueryLake.database import sql_db_tables as T
from QueryLake.runtime.sse import SessionStreamHub
from QueryLake.scanning.contracts import materialize_legacy_markdown_envelope
from QueryLake.scanning.persistence import read_scanner_envelope_payload, write_scanner_envelope


class _DummyDB:
    def add(self, _row):
        return None

    def commit(self):
        return None


class _DummyUmbrella:
    def __init__(self, handles=None):
        self.chandra_handles = handles or {}


class _RuntimeFakeDB:
    def __init__(self, file_version, file_row=None):
        self.file_version = file_version
        self.file_row = file_row or SimpleNamespace(
            id=file_version.file_id,
            logical_name="runtime-test.txt",
            created_by=None,
        )
        self.added = []
        self.commits = 0

    def get(self, model, key):
        if model is T.file_version and key == self.file_version.id:
            return self.file_version
        if model is T.file and key == self.file_row.id:
            return self.file_row
        return None

    def add(self, row):
        self.added.append(row)

    def commit(self):
        self.commits += 1


class _RuntimeFakeEvents:
    def __init__(self):
        self.events = []
        self.jobs = []
        self.dead_letters = []

    def append(self, file_id, version_id, kind, payload):
        event = FileEvent(
            file_id=file_id,
            version_id=version_id,
            rev=len(self.events) + 1,
            kind=kind,
            payload=payload,
            ts=time.time(),
        )
        self.events.append(event)
        return event

    def upsert_job(self, job_id, file_id, version_id, status, *, progress=None, result_meta=None):
        self.jobs.append(
            {
                "job_id": job_id,
                "file_id": file_id,
                "version_id": version_id,
                "status": status,
                "progress": progress,
                "result_meta": result_meta,
            }
        )

    def list_jobs(self, _file_id):
        return list(self.jobs)

    def dead_letter(self, file_id, version_id, event, error):
        self.dead_letters.append(
            {
                "file_id": file_id,
                "version_id": version_id,
                "event": event,
                "error": error,
            }
        )


def _build_process_runtime(tmp_path, monkeypatch, *, bridge_mode="off"):
    if bridge_mode == "off":
        monkeypatch.delenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", raising=False)
    else:
        monkeypatch.setenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", bridge_mode)
    store = LocalCASObjectStore(tmp_path / "cas")
    bytes_cas = store.put_bytes(b"plain text bytes")
    file_version = SimpleNamespace(
        id="fv_runtime",
        file_id="file_runtime",
        bytes_cas=bytes_cas,
        size_bytes=16,
        mime_type="text/plain",
        processing_fingerprint=None,
    )
    db = _RuntimeFakeDB(file_version)
    service = FilesRuntimeService(db, object_store=store, umbrella=None)
    events = _RuntimeFakeEvents()
    service.events = events
    service._assert_file_readable = lambda _file_id, _auth: None  # type: ignore[method-assign]

    async def _noop_publish(_file_id, _event):
        return None

    service._publish = _noop_publish  # type: ignore[method-assign]
    return service, db, events, store, file_version


def _fake_scanner_bridge(store, *, run_id="scan_fv_runtime", markdown="compat text"):
    envelope = materialize_legacy_markdown_envelope(
        run_id=run_id,
        backend_id="pymupdf4llm_native",
        backend_class="native_digital_extraction",
        support_tier="first_class",
        legacy_output_contract="text_layer_fastpath_markdown",
        markdown=markdown,
        meta={
            "engine": "pdf_text_layer",
            "pages": 1,
            "output_contract": "text_layer_fastpath_markdown",
            "page_source_by_page": {"0001": "text_layer"},
            "page_source_counts": {"ocr": 0, "text_layer": 1},
        },
        file_id="file_runtime",
        file_version_id="fv_runtime",
    )
    return envelope, write_scanner_envelope(store, envelope)


def test_local_cas_store_roundtrip(tmp_path: Path):
    base = tmp_path / "cas"
    store = LocalCASObjectStore(base_dir=str(base))
    data = b"hello world"
    cas = store.put_bytes(data)
    assert store.exists(cas)
    out = store.get_bytes(cas)
    assert out == data


def test_files_fingerprint_stability():
    fp1 = FilesRuntimeService.compute_fingerprint("deadbeef")
    fp2 = FilesRuntimeService.compute_fingerprint("deadbeef")
    assert fp1 == fp2
    fp3 = FilesRuntimeService.compute_fingerprint("deadbeee")
    assert fp1 != fp3


def test_sse_hub_publish_and_backlog_replay():
    async def run():
        hub = SessionStreamHub()
        session_id = "file_x"
        sub = await hub.subscribe(session_id)
        # Push a couple of events
        await sub.push({"event": "FILE_UPLOADED", "data": "{}", "id": 1})
        await sub.push({"event": "CHUNKED", "data": "{}", "id": 2})

        # Consume
        items = []
        async def consume(n=2):
            async for item in sub.stream():
                items.append(item)
                if len(items) >= n:
                    break

        await consume(2)
        assert [i["event"] for i in items] == ["FILE_UPLOADED", "CHUNKED"]

        await hub.unsubscribe(session_id, sub)

    asyncio.run(run())


def test_render_cache_key_is_stable_and_page_sensitive():
    key_1 = FilesRuntimeService._compute_render_cache_key(
        "abc123",
        dpi=144,
        page_num=1,
        profile="speed",
        max_image_pixels=589824,
    )
    key_2 = FilesRuntimeService._compute_render_cache_key(
        "abc123",
        dpi=144,
        page_num=1,
        profile="speed",
        max_image_pixels=589824,
    )
    key_3 = FilesRuntimeService._compute_render_cache_key(
        "abc123",
        dpi=144,
        page_num=2,
        profile="speed",
        max_image_pixels=589824,
    )
    assert key_1 == key_2
    assert key_1 != key_3


def test_chandra_handle_selection_prefers_configured_id(monkeypatch):
    handles = {
        "chandra-v1": "HANDLE_ID",
        "Chandra Friendly Name": "HANDLE_ALIAS",
    }
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella(handles))

    monkeypatch.setenv("QUERYLAKE_DEFAULT_CHANDRA_ID", "chandra-v1")
    picked = asyncio.run(service._select_chandra_handle())
    assert picked == "HANDLE_ID"


def test_chandra_handle_selection_falls_back_to_id_like_key(monkeypatch):
    handles = {
        "chandra-v2": "HANDLE_ID",
        "Chandra Friendly Name": "HANDLE_ALIAS",
    }
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella(handles))

    monkeypatch.delenv("QUERYLAKE_DEFAULT_CHANDRA_ID", raising=False)
    picked = asyncio.run(service._select_chandra_handle())
    assert picked == "HANDLE_ID"


def test_render_cache_eviction_order(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_CHANDRA_RENDER_CACHE_MAX_ENTRIES", "2")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    async def run():
        await service._render_cache_set("k1", "v1")
        await service._render_cache_set("k2", "v2")
        await service._render_cache_set("k3", "v3")
        first = await service._render_cache_get("k1")
        second = await service._render_cache_get("k2")
        third = await service._render_cache_get("k3")
        return first, second, third

    first, second, third = asyncio.run(run())
    assert first is None
    assert second == "v2"
    assert third == "v3"


def test_pdf_text_layer_auto_mode_selects_digital_like_pages(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "auto")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_CHARS_PER_PAGE", "50")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_COVERAGE", "0.6")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    pages = [
        "A" * 120,
        "B" * 90,
        "C" * 80,
        "D" * 70,
        "",
    ]
    decision = service._evaluate_pdf_text_layer_candidate(pages)
    assert decision["selected"] is True
    assert decision["reason"] == "auto_threshold_met"
    assert decision["pages"] == 5


def test_pdf_text_layer_auto_mode_rejects_sparse_text(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "auto")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_CHARS_PER_PAGE", "80")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_COVERAGE", "0.8")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    pages = [
        "A" * 100,
        "B" * 40,
        "",
        "",
        "C" * 30,
    ]
    decision = service._evaluate_pdf_text_layer_candidate(pages)
    assert decision["selected"] is False
    assert decision["reason"] == "auto_threshold_miss"


def test_pdf_text_layer_prefer_mode_selects_when_any_text_exists(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "prefer")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    decision = service._evaluate_pdf_text_layer_candidate(["", "hello", ""])
    assert decision["selected"] is True
    assert decision["reason"] == "prefer_nonempty"


def test_pdf_text_layer_off_mode_never_selects(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "off")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    decision = service._evaluate_pdf_text_layer_candidate(["x" * 100, "y" * 100])
    assert decision["selected"] is False
    assert decision["reason"] == "mode_off"


def test_pdf_text_layer_mixed_mode_selects_page_overrides(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "mixed")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_CHARS_PER_PAGE", "50")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    decision = service._evaluate_pdf_text_layer_page_overrides(
        ["A" * 120, "B" * 40, "", "C" * 75]
    )
    assert decision["selected"] is True
    assert decision["mode"] == "mixed"
    assert decision["selected_pages"] == 2
    assert decision["selected_page_indices"] == [0, 3]


def test_pdf_text_layer_mixed_mode_handles_zero_selected(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "mixed")
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_MIN_CHARS_PER_PAGE", "200")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    decision = service._evaluate_pdf_text_layer_page_overrides(
        ["A" * 120, "B" * 40, "", "C" * 75]
    )
    assert decision["selected"] is False
    assert decision["selected_pages"] == 0
    assert decision["selected_page_indices"] == []


def test_pdf_output_contract_helpers():
    page_sources = FilesRuntimeService._build_page_source_by_page(
        4,
        text_layer_page_indices={0, 3},
    )
    assert page_sources == {
        "0001": "text_layer",
        "0002": "ocr",
        "0003": "ocr",
        "0004": "text_layer",
    }
    assert FilesRuntimeService._resolve_pdf_output_contract(4, text_layer_pages=0) == "ocr_markdown"
    assert FilesRuntimeService._resolve_pdf_output_contract(4, text_layer_pages=4) == "text_layer_fastpath_markdown"
    assert FilesRuntimeService._resolve_pdf_output_contract(4, text_layer_pages=2) == "mixed_text_layer_fastpath_markdown"


def test_try_extract_pdf_text_layer_emits_fastpath_contract(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "prefer")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    def _fake_extract(_data):
        return ["A" * 120, "B" * 90], {"engine": "pdf_text_layer", "status": "not_selected"}

    service._extract_pdf_text_layer_pages = _fake_extract  # type: ignore[method-assign]
    text, meta = service._try_extract_pdf_text_layer(b"pdf")
    assert text is not None
    assert meta["output_contract"] == "text_layer_fastpath_markdown"
    assert meta["page_source_counts"] == {"text_layer": 2, "ocr": 0}
    assert meta["page_source_by_page"] == {
        "0001": "text_layer",
        "0002": "text_layer",
    }


def test_try_extract_pdf_text_layer_can_use_pymupdf4llm_native_engine(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "prefer")
    monkeypatch.setenv("QUERYLAKE_PDF_NATIVE_ENGINE", "pymupdf4llm")

    from QueryLake.scanning import native as native_module
    from QueryLake.scanning.adapters import AdapterAvailability
    from QueryLake.scanning.native import NativeExtractionResult

    class _FakeNativeAdapter:
        def __init__(self, *, quality_policy):
            self.quality_policy = quality_policy

        def check_available(self):
            return AdapterAvailability(backend_id="pymupdf4llm_native", available=True, reason="test")

        def extract_pdf_bytes(self, _data):
            return NativeExtractionResult(
                markdown="## Page 1\n\n" + ("Native text. " * 20),
                page_markdown=["Native text. " * 20],
                backend_version="test-version",
            )

    monkeypatch.setattr(native_module, "PyMuPDF4LLMNativeAdapter", _FakeNativeAdapter)
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    text, meta = service._try_extract_pdf_text_layer(b"pdf")

    assert text.startswith("## Page 1")
    assert meta["engine"] == "pymupdf4llm"
    assert meta["output_contract"] == "text_layer_fastpath_markdown"
    assert meta["page_source_by_page"] == {"0001": "native_text"}
    assert meta["native_quality"]["selected"] is True


def test_try_extract_pdf_text_layer_auto_falls_back_to_pypdf_when_pymupdf4llm_missing(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_PDF_TEXT_LAYER_MODE", "prefer")
    monkeypatch.setenv("QUERYLAKE_PDF_NATIVE_ENGINE", "auto")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    def _fake_extract(_data):
        return ["A" * 120], {"engine": "pdf_text_layer", "status": "parsed"}

    service._extract_pdf_text_layer_pages = _fake_extract  # type: ignore[method-assign]
    text, meta = service._try_extract_pdf_text_layer(b"pdf")

    assert text == "## Page 1\n\n" + ("A" * 120)
    assert meta["engine"] == "pdf_text_layer"
    assert meta["output_contract"] == "text_layer_fastpath_markdown"


def test_scanner_runtime_bridge_defaults_to_off(monkeypatch):
    monkeypatch.delenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", raising=False)
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    result = service._build_scanner_runtime_bridge(
        file_id="file_1",
        version_id="fv_1",
        text_result="text",
        source_meta={
            "engine": "chandra",
            "pages": 1,
            "output_contract": "ocr_markdown",
            "page_source_by_page": {"0001": "ocr"},
        },
        ocr_info_cas="ocr-info-cas",
        ocr_engine="chandra",
        selected_profile="balanced",
    )

    assert service._scanner_runtime_bridge == "off"
    assert result is None


def test_scanner_runtime_bridge_persists_chandra_envelope_when_enabled(tmp_path, monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", "enrich_ocr_done")
    store = LocalCASObjectStore(tmp_path / "cas")
    service = FilesRuntimeService(_DummyDB(), object_store=store, umbrella=_DummyUmbrella())

    result = service._build_scanner_runtime_bridge(
        file_id="file_1",
        version_id="fv_1",
        text_result="## Page 1\n\nOCR text",
        source_meta={
            "engine": "chandra",
            "profile": "balanced",
            "pages": 1,
            "ocr_pages": 1,
            "text_layer_pages": 0,
            "output_contract": "ocr_markdown",
            "page_source_by_page": {"0001": "ocr"},
            "page_source_counts": {"ocr": 1, "text_layer": 0},
            "render_cache_hits": 0,
            "render_cache_misses": 1,
        },
        ocr_info_cas="ocr-info-cas",
        ocr_engine="chandra",
        selected_profile="balanced",
    )

    assert result is not None
    envelope, persisted = result
    payload = read_scanner_envelope_payload(store, persisted.envelope_ref.storage_ref)
    assert envelope.scan_run.run_id == "scan_fv_1"
    assert envelope.contract.legacy_output_contract == "ocr_markdown"
    assert payload["scan_run"]["backend_id"] == "chandra_1"
    assert payload["artifacts"][1]["storage_ref"] == "ocr-info-cas"


def test_scanner_runtime_bridge_can_wrap_text_layer_fastpath(tmp_path, monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", "dual_event")
    store = LocalCASObjectStore(tmp_path / "cas")
    service = FilesRuntimeService(_DummyDB(), object_store=store, umbrella=_DummyUmbrella())

    result = service._build_scanner_runtime_bridge(
        file_id="file_1",
        version_id="fv_2",
        text_result="## Page 1\n\nNative text",
        source_meta={
            "engine": "pdf_text_layer",
            "pages": 1,
            "output_contract": "text_layer_fastpath_markdown",
            "page_source_by_page": {"0001": "text_layer"},
            "page_source_counts": {"ocr": 0, "text_layer": 1},
        },
        ocr_info_cas="text-layer-info-cas",
        ocr_engine="pdf_text_layer",
        selected_profile="balanced",
    )

    assert result is not None
    envelope, persisted = result
    payload = read_scanner_envelope_payload(store, persisted.envelope_ref.storage_ref)
    assert envelope.scan_run.backend_id == "pymupdf4llm_native"
    assert envelope.contract.acquisition_mode == "native_text"
    assert payload["contract"]["legacy_output_contract"] == "text_layer_fastpath_markdown"


def test_scanner_runtime_bridge_skips_unsupported_engine(monkeypatch):
    monkeypatch.setenv("QUERYLAKE_SCANNER_RUNTIME_BRIDGE", "enrich_ocr_done")
    service = FilesRuntimeService(_DummyDB(), object_store=LocalCASObjectStore(), umbrella=_DummyUmbrella())

    result = service._build_scanner_runtime_bridge(
        file_id="file_1",
        version_id="fv_3",
        text_result="surya text",
        source_meta={"engine": "surya", "pages": 1, "output_contract": "surya_markdown"},
        ocr_info_cas="surya-info-cas",
        ocr_engine="surya",
        selected_profile="balanced",
    )

    assert result is None


def test_process_version_scanner_bridge_off_preserves_legacy_payload_shape(tmp_path, monkeypatch):
    service, db, events, _store, file_version = _build_process_runtime(
        tmp_path,
        monkeypatch,
        bridge_mode="off",
    )

    result = asyncio.run(service.process_version(file_version.file_id, file_version.id, auth=object()))

    assert result["status"] == "COMPLETED"
    ocr_done = next(event for event in events.events if event.kind == "OCR_DONE")
    assert set(ocr_done.payload) == {
        "pages",
        "ocr_json_cas",
        "engine",
        "profile",
        "render_cache_hits",
        "render_cache_misses",
    }
    assert "scanner_runtime_bridge" not in file_version.processing_fingerprint["fingerprint"]
    assert events.jobs[-1]["status"] == "COMPLETED"
    assert events.jobs[-1]["result_meta"] is None
    chunks = [row for row in db.added if isinstance(row, T.file_chunk)]
    assert len(chunks) == 1
    assert chunks[0].text == f"CAS:{file_version.bytes_cas} size:{file_version.size_bytes}"


def test_process_version_enriches_ocr_done_with_scanner_metadata(tmp_path, monkeypatch):
    service, db, events, store, file_version = _build_process_runtime(
        tmp_path,
        monkeypatch,
        bridge_mode="enrich_ocr_done",
    )
    envelope, persisted = _fake_scanner_bridge(store, markdown="compat text from scanner")

    def _fake_bridge(**_kwargs):
        return envelope, persisted

    service._build_scanner_runtime_bridge = _fake_bridge  # type: ignore[method-assign]

    result = asyncio.run(service.process_version(file_version.file_id, file_version.id, auth=object()))

    assert result["status"] == "COMPLETED"
    assert [event.kind for event in events.events].count("SCANNER_DONE") == 0
    ocr_done = next(event for event in events.events if event.kind == "OCR_DONE")
    assert ocr_done.payload["scanner"]["run_id"] == "scan_fv_runtime"
    assert ocr_done.payload["scanner"]["backend_id"] == "pymupdf4llm_native"
    assert ocr_done.payload["scanner"]["scanner_envelope_cas"] == persisted.envelope_ref.storage_ref
    assert ocr_done.payload["scanner"]["route_explanation_ref"]
    assert read_scanner_envelope_payload(store, persisted.envelope_ref.storage_ref)["scan_run"]["run_id"] == "scan_fv_runtime"
    route_payload = store.get_bytes(ocr_done.payload["scanner"]["route_explanation_ref"])
    assert route_payload is not None
    assert b"scanner_route_explanation_v1" in route_payload
    assert events.jobs[-1]["result_meta"]["scanner"]["run_id"] == "scan_fv_runtime"
    assert events.jobs[-1]["result_meta"]["scanner_envelope_cas"] == persisted.envelope_ref.storage_ref
    assert file_version.processing_fingerprint["fingerprint"]["scanner_runtime_bridge"] == "enrich_ocr_done"
    chunks = [row for row in db.added if isinstance(row, T.file_chunk)]
    assert chunks[0].text == f"CAS:{file_version.bytes_cas} size:{file_version.size_bytes}"


def test_process_version_dual_event_emits_scanner_done_after_ocr_done(tmp_path, monkeypatch):
    service, _db, events, store, file_version = _build_process_runtime(
        tmp_path,
        monkeypatch,
        bridge_mode="dual_event",
    )
    envelope, persisted = _fake_scanner_bridge(store)

    def _fake_bridge(**_kwargs):
        return envelope, persisted

    service._build_scanner_runtime_bridge = _fake_bridge  # type: ignore[method-assign]

    asyncio.run(service.process_version(file_version.file_id, file_version.id, auth=object()))

    event_kinds = [event.kind for event in events.events]
    assert event_kinds == [
        "SAFETY_SCANNED",
        "OCR_DONE",
        "SCANNER_DONE",
        "TEXT_NORMALIZED",
        "CHUNKED",
        "EMBEDDED",
        "INDEXED",
    ]
    scanner_done = next(event for event in events.events if event.kind == "SCANNER_DONE")
    assert scanner_done.payload["scanner_envelope_cas"] == persisted.envelope_ref.storage_ref
    assert scanner_done.payload["acquisition_mode"] == "native_text"
    assert scanner_done.payload["route_explanation_ref"]


def test_process_version_scanner_bridge_failure_is_nonfatal_when_enabled(tmp_path, monkeypatch):
    service, _db, events, _store, file_version = _build_process_runtime(
        tmp_path,
        monkeypatch,
        bridge_mode="enrich_ocr_done",
    )

    def _failing_bridge(**_kwargs):
        raise RuntimeError("bridge exploded")

    service._build_scanner_runtime_bridge = _failing_bridge  # type: ignore[method-assign]

    result = asyncio.run(service.process_version(file_version.file_id, file_version.id, auth=object()))

    assert result["status"] == "COMPLETED"
    assert "FAILED" not in [event.kind for event in events.events]
    ocr_done = next(event for event in events.events if event.kind == "OCR_DONE")
    assert ocr_done.payload["scanner"] == {
        "status": "failed",
        "backend_id": "none",
        "error": "bridge exploded",
    }
    assert events.jobs[-1]["status"] == "COMPLETED"
    assert events.jobs[-1]["result_meta"] is None


def test_process_version_idempotence_short_circuits_before_runtime_events(tmp_path, monkeypatch):
    service, db, events, _store, file_version = _build_process_runtime(
        tmp_path,
        monkeypatch,
        bridge_mode="enrich_ocr_done",
    )
    file_version.processing_fingerprint = FilesRuntimeService.compute_fingerprint(
        file_version.bytes_cas,
        extra={
            "surya": False,
            "chandra": False,
            "embed": False,
            "ocr_profile": service._default_chandra_profile,
            "chandra_dpi": service._default_chandra_dpi,
            "pdf_text_layer_mode": service._pdf_text_layer_mode,
            "pdf_text_layer_min_chars_per_page": service._pdf_text_min_chars_per_page,
            "pdf_text_layer_min_coverage": service._pdf_text_min_coverage,
            "scanner_runtime_bridge": "enrich_ocr_done",
        },
    )

    result = asyncio.run(service.process_version(file_version.file_id, file_version.id, auth=object()))

    assert result == {"job_id": None, "status": "COMPLETED", "note": "already_processed"}
    assert events.events == []
    assert events.jobs == []
    assert db.added == []
