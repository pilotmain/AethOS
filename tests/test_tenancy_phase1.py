# SPDX-License-Identifier: Apache-2.0
"""Phase 1 multi-tenancy: tenant context, shared-mode auth, self-signup, and the
Correction 1 invariant — detached work (durable jobs, arbiter fan-out) resolves
its *owning* tenant, never the request ContextVar or a global.

All deterministic: no real LLM calls, no network. Flag-off paths assert
byte-for-byte single-tenant behavior (tenant == "default").
"""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest

from aethos_core import config as config_mod
from aethos_core.tenancy import (
    DEFAULT_TENANT,
    get_current_tenant,
    normalize_tenant,
    reset_current_tenant,
    resolve_tenant,
    set_current_tenant,
    tenant_scope,
)


@pytest.fixture(autouse=True)
def _clear_settings():
    config_mod.get_settings.cache_clear()
    yield
    config_mod.get_settings.cache_clear()


# ───────────────────────────── core context ──────────────────────────────────


def test_default_tenant_when_unbound():
    assert get_current_tenant() == DEFAULT_TENANT


def test_set_reset_roundtrip():
    token = set_current_tenant("alice@example.com")
    try:
        assert get_current_tenant() == "alice@example.com"
    finally:
        reset_current_tenant(token)
    assert get_current_tenant() == DEFAULT_TENANT


def test_tenant_scope_nested_and_restore():
    with tenant_scope("alice"):
        assert get_current_tenant() == "alice"
        with tenant_scope("bob"):
            assert get_current_tenant() == "bob"
        assert get_current_tenant() == "alice"
    assert get_current_tenant() == DEFAULT_TENANT


def test_normalize_tenant():
    assert normalize_tenant(None) == DEFAULT_TENANT
    assert normalize_tenant("") == DEFAULT_TENANT
    assert normalize_tenant("   ") == DEFAULT_TENANT
    assert normalize_tenant("Alice@Example.COM") == "alice@example.com"


def test_resolve_prefers_explicit_over_contextvar():
    with tenant_scope("bob"):
        # An explicit stamp (e.g. a job's tenant_id) wins over the ambient context.
        assert resolve_tenant("alice") == "alice"
        # No explicit stamp ⇒ fall back to the ambient request tenant.
        assert resolve_tenant(None) == "bob"
        # An explicit "default" is treated as "unstamped" → ambient wins.
        assert resolve_tenant(DEFAULT_TENANT) == "bob"


# ─────────────────────── request → tenant resolution ─────────────────────────


def _fake_request(user):
    return SimpleNamespace(state=SimpleNamespace(user=user))


def test_tenant_for_request_flag_off_is_default(monkeypatch):
    from aethos_core.tenancy.middleware import tenant_for_request

    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    req = _fake_request({"user_id": "alice@example.com"})
    assert tenant_for_request(req) == DEFAULT_TENANT


def test_tenant_for_request_flag_on_uses_user(monkeypatch):
    from aethos_core.tenancy.middleware import tenant_for_request

    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    config_mod.get_settings.cache_clear()
    req = _fake_request({"user_id": "alice@example.com"})
    assert tenant_for_request(req) == "alice@example.com"


def test_tenant_for_request_flag_on_anonymous_is_default(monkeypatch):
    from aethos_core.tenancy.middleware import tenant_for_request

    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    config_mod.get_settings.cache_clear()
    req = _fake_request(None)
    assert tenant_for_request(req) == DEFAULT_TENANT


# ───────────────────── shared-mode auth enforcement (fail closed) ─────────────


def _run_auth_mw(path: str):
    from aethos_core.api.routes.aethos_identity import auth_session_middleware

    req = SimpleNamespace(
        method="POST",
        url=SimpleNamespace(path=path),
        cookies={},
        state=SimpleNamespace(),
    )

    async def call_next(_req):
        return "PASSED_THROUGH"

    return asyncio.run(auth_session_middleware(req, call_next))


