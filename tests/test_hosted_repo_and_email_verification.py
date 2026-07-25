# SPDX-License-Identifier: Apache-2.0
"""Hosted repo substrate + email verification gates."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _clear_settings(monkeypatch, tmp_path):
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("REMOTE_WORKSPACE_CACHE_DIR", str(tmp_path / "remote_cache"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_parse_github_repository():
    from aethos_core.remote_workspace.github_clone import parse_github_repository

    assert parse_github_repository("pilotmain/AethOS") == "pilotmain/AethOS"
    assert parse_github_repository("https://github.com/pilotmain/AethOS") == "pilotmain/AethOS"
    assert parse_github_repository("not-a-repo") is None


def test_email_verification_required_on_hosted(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    get_settings.cache_clear()
    from aethos_core.auth.email_verification import email_verification_required

    assert email_verification_required() is True


def test_email_verification_skipped_on_local(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    get_settings.cache_clear()
    from aethos_core.auth.email_verification import email_verification_required

    assert email_verification_required() is False


def test_register_workspace_rejects_local_path_on_hosted(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("LOCAL_WORKSPACE_REGISTRY_DIR", "/tmp/ws-test")
    get_settings.cache_clear()
    from aethos_core.local_workspace.registry import register_workspace

    with pytest.raises(ValueError, match="hosted deployment"):
        register_workspace(path="/Users/me/project")


def test_register_fails_without_mailer_on_hosted(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()

    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    res = client.post(
        "/api/v1/aethos-identity/register",
        json={"email": "new@example.com", "password": "securepass123", "name": "New"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is False
    assert body.get("error") == "mailer_not_configured"


def _stub_request(path: str = "/api/v1/aethos-identity/register", host: str = "pilotmain.com"):
    import types

    return types.SimpleNamespace(url=types.SimpleNamespace(path=path), headers={"host": host})


def test_verify_url_includes_aethos_base_path_on_hosted_bare_origin(monkeypatch):
    """Regression: PUBLIC_APP_BASE_URL set to a bare origin (no path) must still produce
    https://pilotmain.com/aethos/verify-email — not a 404 at /verify-email."""
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("PUBLIC_APP_BASE_URL", "https://pilotmain.com")
    get_settings.cache_clear()
    from aethos_core.auth.email_verification import build_verification_url

    url = build_verification_url(_stub_request(), "tok123")
    assert url == "https://pilotmain.com/aethos/verify-email?token=tok123"


def test_verify_url_no_duplicate_aethos_when_base_url_has_path(monkeypatch):
    """PUBLIC_APP_BASE_URL already containing /aethos must not double to /aethos/aethos."""
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("PUBLIC_APP_BASE_URL", "https://pilotmain.com/aethos")
    get_settings.cache_clear()
    from aethos_core.auth.email_verification import build_verification_url

    url = build_verification_url(_stub_request(), "tok123")
    assert url == "https://pilotmain.com/aethos/verify-email?token=tok123"
    assert "/aethos/aethos" not in url


def test_verify_url_no_base_path_on_local(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("PUBLIC_APP_BASE_URL", "http://localhost:3000")
    get_settings.cache_clear()
    from aethos_core.auth.email_verification import build_verification_url

    url = build_verification_url(_stub_request(host="localhost:3000"), "tok123")
    assert url == "http://localhost:3000/verify-email?token=tok123"
