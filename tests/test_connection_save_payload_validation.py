# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_connection_save_payload_accepts_secret_alias():
    from aethos_core.api.main import app
    from unittest.mock import patch

    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Vercel token validated."},
    ):
        r = client.post(
            "/api/v1/connections/vercel/credentials",
            json={
                "label": "Test",
                "secret": "vercel_test_token_abcdefgh",
                "type": "api_token",
            },
        )
    assert r.status_code == 200
    assert r.json()["ok"] is True
