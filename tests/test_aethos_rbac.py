# SPDX-License-Identifier: Apache-2.0
"""§7 RBAC — permission model, middleware enforcement, user/role admin."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

import aethos_core.api.routes.aethos_identity as ident
from aethos_core.config import get_settings
from aethos_core.security import rbac


def test_permission_model():
    assert rbac.OWN_PLATFORM not in rbac.permissions_for_roles(["admin"])
    assert rbac.MANAGE_USERS in rbac.permissions_for_roles(["admin"])
    assert rbac.MANAGE_GOVERNANCE in rbac.permissions_for_roles(["admin"])
    assert rbac.MANAGE_GOVERNANCE not in rbac.permissions_for_roles(["operator"])
    assert rbac.permissions_for_roles(["read_only"]) == {rbac.READ}
    assert rbac.APPROVE in rbac.permissions_for_roles(["approver"])
    assert rbac.MUTATE not in rbac.permissions_for_roles(["approver"])
    assert rbac.MUTATE in rbac.permissions_for_roles(["operator"])


def test_required_permission_mapping():
    assert rbac.required_permission("GET", "/api/v1/anything") == rbac.READ
    assert rbac.required_permission("POST", "/api/v1/mutations/x") == rbac.MUTATE
    assert rbac.required_permission("POST", "/api/v1/foo/approve") == rbac.APPROVE
    assert rbac.required_permission("POST", "/api/v1/agents/spawn") == rbac.SPAWN_AGENT
    assert rbac.required_permission("POST", "/api/v1/aethos-identity/users/roles") == rbac.MANAGE_USERS
    assert rbac.required_permission("GET", "/api/v1/governance/diagnostics") == rbac.MANAGE_GOVERNANCE
    assert rbac.required_permission("POST", "/api/v1/governance/overrides") == rbac.MANAGE_GOVERNANCE


@pytest.fixture
def auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")

    @app.post("/api/v1/mutations/run")
    def _mutate(request: Request):
        return {"ok": True}

    return app


def _seed_admin_and_login(client):
    client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    )
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "admin@aethos.test", "password": "supersecret123"},
    )


def test_read_only_user_cannot_mutate(auth_env):
    admin = TestClient(_app())
    _seed_admin_and_login(admin)
    # Admin creates a read-only user by direct store write (no self-serve signup).
    import json

    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["viewer@aethos.test"] = {
        "user_id": "viewer@aethos.test",
        "email": "viewer@aethos.test",
        "roles": ["read_only"],
        "auth": "local",
        "password": ident.hash_password("viewerpass1234"),
    }
    store_path.write_text(json.dumps(store))

    viewer = TestClient(_app())
    viewer.post(
        "/api/v1/aethos-identity/login",
        json={"email": "viewer@aethos.test", "password": "viewerpass1234"},
    )
    # read_only can read but not mutate.
    assert viewer.get("/api/v1/aethos-identity/session").status_code == 200
    blocked = viewer.post("/api/v1/mutations/run")
    assert blocked.status_code == 403
    assert blocked.json()["required_permission"] == rbac.MUTATE


def test_admin_can_mutate_and_manage_roles(auth_env):
    client = TestClient(_app())
    _seed_admin_and_login(client)
    assert client.post("/api/v1/mutations/run").status_code == 200
    # Create a second user, then promote.
    import json

    store_path = ident._store_path()
    store = json.loads(store_path.read_text())
    store["users"]["op@aethos.test"] = {
        "user_id": "op@aethos.test",
        "email": "op@aethos.test",
        "roles": ["read_only"],
        "auth": "local",
        "password": ident.hash_password("oppass12345"),
    }
    store_path.write_text(json.dumps(store))
    resp = client.post(
        "/api/v1/aethos-identity/users/roles",
        json={"email": "op@aethos.test", "roles": ["operator"]},
    ).json()
    assert resp["ok"] and resp["roles"] == ["operator"]


def test_cannot_remove_last_admin(auth_env):
    client = TestClient(_app())
    _seed_admin_and_login(client)
    resp = client.post(
        "/api/v1/aethos-identity/users/roles",
        json={"email": "admin@aethos.test", "roles": ["operator"]},
    ).json()
    assert resp["ok"] is False
    assert resp["error"] == "cannot_remove_last_admin"


def test_read_only_lock_not_overridden_by_account_ownership(monkeypatch):
    """A user the platform owner restricts to read_only stays read-only even in their
    own account — account-owner elevation must not silently re-grant write/approve."""
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()
    try:
        ro = {"email": "bob@x.com", "user_id": "bob@x.com", "roles": ["read_only"]}
        perms = rbac.permissions_for_user(ro)
        assert perms == {rbac.READ}, f"read_only owner leaked perms: {perms}"
        # An operator owner, by contrast, IS elevated to approve their own work.
        op = {"email": "alice@x.com", "user_id": "alice@x.com", "roles": ["operator"]}
        assert rbac.APPROVE in rbac.permissions_for_user(op)
    finally:
        get_settings.cache_clear()
