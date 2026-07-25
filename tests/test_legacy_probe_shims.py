# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_legacy_probe_shims_are_stable():
    from aethos_core.api.main import app

    client = TestClient(app)
    paths = (
        "/api/setup-creds",
        "/api/v1/auth/ping",
        "/api/v1/setup/auth-diagnostics",
    )
    for path in paths:
        first = client.get(path)
        second = client.get(path)
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == second.json()
