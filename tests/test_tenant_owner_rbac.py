# SPDX-License-Identifier: Apache-2.0
"""Tenant owner vs platform owner — two-plane authority model."""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aethos_core.api.routes.aethos_identity as ident
from aethos_core.config import get_settings
from aethos_core.security import rbac
from aethos_core.tenancy.middleware import tenant_context_middleware


@pytest.fixture
def mt_auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("AUDIT_LEDGER_DIR", str(tmp_path / "audit"))
    monkeypatch.delenv("PLATFORM_OWNER_EMAILS", raising=False)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _app() -> FastAPI:
    app = FastAPI()
    app.middleware("http")(tenant_context_middleware)
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")
    return app


def test_existing_operator_account_is_tenant_owner_by_tenancy(mt_auth_env):
    """Real account shape: roles ``operator`` only, tenant == user_id — no migration required."""
    operator = {
        "user_id": "operator@example.com",
        "email": "operator@example.com",
        "roles": ["operator"],
    }
    assert rbac.is_tenant_owner(operator)
    perms = rbac.permissions_for_user(operator)
    assert rbac.APPROVE in perms
    path = "/api/v1/channels/pairing/approve"
    assert rbac.is_authorized(["operator"], "POST", path, user=operator)


def test_operator_accounts_own_distinct_tenants(mt_auth_env):
    bob = {"user_id": "bob@example.com", "email": "bob@example.com", "roles": ["operator"]}
    alice = {"user_id": "alice@example.com", "email": "alice@example.com", "roles": ["operator"]}
    assert rbac.is_tenant_owner(bob)
    assert rbac.is_tenant_owner(alice)
    assert rbac.tenant_for_user(bob) != rbac.tenant_for_user(alice)


def test_existing_operator_can_approve_own_pairing(mt_auth_env, tmp_path, monkeypatch):
    monkeypatch.setenv("CHANNEL_PAIRING_STORE_DIR", str(tmp_path / "pairing"))
    get_settings.cache_clear()

    from aethos_core.api.routes.channels import router as channels_router
    from aethos_core.channels.pairing_store import is_sender_allowed, request_pairing
    from aethos_core.tenancy import tenant_scope

    app = _app()
    app.include_router(channels_router, prefix="/api/v1")
    store_path = ident._store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)

    with tenant_scope("operator@example.com"):
        pairing = request_pairing("telegram", "sender-op", preview="hi")
    code = str(pairing["code"])

    store = {
        "users": {
            "operator@example.com": {
                "user_id": "operator@example.com",
                "email": "operator@example.com",
                "roles": ["operator"],
                "auth": "local",
                "password": ident.hash_password("operatorpass1234"),
                "status": "trial",
            }
        },
        "sessions": {},
    }
    store_path.write_text(json.dumps(store))

    client = TestClient(app)
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "operator@example.com", "password": "operatorpass1234"},
    )
    approved = client.post(
        "/api/v1/channels/pairing/approve",
        json={"channel": "telegram", "code": code},
    )
    assert approved.status_code == 200
    assert approved.json().get("ok") is True
    with tenant_scope("operator@example.com"):
        assert is_sender_allowed("telegram", "sender-op")


def test_doctor_migrates_primary_operator_to_tenant_admin(mt_auth_env, tmp_path):
    store_path = ident._store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)
    store_path.write_text(
        json.dumps(
            {
                "users": {
                    "operator@example.com": {
                        "user_id": "operator@example.com",
                        "email": "operator@example.com",
                        "roles": ["operator"],
                        "auth": "local",
                    }
                },
                "sessions": {},
            }
        )
    )
    loaded = ident._load_store()
    assert loaded["users"]["operator@example.com"]["roles"] == ["tenant_admin"]
    assert store_path.exists()
    persisted = json.loads(store_path.read_text())
    assert persisted["users"]["operator@example.com"]["roles"] == ["tenant_admin"]


