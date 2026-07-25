# SPDX-License-Identifier: Apache-2.0
"""Channel webhooks must stay reachable when enterprise auth is on."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings


@pytest.fixture
def shared_auth_env(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_telegram_webhook_open_when_auth_enabled(shared_auth_env):
    from aethos_core.api.main import app

    with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
        with patch(
            "aethos_core.channels.telegram.telegram_router.handle_telegram_update",
            return_value={"ok": True, "skipped": True},
        ):
            with TestClient(app) as client:
                assert client.get("/api/v1/observability/metering").status_code == 401
                r = client.post("/api/v1/channels/telegram/webhook", json={})
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_telegram_webhook_binds_vault_owner_tenant(shared_auth_env):
    from aethos_core.api.main import app
    from aethos_core.security.credential_vault import CredentialVault

    owner = "tenant-a@example.com"
    seen: list[str] = []

    def _capture(update):
        from aethos_core.tenancy import get_current_tenant

        seen.append(get_current_tenant())
        return {"ok": True, "skipped": True}

    # Patch the class method so it holds across any vault instance the app startup
    # (re)creates — the global singleton is replaced during deferred startup.
    with patch.object(CredentialVault, "find_unique_owner_for_provider", return_value=owner):
        with patch("aethos_core.channels.telegram.telegram_runtime.telegram_configured", return_value=True):
            with patch(
                "aethos_core.channels.telegram.telegram_router.handle_telegram_update",
                side_effect=_capture,
            ):
                with TestClient(app) as client:
                    r = client.post("/api/v1/channels/telegram/webhook", json={})
    assert r.status_code == 200
    assert seen == [owner]
