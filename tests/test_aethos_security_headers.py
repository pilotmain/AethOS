# SPDX-License-Identifier: Apache-2.0
"""§5 Transport security headers."""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aethos_core.api.security_headers as sh
from aethos_core.config import get_settings


@pytest.fixture
def headers_env(monkeypatch):
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "true")
    monkeypatch.setenv("SECURITY_HEADERS_HSTS_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(sh.security_headers_middleware)

    @app.get("/api/v1/ping")
    def ping():
        return {"ok": True}

    return app


def test_core_headers_present(headers_env):
    resp = TestClient(_app()).get("/api/v1/ping")
    assert resp.headers["X-Content-Type-Options"] == "nosniff"
    assert resp.headers["X-Frame-Options"] == "DENY"
    assert "frame-ancestors 'none'" in resp.headers["Content-Security-Policy"]
    assert resp.headers["Referrer-Policy"]
    assert "max-age=" in resp.headers["Strict-Transport-Security"]


def test_disabled_omits_headers(monkeypatch):
    monkeypatch.setenv("SECURITY_HEADERS_ENABLED", "false")
    get_settings.cache_clear()
    try:
        resp = TestClient(_app()).get("/api/v1/ping")
        assert "Content-Security-Policy" not in resp.headers
    finally:
        get_settings.cache_clear()
