# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_connection_save_token_route_exists():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.post(
        "/api/v1/connections/vercel/credentials",
        json={"label": "Test", "token": "short"},
    )
    assert r.status_code == 422
