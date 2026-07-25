# SPDX-License-Identifier: Apache-2.0
"""Transactional mailer diagnostics and error surfacing."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

import pytest

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _settings(tmp_path, monkeypatch):
    monkeypatch.setenv("AUTH_STORE_DIR", str(tmp_path / "auth"))
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_hosted_requires_email_from(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "hosted")
    monkeypatch.setenv("EMAIL_FROM", "")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key_1234567890")  # gitleaks:allow - fixture
    get_settings.cache_clear()

    from aethos_core.auth.transactional_email import resolve_from_address

    addr, err = resolve_from_address()
    assert addr is None
    assert err is not None
    assert err.get("ok") is False
    assert "EMAIL_FROM" in str(err.get("detail") or "")


def test_resend_failure_surfaces_provider_detail(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("EMAIL_FROM", "ops@verified.example.com")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key_1234567890")  # gitleaks:allow - fixture
    get_settings.cache_clear()

    body = json.dumps({"message": "The pilotmain.com domain is not verified"}).encode()
    err = HTTPError(
        url="https://api.resend.com/emails",
        code=403,
        msg="Forbidden",
        hdrs=None,
        fp=BytesIO(body),
    )

    with patch("aethos_core.auth.transactional_email.urlopen", side_effect=err):
        from aethos_core.auth.transactional_email import send_transactional_email

        result = send_transactional_email("user@example.com", "Test", "body")

    assert result.get("ok") is False
    assert result.get("provider") == "resend"
    assert result.get("status") == 403
    detail = str(result.get("detail") or "")
    assert "403" in detail
    assert "not verified" in detail.lower()
    assert "re_test" not in detail
    assert result.get("hint")


def test_actionable_hint_invalid_key():
    from aethos_core.auth.transactional_email import _actionable_hint

    hint = _actionable_hint("resend 401: unauthorized")
    assert hint is not None
    assert "RESEND_API_KEY" in hint


def test_actionable_hint_cloudflare_1010_not_api_key():
    from aethos_core.auth.transactional_email import _actionable_hint

    hint = _actionable_hint("resend 403: error code: 1010")
    assert hint is not None
    assert "CDN" in hint or "Cloudflare" in hint
    assert "not an API key" in hint
    assert "RESEND_API_KEY" not in hint


def test_resend_request_includes_user_agent(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_MODE", "local")
    monkeypatch.setenv("EMAIL_FROM", "ops@verified.example.com")
    monkeypatch.setenv("RESEND_API_KEY", "re_test_key_1234567890")  # gitleaks:allow - fixture
    get_settings.cache_clear()

    captured: list[dict[str, str]] = []

    def fake_urlopen(req, timeout=20):
        captured.append(dict(req.header_items()))
        from unittest.mock import MagicMock

        resp = MagicMock()
        resp.status = 200
        resp.read.return_value = b"{}"
        resp.__enter__ = lambda s: s
        resp.__exit__ = MagicMock(return_value=False)
        return resp

    with patch("aethos_core.auth.transactional_email.urlopen", side_effect=fake_urlopen):
        from aethos_core.auth.transactional_email import _MAILER_USER_AGENT, send_transactional_email

        result = send_transactional_email("user@example.com", "Test", "body")

    assert result.get("ok") is True
    assert captured
    headers = {k.lower(): v for k, v in captured[0].items()}
    assert headers.get("user-agent") == _MAILER_USER_AGENT
    assert headers.get("accept") == "application/json"


def test_mailer_test_endpoint_requires_session(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    monkeypatch.setenv("AUTH_ENABLED", "true")
    get_settings.cache_clear()

    from fastapi.testclient import TestClient

    from aethos_core.api.main import app

    client = TestClient(app)
    res = client.post(
        "/api/v1/aethos-identity/mailer-test",
        json={"to": "ops@example.com"},
    )
    assert res.status_code == 401
