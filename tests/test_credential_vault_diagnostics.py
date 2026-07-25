# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_credential_vault_diagnostics_endpoint():
    from aethos_core.api.main import app

    client = TestClient(app)
    r = client.get("/api/v1/connections/diagnostics")
    assert r.status_code == 200
    body = r.json()
    assert "credential_vault" in body
    vault = body["credential_vault"]
    assert "available" in vault
    assert "dependencies" in vault
    assert "cryptography" in vault["dependencies"]