def test_multi_tenant_requires_auth_even_if_auth_disabled(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    result = _run_auth_mw("/api/v1/chat")
    # No session cookie ⇒ rejected (fail closed), not passed through.
    assert getattr(result, "status_code", None) == 401


def test_single_tenant_no_auth_passes_through(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    assert _run_auth_mw("/api/v1/chat") == "PASSED_THROUGH"


# ─────────────────────────── self-service signup ─────────────────────────────


@pytest.fixture
def _auth_store(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    config_mod.get_settings.cache_clear()
    yield
    config_mod.get_settings.cache_clear()


def _mock_request():
    from unittest.mock import MagicMock

    req = MagicMock()
    req.headers = {}
    return req


def test_self_signup_disabled_by_default(_auth_store, monkeypatch):
    from starlette.responses import Response

    from aethos_core.api.routes.aethos_identity import RegisterIn, register_api

    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    out = register_api(RegisterIn(email="a@example.com", password="securepass123"), _mock_request(), Response())
    assert out == {"ok": False, "error": "signup_disabled"}


def test_self_signup_creates_operator_only(_auth_store, monkeypatch):
    from starlette.responses import Response

    from aethos_core.api.routes.aethos_identity import RegisterIn, register_api

    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("SENDGRID_API_KEY", "test-key")
    config_mod.get_settings.cache_clear()

    out = register_api(
        RegisterIn(email="Alice@Example.com", password="hunter2hunter22"),
        _mock_request(),
        Response(),
    )
    assert out["ok"] is True
    assert out["user"]["roles"] == ["tenant_admin"]

    # Weak password rejected.
    weak = register_api(RegisterIn(email="bob@example.com", password="short"), _mock_request(), Response())
    assert weak["ok"] is False
    assert weak["error"] == "weak_password"

    # Duplicate email rejected.
    dup = register_api(
        RegisterIn(email="alice@example.com", password="hunter2hunter22"),
        _mock_request(),
        Response(),
    )
    assert dup == {"ok": False, "error": "email_taken"}


# ──────────── Correction 1: detached work resolves its OWNING tenant ──────────


def test_durable_job_stamped_with_current_tenant(tmp_path, monkeypatch):
    from aethos_core.jobs import job_state

    monkeypatch.setattr(job_state, "_root", lambda: tmp_path)
    with tenant_scope("alice@example.com"):
        job = job_state.create_job_record(job_type="noop", session_id="s1")
    assert job["tenant_id"] == "alice@example.com"


def test_durable_job_default_tenant_when_unbound(tmp_path, monkeypatch):
    from aethos_core.jobs import job_state

    monkeypatch.setattr(job_state, "_root", lambda: tmp_path)
    job = job_state.create_job_record(job_type="noop", session_id="s1")
    assert job["tenant_id"] == DEFAULT_TENANT


def test_detached_job_resolves_owning_tenant_not_ambient(tmp_path, monkeypatch):
    """A durable job created by tenant 'alice' must resolve 'alice' inside its
    detached embedded runner — even if the surrounding context belongs to 'bob'
    and even though the runner is a background thread with no request context."""
    from aethos_core.jobs import job_state, trigger_adapter

    monkeypatch.setattr(job_state, "_root", lambda: tmp_path)

    # alice creates the job.
    with tenant_scope("alice@example.com"):
        job = job_state.create_job_record(job_type="noop", session_id="s1")

    seen: dict[str, str] = {}

    def _fake_handler(j):
        seen["tenant"] = get_current_tenant()
        return {"ok": True}

    monkeypatch.setattr(trigger_adapter, "_run_job_handler", _fake_handler)
    monkeypatch.setattr(trigger_adapter, "_complete_job", lambda *a, **k: None)

    # Execute the job while the ambient context belongs to a DIFFERENT tenant.
    with tenant_scope("bob@example.com"):
        trigger_adapter._embedded_execute(job["job_id"])

    assert seen["tenant"] == "alice@example.com"


def test_arbiter_sync_complete_reestablishes_owning_tenant(monkeypatch):
    """The arbiter's executor-thread completion must resolve the stamped tenant,
    not the ambient/request one (the thread doesn't inherit the ContextVar)."""
    from aethos_core.arbiter import dispatcher

    seen: dict[str, str] = {}

    class _Result:
        text = "ok"
        input_tokens = 1
        output_tokens = 1
        used_llm = True

    def _fake_complete(*args, **kwargs):
        seen["tenant"] = get_current_tenant()
        return _Result()

    monkeypatch.setattr(
        "aethos_core.provider.completion._complete_one_attempt", _fake_complete
    )

    with tenant_scope("bob@example.com"):
        dispatcher._sync_complete("openai", "gpt-x", "hi", "alice@example.com")

    assert seen["tenant"] == "alice@example.com"


def test_arbiter_session_stamps_tenant(monkeypatch):
    """run_arbiter_session stamps the owning tenant on the session even on the
    deterministic disabled path (no LLM calls)."""
    monkeypatch.setenv("ARBITER_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    from aethos_core.arbiter.service import run_arbiter_session

    with tenant_scope("alice@example.com"):
        session = asyncio.run(run_arbiter_session("hello", chat_session_id="c1"))
    assert session.tenant_id == "alice@example.com"
    assert session.to_dict()["tenant_id"] == "alice@example.com"
