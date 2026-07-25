# SPDX-License-Identifier: Apache-2.0
"""Self-host single-user mode: no multi-tenant beta gate, no auth wall, and the
local operator owns their own instance — enforced even against a hosted-style .env."""

from __future__ import annotations

import pytest

from aethos_core.config import Settings, get_settings
from aethos_core.security import rbac


@pytest.fixture(autouse=True)
def _clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_self_host_forces_single_user_even_with_hosted_env(monkeypatch):
    monkeypatch.setenv("SELF_HOST", "true")
    # A hosted-style .env tries to turn the gate + auth wall back on...
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    s = Settings()
    assert s.self_host is True
    assert s.multi_tenant_enabled is False  # gate forced off
    assert s.auth_enabled is False  # wall forced off


def test_self_host_grants_owner_to_local_operator(monkeypatch):
    monkeypatch.setenv("SELF_HOST", "true")
    get_settings.cache_clear()
    # Single-user instance: owner rights regardless of email / PLATFORM_OWNER_EMAILS.
    assert rbac.is_platform_owner({"email": "anyone@local"}) is True
    assert rbac.is_platform_owner(None) is True


def test_hosted_mode_unchanged_when_self_host_off(monkeypatch):
    monkeypatch.delenv("SELF_HOST", raising=False)
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("PLATFORM_OWNER_EMAILS", "owner@x.com")
    s = Settings()
    assert s.self_host is False
    assert s.multi_tenant_enabled is True  # hosted gate preserved
    get_settings.cache_clear()
    # Owner is still email-gated in hosted mode (no blanket ownership).
    assert rbac.is_platform_owner({"email": "owner@x.com"}) is True
    assert rbac.is_platform_owner({"email": "random@x.com"}) is False
    assert rbac.is_platform_owner(None) is False
