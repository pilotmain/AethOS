# SPDX-License-Identifier: Apache-2.0
"""§4 API rate limiting & abuse protection."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aethos_core.api.rate_limit as rl
from aethos_core.config import get_settings


@pytest.fixture
def rl_env(monkeypatch):
    monkeypatch.setenv("RATE_LIMIT_ENABLED", "true")
    monkeypatch.setenv("RATE_LIMIT_EXEMPT_LOOPBACK", "false")
    monkeypatch.setenv("RATE_LIMIT_AUTH_PER_MIN", "3")
    monkeypatch.setenv("RATE_LIMIT_DEFAULT_PER_MIN", "5")
    monkeypatch.setenv("MAX_REQUEST_BYTES", "1000")
    get_settings.cache_clear()
    rl.reset_state()
    yield
    rl.reset_state()
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(rl.rate_limit_middleware)

    @app.get("/api/v1/ping")
    def ping():
        return {"ok": True}

    @app.post("/api/v1/aethos-identity/login")
    def login():
        return {"ok": True}

    @app.post("/api/v1/echo")
    def echo(body: dict):
        return body

    return app


def test_default_bucket_limit_and_429_headers(rl_env):
    client = TestClient(_app())
    for _ in range(5):
        assert client.get("/api/v1/ping").status_code == 200
    blocked = client.get("/api/v1/ping")
    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"]
    assert blocked.headers["X-RateLimit-Remaining"] == "0"


def test_auth_bucket_is_tighter(rl_env):
    client = TestClient(_app())
    for _ in range(3):
        assert client.post("/api/v1/aethos-identity/login").status_code == 200
    assert client.post("/api/v1/aethos-identity/login").status_code == 429


def test_request_size_cap(rl_env):
    client = TestClient(_app())
    big = {"data": "x" * 2000}
    assert client.post("/api/v1/echo", json=big).status_code == 413


def test_rate_limit_headers_present_on_success(rl_env):
    client = TestClient(_app())
    resp = client.get("/api/v1/ping")
    assert resp.headers["X-RateLimit-Limit"] == "5"
    assert int(resp.headers["X-RateLimit-Remaining"]) >= 0
