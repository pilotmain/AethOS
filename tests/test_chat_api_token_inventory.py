# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "false")
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_chat_uses_api_token_without_browser(vault_env):
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Vercel token validated."},
    ):
        client.post(
            "/api/v1/connections/vercel/credentials",
            json={"type": "api_token", "label": "Primary", "token": "vercel_test_token_abcdefgh"},
        )
    r = client.post(
        "/api/v1/chat",
        json={"message": "show my Vercel apps", "session_id": "api-token-chat"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "created tracked job" in body["reply"].lower()
    assert "api token" in body["reply"].lower()
    assert body["intent"] == "vercel_readonly_job_created"
    assert (body.get("meta") or {}).get("auth_method") == "api_token"
