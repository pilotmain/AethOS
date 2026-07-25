# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def test_vercel_api_token_connection_save_and_list(vault_env):
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Vercel token validated."},
    ):
        r = client.post(
            "/api/v1/connections/vercel/credentials",
            json={"type": "api_token", "label": "Primary", "token": "vercel_test_token_abcdefgh"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "vercel_test_token_abcdefgh" not in str(body)
    cred = body["credential"]
    assert cred["credential_id"].startswith("cred-")
    assert cred["masked_identifier"]

    listed = client.get("/api/v1/connections/vercel").json()
    assert listed["connected_methods"]["api_token"] == "validated"
    assert listed["credentials"]
