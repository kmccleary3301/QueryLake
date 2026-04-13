from pathlib import Path
import sys
import asyncio

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.routing.misc_models import embedding_sparse_call


class _RemoteFn:
    def __init__(self, value):
        self._value = value

    async def remote(self, payload):
        return self._value


class _Handle:
    def __init__(self, value):
        self.run = _RemoteFn(value)


class _Auth:
    username = "tester"


class _Enabled:
    embedding = True


class _Defaults:
    embedding = "embed-model"


class _Config:
    enabled_model_classes = _Enabled()
    default_models = _Defaults()


class _DummyUmbrella:
    def __init__(self, value):
        self.config = _Config()
        self.embedding_handles = {"embed-model": _Handle(value)}
        self.database = object()


def test_embedding_sparse_route_returns_lexical_weights(monkeypatch):
    umbrella = _DummyUmbrella([
        {"embedding": [0.1], "lexical_weights": {12: 0.4}, "token_count": 5},
        {"embedding": [0.2], "lexical_weights": {3: 0.9}, "token_count": 7},
    ])
    monkeypatch.setattr(
        "QueryLake.routing.misc_models.api.get_user",
        lambda *_args, **_kwargs: (object(), _Auth(), None, 0),
    )
    monkeypatch.setattr(
        "QueryLake.routing.misc_models.api.increment_usage_tally",
        lambda *_args, **_kwargs: None,
    )
    monkeypatch.setattr(
        "QueryLake.routing.misc_models.log_usage_event",
        lambda *_args, **_kwargs: None,
    )

    result = asyncio.run(embedding_sparse_call(umbrella, auth={}, inputs=["a", "b"]))
    assert result == [{12: 0.4}, {3: 0.9}]
