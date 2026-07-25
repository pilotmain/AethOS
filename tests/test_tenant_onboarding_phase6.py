# SPDX-License-Identifier: Apache-2.0
"""Phase 6 — tenant onboarding wizard, metering quotas, release-gate helpers."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.tenancy import tenant_scope


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "creds"))
    monkeypatch.setenv("RUNTIME_CONFIG_DIR", str(tmp_path / "runtime_config"))
    monkeypatch.setenv("TENANT_DATA_DIR", str(tmp_path / "tenant_data"))
    get_settings.cache_clear()
    from aethos_core.runtime_config import runtime_config_store as config_store
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests
    from aethos_core.tenancy.tenant_data_store import reset_for_tests as reset_tenant_data

    reset_credential_vault_for_tests()
    config_store.reset_for_tests()
    reset_tenant_data()
    yield
    reset_credential_vault_for_tests()
    config_store.reset_for_tests()
    reset_tenant_data()
    get_settings.cache_clear()


def _enable_multi_tenant(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()


def test_anthropic_vault_key_counts_for_onboarding_credentials(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.tenancy.tenant_onboarding import build_tenant_onboarding_state

    vault = __import__(
        "aethos_core.security.credential_vault", fromlist=["get_credential_vault"]
    ).get_credential_vault()
    with tenant_scope("alice@example.com"):
        vault.store_api_token(provider="anthropic", label="alice", token="sk-ant-test-key-99")
        state = build_tenant_onboarding_state()
        cred = next(s for s in state["steps"] if s["id"] == "credentials")
        models = next(s for s in state["steps"] if s["id"] == "models")
        assert cred["completed"] is True
        assert models["completed"] is True


def test_onboarding_required_until_credentials_and_features(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.tenancy.tenant_onboarding import build_tenant_onboarding_state, mark_onboarding_complete

    with tenant_scope("alice@example.com"):
        state = build_tenant_onboarding_state()
        assert state["enabled"] is True
        assert state["required"] is True
        assert state["complete"] is False

        vault = __import__(
            "aethos_core.security.credential_vault", fromlist=["get_credential_vault"]
        ).get_credential_vault()
        vault.store_api_token(provider="openai", label="alice", token="sk-alice-test-key-99")

        from aethos_core.runtime_config.effective_settings import set_effective_setting

        set_effective_setting("USE_REAL_LLM", True, actor="alice@example.com")
        state2 = build_tenant_onboarding_state()
        assert state2["complete"] is True
        assert state2["required"] is False

        mark_onboarding_complete()
        state3 = build_tenant_onboarding_state()
        assert state3["complete"] is True


def test_operator_tenant_skips_onboarding(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    from aethos_core.tenancy import DEFAULT_TENANT
    from aethos_core.tenancy.tenant_onboarding import build_tenant_onboarding_state

    with tenant_scope(DEFAULT_TENANT):
        state = build_tenant_onboarding_state()
        assert state["operator_exempt"] is True
        assert state["complete"] is True


def test_llm_token_quota_blocks_non_operator(monkeypatch):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("TENANT_LLM_TOKENS_PER_DAY", "100")
    get_settings.cache_clear()
    from aethos_core.tenancy.tenant_metering import check_llm_token_quota, record_llm_tokens

    with tenant_scope("alice@example.com"):
        assert check_llm_token_quota()[0] is True
        record_llm_tokens(150)
        allowed, retry = check_llm_token_quota()
        assert allowed is False
        assert retry > 0

    from aethos_core.tenancy import DEFAULT_TENANT

    with tenant_scope(DEFAULT_TENANT):
        record_llm_tokens(500)
        assert check_llm_token_quota()[0] is True


def test_tenant_onboarding_api_authenticated(monkeypatch, tmp_path):
    _enable_multi_tenant(monkeypatch)
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()

    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    import aethos_core.api.routes.aethos_identity as ident
    from aethos_core.api.routes import tenant_onboarding as onboarding_routes
    from aethos_core.security import rbac
    from aethos_core.tenancy.middleware import tenant_context_middleware

    app = FastAPI()
    app.middleware("http")(tenant_context_middleware)
    app.middleware("http")(rbac.rbac_middleware)
    app.middleware("http")(ident.auth_session_middleware)
    app.include_router(ident.router, prefix="/api/v1")
    app.include_router(onboarding_routes.router, prefix="/api/v1")

    client = TestClient(app)
    client.post(
        "/api/v1/aethos-identity/bootstrap",
        json={"email": "alice@aethos.test", "password": "supersecret123"},
    )
    client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "alice@aethos.test", "password": "supersecret123"},
    )
    resp = client.get("/api/v1/tenancy/onboarding")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("enabled") is True
    assert body.get("tenant_id") == "alice@aethos.test"
