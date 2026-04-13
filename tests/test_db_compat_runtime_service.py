from pathlib import Path
import sys
import asyncio

import pytest
from fastapi import HTTPException

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError
from QueryLake.runtime.service import SessionEntry, ToolchainRuntimeService


class DummyUserAuth:
    username = "alice"


class DummyRuntime:
    def __init__(self):
        self.server_context = {}
        self.session_id = "sess-1"
        self.state = {}
        self.files = {}


class DummyEntryRuntime(DummyRuntime):
    def __init__(self, exc):
        super().__init__()
        self._exc = exc

    async def process_event(self, *_args, **_kwargs):
        raise self._exc


async def _return_entry(entry):
    return entry


@pytest.mark.asyncio
async def test_runtime_service_post_event_returns_501_for_unsupported_feature(monkeypatch):
    service = object.__new__(ToolchainRuntimeService)
    service._logger = None
    service.database = object()
    service.event_store = None
    service.stream_hub = None
    service.job_registry = None
    service.signal_bus = None
    entry = SessionEntry(
        runtime=DummyEntryRuntime(QueryLakeUnsupportedFeatureError(capability="retrieval.sparse.vector", profile="postgres_pgvector_light_v1")),
        lock=asyncio.Lock(),
        last_rev=0,
        author="alice",
        toolchain_id="t1",
    )
    emitted = []
    persisted = []
    monkeypatch.setattr(service, "_ensure_session", lambda *_args, **_kwargs: _return_entry(entry))
    monkeypatch.setattr("QueryLake.runtime.service.toolchains_api.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr(service, "_emit_event", lambda *_args, **_kwargs: emitted.append(_args[1]) or None)
    monkeypatch.setattr(service, "_persist_session_state", lambda *_args, **_kwargs: persisted.append(True))

    with pytest.raises(HTTPException) as exc_info:
        await service.post_event("sess-1", "node-1", {}, 0, auth={}, correlation_id=None)

    assert exc_info.value.status_code == 501
    assert exc_info.value.detail["type"] == "unsupported_feature"
    assert exc_info.value.detail["docs_ref"] == "docs/database/DB_COMPAT_PROFILES.md#unsupported-feature-contract"
    assert exc_info.value.detail["retryable"] is False
    assert emitted == ["EVENT_RECEIVED", "EVENT_FAILED"]
    assert persisted == [True]


@pytest.mark.asyncio
async def test_runtime_service_post_event_returns_503_for_deployment_disabled_assertion(monkeypatch):
    service = object.__new__(ToolchainRuntimeService)
    service._logger = None
    service.database = object()
    entry = SessionEntry(
        runtime=DummyEntryRuntime(AssertionError("LLMs are disabled on this QueryLake Deployment")),
        lock=asyncio.Lock(),
        last_rev=0,
        author="alice",
        toolchain_id="t1",
    )
    monkeypatch.setattr(service, "_ensure_session", lambda *_args, **_kwargs: _return_entry(entry))
    monkeypatch.setattr("QueryLake.runtime.service.toolchains_api.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr(service, "_emit_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_persist_session_state", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        await service.post_event("sess-1", "node-1", {}, 0, auth={}, correlation_id=None)

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "LLMs are disabled on this QueryLake Deployment"


@pytest.mark.asyncio
async def test_runtime_service_post_event_returns_500_for_generic_assertion(monkeypatch):
    service = object.__new__(ToolchainRuntimeService)
    service._logger = None
    service.database = object()
    entry = SessionEntry(
        runtime=DummyEntryRuntime(AssertionError("bad runtime invariant")),
        lock=asyncio.Lock(),
        last_rev=0,
        author="alice",
        toolchain_id="t1",
    )
    monkeypatch.setattr(service, "_ensure_session", lambda *_args, **_kwargs: _return_entry(entry))
    monkeypatch.setattr("QueryLake.runtime.service.toolchains_api.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr(service, "_emit_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_persist_session_state", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        await service.post_event("sess-1", "node-1", {}, 0, auth={}, correlation_id=None)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "bad runtime invariant"


@pytest.mark.asyncio
async def test_runtime_service_post_event_returns_500_for_generic_exception(monkeypatch):
    service = object.__new__(ToolchainRuntimeService)
    service._logger = None
    service.database = object()
    entry = SessionEntry(
        runtime=DummyEntryRuntime(RuntimeError("database exploded")),
        lock=asyncio.Lock(),
        last_rev=0,
        author="alice",
        toolchain_id="t1",
    )
    monkeypatch.setattr(service, "_ensure_session", lambda *_args, **_kwargs: _return_entry(entry))
    monkeypatch.setattr("QueryLake.runtime.service.toolchains_api.get_user", lambda *_args, **_kwargs: (None, DummyUserAuth()))
    monkeypatch.setattr(service, "_emit_event", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(service, "_persist_session_state", lambda *_args, **_kwargs: None)

    with pytest.raises(HTTPException) as exc_info:
        await service.post_event("sess-1", "node-1", {}, 0, auth={}, correlation_id=None)

    assert exc_info.value.status_code == 500
    assert exc_info.value.detail == "database exploded"
