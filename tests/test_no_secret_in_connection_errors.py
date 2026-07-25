# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient


def test_no_secret_in_connection_errors():
    from aethos_core.api.main import app

    token = "vercel_test_token_secret_leak_1234567890"
    client = TestClient(app)
    with patch(
        "aethos_core.api.routes.connections.get_credential_vault",
        side_effect=RuntimeError(f"boom with {token}"),
    ):
        with patch(
            "aethos_core.api.routes.connections.get_credential_vault_diagnostics",
            return_value={"available": True, "dependencies": {"cryptography": "installed"}},
        ):
            r = client.post(
                "/api/v1/connections/vercel/credentials",
                json={"label": "Test", "token": token, "type": "api_token"},
            )
    body = r.json()
    assert token not in str(body)
