# SPDX-License-Identifier: Apache-2.0
"""Platform owner role, entitlements, and owner admin API."""

from __future__ import annotations

import json
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aethos_core.api.routes.aethos_identity as ident
from aethos_core.config import get_settings
from aethos_core.security import rbac


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    monkeypatch.setenv("PLATFORM_OWNER_EMAILS", "owner@aethos.test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")
    return app


def _seed_users(client: TestClient) -> None:
    client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "owner@aethos.test", "password": "supersecret123"},
    )
    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["beta@aethos.test"] = {
        "user_id": "beta@aethos.test",
        "email": "beta@aethos.test",
        "roles": ["operator"],
        "auth": "local",
        "password": ident.hash_password("betapass12345"),
        "status": "trial",
        "entitlement_source": "manual",
        "plan": "beta",
        "access_expires_at": None,
    }
    store_path.write_text(json.dumps(store))


def test_platform_owner_is_env_computed_not_stored(auth_env):
    owner = {"email": "owner@aethos.test", "roles": ["operator"]}
    assert rbac.is_platform_owner(owner)
    perms = rbac.permissions_for_user(owner)
    assert rbac.OWN_PLATFORM in perms
    assert rbac.MANAGE_USERS in perms
    assert rbac.APPROVE not in perms
    assert perms != set(rbac.ALL_PERMISSIONS)
    assert rbac.OWN_PLATFORM not in rbac.permissions_for_roles(["admin"])
    assert not rbac.is_platform_owner({"email": "beta@aethos.test"})


def test_platform_owner_with_tenant_admin_can_approve_in_own_tenant(auth_env):
    owner = {
        "user_id": "owner@aethos.test",
        "email": "owner@aethos.test",
        "roles": ["tenant_admin"],
    }
    path = "/api/v1/channels/pairing/approve"
    assert rbac.is_authorized(["tenant_admin"], "POST", path, user=owner)


def test_plain_operator_cannot_approve(auth_env):
    plain = {"email": "beta@aethos.test", "roles": ["operator"]}
    path = "/api/v1/channels/pairing/approve"
    assert not rbac.is_authorized(["operator"], "POST", path, user=plain)


def test_owner_can_approve_channel_pairing(auth_env, tmp_path, monkeypatch):
    monkeypatch.setenv("CHANNEL_PAIRING_STORE_DIR", str(tmp_path / "pairing"))
    get_settings.cache_clear()

    from aethos_core.api.routes.channels import router as channels_router
    from aethos_core.channels.pairing_store import is_sender_allowed, request_pairing

    app = FastAPI()
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")
    app.include_router(channels_router, prefix="/api/v1")
    client = TestClient(app)
    _seed_users(client)
    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["owner@aethos.test"]["roles"] = ["tenant_admin"]
    store_path.write_text(json.dumps(store))

    pairing = request_pairing("telegram", "sender-1085", preview="hi")
    code = str(pairing["code"])

    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "owner@aethos.test", "password": "supersecret123"},
    )
    approved = client.post(
        "/api/v1/channels/pairing/approve",
        json={"channel": "telegram", "code": code},
    )
    assert approved.status_code == 200
    assert approved.json().get("ok") is True
    assert is_sender_allowed("telegram", "sender-1085")

    beta = TestClient(app)
    beta.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@aethos.test", "password": "betapass12345"},
    )
    blocked = beta.post(
        "/api/v1/channels/pairing/approve",
        json={"channel": "telegram", "code": "0000"},
    )
    assert blocked.status_code == 403
    assert blocked.json()["required_permission"] == rbac.APPROVE


def test_session_reports_is_platform_owner(auth_env):
    client = TestClient(_app())
    _seed_users(client)
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "owner@aethos.test", "password": "supersecret123"},
    )
    sess = client.get("/api/v1/aethos-identity/session").json()
    assert sess["is_platform_owner"] is True
    assert "own_platform" in sess["user"]["permissions"]
    assert sess.get("is_tenant_owner") is True


def test_non_owner_cannot_call_owner_admin_api(auth_env):
    client = TestClient(_app())
    _seed_users(client)
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@aethos.test", "password": "betapass12345"},
    )
    resp = client.get("/api/v1/aethos-identity/admin/users")
    assert resp.json()["ok"] is False


def test_owner_can_grant_and_revoke_beta_user(auth_env):
    client = TestClient(_app())
    _seed_users(client)
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "owner@aethos.test", "password": "supersecret123"},
    )
    grant = client.post(
        "/api/v1/aethos-identity/admin/users/beta@aethos.test/grant",
        json={"status": "trial", "plan": "beta", "trial_days": 30},
    ).json()
    assert grant["ok"] is True
    assert grant["status"] == "trial"
    revoke = client.post("/api/v1/aethos-identity/admin/users/beta@aethos.test/revoke").json()
    assert revoke["ok"] is True

    beta = TestClient(_app())
    login = beta.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@aethos.test", "password": "betapass12345"},
    )
    assert login.json()["ok"] is False
    assert login.json()["error"] == "access_revoked"


def test_expired_entitlement_blocks_request_and_kills_session(auth_env):
    client = TestClient(_app())
    _seed_users(client)
    beta = TestClient(_app())
    beta.post(
        "/api/v1/aethos-identity/login",
        json={"email": "beta@aethos.test", "password": "betapass12345"},
    )
    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["beta@aethos.test"]["access_expires_at"] = time.time() - 5
    store_path.write_text(json.dumps(store))

    blocked = beta.get("/api/v1/aethos-identity/session")
    assert blocked.status_code == 403
    assert blocked.json()["error"] == "access_expired"
    assert blocked.json()["authenticated"] is False


def test_owner_never_blocked_by_entitlement(auth_env, monkeypatch):
    client = TestClient(_app())
    _seed_users(client)
    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["owner@aethos.test"]["status"] = "expired"
    store_path.write_text(json.dumps(store))

    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "owner@aethos.test", "password": "supersecret123"},
    )
    assert client.get("/api/v1/aethos-identity/session").status_code == 200


def test_version_endpoint(auth_env):
    from aethos_core.api.routes.health import router as health_router

    app = FastAPI()
    app.include_router(health_router, prefix="/api/v1")
    client = TestClient(app)
    data = client.get("/api/v1/version").json()
    assert "version" in data
    assert data["min_supported"] == ""


def test_git_sha_version_from_railway_env(auth_env, monkeypatch):
    monkeypatch.setenv("RAILWAY_GIT_COMMIT_SHA", "f7952ea")
    get_settings.cache_clear()
    from aethos_core.api.routes.health import get_app_version

    info = get_app_version()
    assert info["version"] == "f7952ea"
    assert info["min_supported"] == ""


def test_billing_webhook_disabled_by_default(auth_env):
    client = TestClient(_app())
    resp = client.post(
        "/api/v1/aethos-identity/billing/webhook",
        json={"subscription_status": "active", "customer_email": "beta@aethos.test"},
    )
    assert resp.json()["ok"] is False
    assert resp.json()["error"] == "billing_disabled"
