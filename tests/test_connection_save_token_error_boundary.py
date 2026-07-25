# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_connection_save_token_error_boundary():
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.api.routes.connections.get_credential_vault",
        side_effect=RuntimeError("vault exploded"),
    ):
        with patch(
            "aethos_core.api.routes.connections.get_credential_vault_diagnostics",
            return_value={"available": True, "dependencies": {"cryptography": "installed"}},
        ):
            r = client.post(
                "/api/v1/connections/vercel/credentials",
                json={"label": "Test", "token": "vercel_test_token_abcdefgh", "type": "api_token"},
            )
    assert r.status_code == 500
    body = r.json()
    assert body["ok"] is False
    assert body["code"] == "CREDENTIAL_SAVE_FAILED"
    assert "vercel_test_token" not in body["detail"]
