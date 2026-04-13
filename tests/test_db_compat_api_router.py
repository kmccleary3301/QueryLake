from pathlib import Path
import sys
import json

import pytest
from fastapi import Request
from starlette.responses import JSONResponse

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.routing.api_call_router import api_general_call
from QueryLake.runtime.db_compat import QueryLakeUnsupportedFeatureError, QueryLakeProfileConfigurationError


class DummyDB:
    def rollback(self):
        self.rolled_back = True

    def flush(self):
        self.flushed = True


class DummyUmbrella:
    def __init__(self):
        self.database = DummyDB()
        self.default_function_arguments = {}

    def api_function_getter(self, _name):
        def inner(**_kwargs):
            raise QueryLakeUnsupportedFeatureError(
                capability="retrieval.sparse.vector",
                profile="postgres_pgvector_light_v1",
                message="Sparse retrieval is not supported by deployment profile 'postgres_pgvector_light_v1'.",
            )

        return inner


class DummyUmbrellaAssertion(DummyUmbrella):
    def api_function_getter(self, _name):
        def inner(**_kwargs):
            raise AssertionError("limit must be an int between 0 and 200")

        return inner


class DummyUmbrellaProfileError(DummyUmbrella):
    def api_function_getter(self, _name):
        def inner(**_kwargs):
            raise QueryLakeProfileConfigurationError(
                "broken_profile",
                "Malformed profile config for 'broken_profile'.",
            )

        return inner


def _clean_args(_defaults, arguments, function_object=None):
    return arguments


@pytest.mark.asyncio
async def test_api_general_call_returns_501_for_unsupported_feature():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/search",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    async def receive():
        return {"type": "http.request", "body": json.dumps({}).encode(), "more_body": False}

    request = Request(scope, receive=receive)
    response = await api_general_call(
        DummyUmbrella(),
        _clean_args,
        {},
        {},
        request,
        "search",
        None,
    )
    assert isinstance(response, JSONResponse)
    assert response.status_code == 501
    payload = json.loads(response.body.decode())
    assert payload["success"] is False
    assert payload["detail"]["type"] == "unsupported_feature"
    assert payload["detail"]["capability"] == "retrieval.sparse.vector"
    assert payload["detail"]["docs_ref"] == "docs/database/DB_COMPAT_PROFILES.md#unsupported-feature-contract"
    assert payload["detail"]["retryable"] is False


@pytest.mark.asyncio
async def test_api_general_call_returns_400_for_assertion_validation_error():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/search",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    async def receive():
        return {"type": "http.request", "body": json.dumps({}).encode(), "more_body": False}

    request = Request(scope, receive=receive)
    response = await api_general_call(
        DummyUmbrellaAssertion(),
        _clean_args,
        {},
        {},
        request,
        "search",
        None,
    )
    payload = json.loads(response.body.decode())
    assert response.status_code == 400
    assert payload["detail"]["type"] == "invalid_request"
    assert payload["detail"]["code"] == "ql.invalid_request"
    assert payload["detail"]["docs_ref"] == "docs/sdk/API_REFERENCE.md"
    assert payload["detail"]["retryable"] is False


@pytest.mark.asyncio
async def test_api_general_call_returns_500_for_profile_configuration_error():
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/search",
        "query_string": b"",
        "headers": [(b"content-type", b"application/json")],
    }

    async def receive():
        return {"type": "http.request", "body": json.dumps({}).encode(), "more_body": False}

    request = Request(scope, receive=receive)
    response = await api_general_call(
        DummyUmbrellaProfileError(),
        _clean_args,
        {},
        {},
        request,
        "search",
        None,
    )
    payload = json.loads(response.body.decode())
    assert response.status_code == 500
    assert payload["detail"]["type"] == "profile_configuration_error"
    assert payload["detail"]["profile"] == "broken_profile"
    assert payload["detail"]["docs_ref"] == "docs/database/PROFILE_DIAGNOSTICS.md#startup-validation-rules"
    assert payload["detail"]["retryable"] is False
