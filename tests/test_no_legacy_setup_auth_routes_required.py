# SPDX-License-Identifier: Apache-2.0

from fastapi.testclient import TestClient


def test_legacy_routes_return_deprecated_shims():
    from aethos_core.api.main import app

    client = TestClient(app)
    for path in (
        "/api/setup-creds",
        "/api/v1/auth/ping",
        "/api/v1/setup/auth-diagnostics",
    ):
        res = client.get(path)
        assert res.status_code == 200, path
        body = res.json()
        assert body.get("ok") is True
        assert body.get("deprecated") is True
