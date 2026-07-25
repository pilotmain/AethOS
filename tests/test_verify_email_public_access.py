# SPDX-License-Identifier: Apache-2.0
"""Regression: email verification must work without a session."""

from __future__ import annotations

import re
import time
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.api.routes import aethos_identity as ident
from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_COOKIE_SECURE", "false")
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("AUTH_SELF_SIGNUP_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _mock_request(host: str = "pilotmain.com", proto: str = "https", path: str = "/api/v1/aethos-identity/register"):
    req = MagicMock()
    req.url.path = path
    req.headers = {"host": host, "x-forwarded-proto": proto}
    return req


def _seed_pending_user(token: str = "verify-token-abc") -> str:
    user_id = "verify@example.com"
    with ident._LOCK:
        store = ident._load_store()
        store["users"][user_id] = {
            "user_id": user_id,
            "email": "verify@example.com",
            "auth": "local",
            "password": ident.hash_password("securepass123"),
            "roles": ["operator"],
            "verification_token": token,
            "verification_expires": time.time() + 3600,
            "email_verified": False,
        }
        ident._save_store(store)
    return user_id


@pytest.mark.parametrize(
    ("public_url", "expected"),
    [
        (None, "https://pilotmain.com/aethos/verify-email"),
        ("https://pilotmain.com", "https://pilotmain.com/verify-email"),
        ("https://pilotmain.com/aethos", "https://pilotmain.com/aethos/verify-email"),
    ],
)
def test_build_verification_url_single_aethos_prefix(monkeypatch, public_url, expected):
    if public_url is None:
        monkeypatch.delenv("PUBLIC_APP_BASE_URL", raising=False)
    else:
        monkeypatch.setenv("PUBLIC_APP_BASE_URL", public_url)
    get_settings.cache_clear()

    from aethos_core.auth.email_verification import build_verification_url

    url = build_verification_url(_mock_request(), "tok-abc")
    assert url == f"{expected}?token=tok-abc"
    assert url.count("/aethos") == expected.count("/aethos")
    assert "localhost" not in url
    assert url.endswith("/verify-email?token=tok-abc")
    assert "/aethos/aethos" not in url


def test_public_app_base_splits_origin_and_path(monkeypatch):
    monkeypatch.setenv("PUBLIC_APP_BASE_URL", "https://pilotmain.com/aethos")
    get_settings.cache_clear()

    from aethos_core.auth.email_verification import (
        public_app_base,
        public_app_base_path,
        public_app_origin,
        verification_landing_path,
    )

    req = _mock_request(host="wrong.example.com")
    assert public_app_origin(req) == "https://pilotmain.com"
    assert public_app_base_path(req) == "/aethos"
    assert public_app_base(req) == "https://pilotmain.com/aethos"
    assert verification_landing_path(req) == "/aethos/verify-email"


def test_public_app_origin_hosted_never_localhost(monkeypatch):
    monkeypatch.delenv("PUBLIC_APP_BASE_URL", raising=False)
    get_settings.cache_clear()

    from aethos_core.auth.email_verification import build_verification_url

    req = _mock_request(host="localhost:8000")
    url = build_verification_url(req, "x")
    assert "localhost" not in url
    assert url.startswith("https://pilotmain.com/aethos/verify-email")


def test_verify_email_api_unauthenticated_succeeds():
    _seed_pending_user()
    client = TestClient(app)
    res = client.get("/api/v1/aethos-identity/verify-email", params={"token": "verify-token-abc"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is True
    assert body.get("email") == "verify@example.com"


def test_verify_then_login_without_prior_session():
    _seed_pending_user("login-after-verify")
    client = TestClient(app)
    verify = client.get(
        "/api/v1/aethos-identity/verify-email",
        params={"token": "login-after-verify"},
    )
    assert verify.json().get("ok") is True

    login = client.post(
        "/api/v1/aethos-identity/login",
        json={"email": "verify@example.com", "password": "securepass123"},
    )
    assert login.status_code == 200
    assert login.json().get("ok") is True


def test_verify_landing_path_not_requires_auth():
    _seed_pending_user("landing-token")
    client = TestClient(app)
    res = client.get("/verify-email", params={"token": "landing-token"}, follow_redirects=False)
    assert res.status_code != 401
    assert res.status_code in (200, 302, 307)
    if res.status_code in (302, 307):
        assert "token=landing-token" in res.headers.get("location", "")


def test_aethos_prefixed_verify_landing_not_requires_auth():
    client = TestClient(app)
    res = client.get("/aethos/verify-email", params={"token": "pref-token"}, follow_redirects=False)
    assert res.status_code != 401
    assert res.status_code in (200, 302, 307)


def test_open_path_allowlist_covers_prelogin_surfaces():
    from aethos_core.api.routes.aethos_identity import _is_open_path

    assert _is_open_path("/verify-email")
    assert _is_open_path("/aethos/verify-email")
    assert _is_open_path("/login")
    assert _is_open_path("/aethos/login")
    assert _is_open_path("/register")
    assert _is_open_path("/aethos/register")
    assert _is_open_path("/api/v1/aethos-identity/verify-email")
    assert _is_open_path("/api/v1/aethos-identity/resend-verification", "POST")
    assert _is_open_path("/api/v1/aethos-identity/sso/callback")
    assert not _is_open_path("/api/v1/chat")


def test_protected_route_still_requires_auth():
    client = TestClient(app)
    assert client.post("/api/v1/chat", json={"message": "hi", "session_id": "s1"}).status_code == 401


def test_public_app_url_idempotent_base_path(monkeypatch):
    monkeypatch.setenv("PUBLIC_APP_BASE_URL", "https://pilotmain.com/aethos")
    get_settings.cache_clear()

    from aethos_core.auth.email_verification import public_app_url

    url = public_app_url(_mock_request(), "/verify-email")
    assert url == "https://pilotmain.com/aethos/verify-email"
    assert not re.search(r"/aethos/aethos", url)
