# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_no_vercel_token_leakage_in_connection_api(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    from aethos_core.api.main import app

    token = "vercel_test_token_leak_check_1234567890"
    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Vercel token validated."},
    ):
        r = client.post(
            "/api/v1/connections/vercel/credentials",
            json={"type": "api_token", "label": "Primary", "token": token},
        )
    body = r.json()
    serialized = str(body)
    assert token not in serialized
    listed = client.get("/api/v1/connections/vercel").json()
    assert token not in str(listed)
    reset_credential_vault_for_tests()
