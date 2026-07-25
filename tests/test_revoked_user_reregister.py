# SPDX-License-Identifier: Apache-2.0
"""Revoked/ended beta users can re-register, landing in 'pending' until the platform
owner grants access — instead of the old dead-end (can't log in AND 'email already
registered'). Email verification gates it on hosted, so only the inbox owner completes it.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aethos_core.api.routes.aethos_identity as ident
from aethos_core.config import get_settings


@pytest.fixture
def signup_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")  # no email verification gate in tests
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(ident.router, prefix="/api/v1")
    return app


def test_pending_status_blocks_login():
    assert ident._entitlement_error_for_user({"email": "x@y.com", "status": "pending"}) == "access_pending"


def test_revoked_user_can_reregister_into_pending(signup_env):
    client = TestClient(_app())
    pw = "betatester1234"
    # Sign up, then revoke (simulate beta ended) by direct store edit.
    assert client.post("/api/v1/aethos-identity/register", json={"email": "beta@x.com", "password": pw}).json()["ok"]
    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["beta@x.com"]["status"] = "revoked"
    store_path.write_text(json.dumps(store))

    # Revoked user is blocked at login.
    blocked = client.post("/api/v1/aethos-identity/login", json={"email": "beta@x.com", "password": pw}).json()
    assert blocked["ok"] is False and blocked["error"] == "access_revoked"

    # Re-register with the same email → allowed, lands pending (not signed in).
    out = client.post(
        "/api/v1/aethos-identity/register",
        json={"email": "beta@x.com", "password": "newbetapass1234"},
    ).json()
    assert out["ok"] is True and out.get("pending") is True
    store = json.loads(store_path.read_text())
    assert store["users"]["beta@x.com"]["status"] == "pending"

    # Still cannot sign in while pending.
    pend = client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@x.com", "password": "newbetapass1234"},
    ).json()
    assert pend["ok"] is False and pend["error"] == "access_pending"

    # Owner grants access → can sign in with the new password.
    store = json.loads(store_path.read_text())
    store["users"]["beta@x.com"]["status"] = "trial"
    store_path.write_text(json.dumps(store))
    ok = client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@x.com", "password": "newbetapass1234"},
    ).json()
    assert ok["ok"] is True


def test_active_user_reregister_still_blocked(signup_env):
    client = TestClient(_app())
    assert client.post(
        "/api/v1/aethos-identity/register", json={"email": "good@x.com", "password": "goodpass12345"}
    ).json()["ok"]
    # Re-registering an account in good standing must NOT reset it.
    out = client.post(
        "/api/v1/aethos-identity/register",
        json={"email": "good@x.com", "password": "otherpass12345"},  # gitleaks:allow - fixture
    ).json()
    assert out["ok"] is False and out["error"] == "email_taken"
