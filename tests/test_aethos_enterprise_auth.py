# SPDX-License-Identifier: Apache-2.0
"""§2 enterprise auth — password hashing, TOTP, sessions, middleware enforcement."""

from __future__ import annotations

import time

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import aethos_core.api.routes.aethos_identity as ident
from aethos_core.config import get_settings


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("MFA_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_password_hash_roundtrip():
    h = ident.hash_password("correct horse battery staple")
    assert h.startswith("scrypt$")
    assert ident.verify_password("correct horse battery staple", h)
    assert not ident.verify_password("wrong", h)


def test_totp_rfc6238():
    secret = ident.new_totp_secret()
    code = ident._totp_at(secret, int(time.time() // 30))
    assert ident.verify_totp(secret, code)
    assert not ident.verify_totp(secret, "000000")


def test_session_signature_tamper_evident():
    signed = ident._sign("session-abc")
    assert ident._unsign(signed) == "session-abc"
    assert ident._unsign(signed[:-1] + ("0" if signed[-1] != "0" else "1")) is None


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")

    @app.get("/api/v1/protected/ping")
    def _protected(request: Request):
        return {"user": request.state.user["email"]}

    return app


def test_middleware_rejects_unauthenticated(auth_env):
    client = TestClient(_app())
    assert client.get("/api/v1/protected/ping").status_code == 401
    # Open endpoints stay reachable.
    assert client.get("/api/v1/aethos-identity/session").status_code == 200


def test_bootstrap_login_session_flow(auth_env):
    client = TestClient(_app())
    boot = client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    ).json()
    assert boot["ok"] and "admin" in boot["roles"]

    # Second bootstrap is refused.
    assert client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "x@y.z", "password": "supersecret123"},
    ).json()["ok"] is False

    login = client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    ).json()
    assert login["ok"]

    # Cookie now grants access to the protected route.
    assert client.get("/api/v1/protected/ping").json()["user"] == "admin@aethos.test"

    # Logout clears the session.
    assert client.post("/api/v1/aethos-identity/logout").json()["ok"]
    assert client.get("/api/v1/protected/ping").status_code == 401


def test_bad_password_and_lockout(auth_env, monkeypatch):
    monkeypatch.setenv("AUTH_LOGIN_MAX_ATTEMPTS", "2")
    get_settings.cache_clear()
    client = TestClient(_app())
    client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    )
    for _ in range(2):
        r = client.post(
            "/api/v1/aethos-identity/login",
            json={"email": "admin@aethos.test", "password": "nope"},
        ).json()
        assert r["error"] == "invalid_credentials"
    locked = client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    ).json()
    assert locked["error"] == "account_locked"
