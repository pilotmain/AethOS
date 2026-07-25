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


def test_railway_api_token_save_and_list(vault_env):
    import aethos_core.providers  # noqa: F401
    from aethos_core.providers.github.provider import ensure_github_registered
    from aethos_core.providers.railway.provider import ensure_railway_registered
    from aethos_core.providers.vercel.provider import ensure_vercel_registered

    ensure_vercel_registered()
    ensure_railway_registered()
    ensure_github_registered()
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_railway_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Railway account verified."},
    ):
        r = client.post(
            "/api/v1/connections/railway/credentials",
            json={"type": "api_token", "label": "Primary", "token": "railway_test_token_abcdefgh"},
        )
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "railway_test_token" not in str(body)

    listed = client.get("/api/v1/connections/railway").json()
    assert listed["connected_methods"]["api_token"] == "validated"


def test_github_api_token_save_and_list(vault_env):
    import aethos_core.providers  # noqa: F401
    from aethos_core.providers.github.provider import ensure_github_registered
    from aethos_core.providers.railway.provider import ensure_railway_registered
    from aethos_core.providers.vercel.provider import ensure_vercel_registered

    ensure_vercel_registered()
    ensure_railway_registered()
    ensure_github_registered()
    from aethos_core.api.main import app

    client = TestClient(app)
    with patch(
        "aethos_core.connections.credential_validation._validate_github_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "GitHub account verified (@acme)."},
    ):
        r = client.post(
            "/api/v1/connections/github/credentials",
            json={"type": "api_token", "label": "Primary", "token": "github_pat_test_token_ab"},
        )
    assert r.status_code == 200
    listed = client.get("/api/v1/connections/github").json()
    assert listed["connected_methods"]["api_token"] == "validated"