def test_tenant_owner_has_approve_without_platform_owner(mt_auth_env):
    jeremy = {"user_id": "jeremy@example.com", "email": "jeremy@example.com", "roles": ["tenant_admin"]}
    assert rbac.is_tenant_owner(jeremy)
    perms = rbac.permissions_for_user(jeremy)
    assert rbac.APPROVE in perms
    assert rbac.MANAGE_USERS not in perms
    assert rbac.OWN_PLATFORM not in perms
    path = "/api/v1/channels/pairing/approve"
    assert rbac.is_authorized(["tenant_admin"], "POST", path, user=jeremy)


def test_platform_owner_is_narrow_cross_tenant_only(mt_auth_env, monkeypatch):
    monkeypatch.setenv("PLATFORM_OWNER_EMAILS", "owner@aethos.test")
    get_settings.cache_clear()
    owner = {"user_id": "owner@aethos.test", "email": "owner@aethos.test", "roles": ["operator"]}
    perms = rbac.permissions_for_user(owner)
    assert rbac.OWN_PLATFORM in perms
    assert rbac.MANAGE_USERS in perms
    assert rbac.APPROVE not in rbac.PLATFORM_OWNER_PERMISSIONS
    assert perms != set(rbac.ALL_PERMISSIONS)
    # Platform-plane grants alone do not include approve; tenant ownership may add it.
    assert rbac.is_tenant_owner(owner)
    assert rbac.APPROVE in perms


def test_tenant_owner_can_approve_own_pairing(mt_auth_env, tmp_path, monkeypatch):
    monkeypatch.setenv("CHANNEL_PAIRING_STORE_DIR", str(tmp_path / "pairing"))
    get_settings.cache_clear()

    from aethos_core.api.routes.channels import router as channels_router
    from aethos_core.channels.pairing_store import is_sender_allowed, request_pairing
    from aethos_core.tenancy import tenant_scope

    app = _app()
    app.include_router(channels_router, prefix="/api/v1")
    store_path = ident._store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)

    with tenant_scope("jeremy@example.com"):
        pairing = request_pairing("telegram", "sender-jeremy", preview="hi")
    code = str(pairing["code"])

    store = {
        "users": {
            "jeremy@example.com": {
                "user_id": "jeremy@example.com",
                "email": "jeremy@example.com",
                "roles": ["tenant_admin"],
                "auth": "local",
                "password": ident.hash_password("jeremypass12345"),
                "status": "trial",
            }
        },
        "sessions": {},
    }
    store_path.write_text(json.dumps(store))

    client = TestClient(app)
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "jeremy@example.com", "password": "jeremypass12345"},  # gitleaks:allow - fixture
    )
    approved = client.post(
        "/api/v1/channels/pairing/approve",
        json={"channel": "telegram", "code": code},
    )
    assert approved.status_code == 200
    assert approved.json().get("ok") is True
    with tenant_scope("jeremy@example.com"):
        assert is_sender_allowed("telegram", "sender-jeremy")


def test_tenant_b_cannot_approve_tenant_a_pairing(mt_auth_env, tmp_path, monkeypatch):
    monkeypatch.setenv("CHANNEL_PAIRING_STORE_DIR", str(tmp_path / "pairing"))
    get_settings.cache_clear()

    from aethos_core.api.routes.channels import router as channels_router
    from aethos_core.channels.pairing_store import request_pairing
    from aethos_core.tenancy import tenant_scope

    app = _app()
    app.include_router(channels_router, prefix="/api/v1")
    store_path = ident._store_path()
    store_path.parent.mkdir(parents=True, exist_ok=True)

    with tenant_scope("alice@example.com"):
        pairing = request_pairing("telegram", "sender-alice", preview="hi")
    code = str(pairing["code"])

    store = {
        "users": {
            "bob@example.com": {
                "user_id": "bob@example.com",
                "email": "bob@example.com",
                "roles": ["tenant_admin"],
                "auth": "local",
                "password": ident.hash_password("bobpass12345678"),
                "status": "trial",
            }
        },
        "sessions": {},
    }
    store_path.write_text(json.dumps(store))

    bob = TestClient(app)
    bob.post(
        "/api/v1/aethos-identity/login",
        json={"email": "bob@example.com", "password": "bobpass12345678"},  # gitleaks:allow - fixture
    )
    blocked = bob.post(
        "/api/v1/channels/pairing/approve",
        json={"channel": "telegram", "code": code},
    )
    assert blocked.status_code == 404
