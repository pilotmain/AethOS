# SPDX-License-Identifier: Apache-2.0
"""Per-tenant vault-backed IMAP credentials for workspace email."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings
from aethos_core.tenancy import tenant_scope


@pytest.fixture(autouse=True)
def _isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "creds"))
    get_settings.cache_clear()
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    yield
    reset_credential_vault_for_tests()
    get_settings.cache_clear()


def _fields() -> dict[str, str]:
    return {
        "imap_host": "imap.example.com",
        "imap_port": "993",
        "imap_user": "alice@example.com",
        "imap_password": "secret-app-pass",
        "imap_mailbox": "INBOX",
    }


def test_store_resolve_roundtrip():
    from aethos_core.workspace_suite.email_credentials import (
        email_has_vault_credentials,
        resolve_email_imap_connection,
        store_email_imap_credentials,
    )

    record = store_email_imap_credentials(label="Personal inbox", fields=_fields())
    assert record.provider == "email_imap"
    assert email_has_vault_credentials() is True
    conn = resolve_email_imap_connection()
    assert conn is not None
    assert conn["host"] == "imap.example.com"
    assert conn["user"] == "alice@example.com"
    assert conn["password"] == "secret-app-pass"
    assert conn["mailbox"] == "INBOX"
    assert conn["port"] == "993"


def test_store_requires_imap_password():
    from aethos_core.workspace_suite.email_credentials import EmailCredentialError, store_email_imap_credentials

    bad = dict(_fields())
    bad.pop("imap_password")
    with pytest.raises(EmailCredentialError):
        store_email_imap_credentials(label="x", fields=bad)


def test_secret_masked_in_public_dict():
    from aethos_core.workspace_suite.email_credentials import store_email_imap_credentials

    record = store_email_imap_credentials(label="inbox", fields=_fields())
    public = record.to_public_dict()
    assert "secret-app-pass" not in json.dumps(public)


def test_credentials_invisible_across_tenants(monkeypatch):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()

    from aethos_core.workspace_suite.email_credentials import (
        resolve_email_imap_connection,
        store_email_imap_credentials,
    )

    with tenant_scope("alice@example.com"):
        store_email_imap_credentials(label="A inbox", fields=_fields())
    with tenant_scope("bob@example.com"):
        assert resolve_email_imap_connection() is None
        bob_fields = dict(_fields())
        bob_fields["imap_user"] = "bob@example.com"
        store_email_imap_credentials(label="B inbox", fields=bob_fields)

    with tenant_scope("alice@example.com"):
        conn = resolve_email_imap_connection()
        assert conn is not None
        assert conn["user"] == "alice@example.com"

    with tenant_scope("bob@example.com"):
        conn = resolve_email_imap_connection()
        assert conn is not None
        assert conn["user"] == "bob@example.com"


def test_resolve_imap_creds_prefers_vault_on_hosted(monkeypatch, tmp_path):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "true")
    get_settings.cache_clear()

    from aethos_core.workspace_suite.email_credentials import store_email_imap_credentials
    from aethos_core.workspace_suite.email_triage import _resolve_imap_creds

    store_email_imap_credentials(label="vault", fields=_fields())

    creds_path = tmp_path / "email_creds.json"
    creds_path.write_text(
        json.dumps({"imap_host": "file.host", "imap_user": "file@example.com", "imap_password": "file"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("aethos_core.workspace_suite.email_triage._store_root", lambda: tmp_path)

    with patch("aethos_core.production.deployment_mode.is_hosted_deployment", return_value=True):
        creds = _resolve_imap_creds()
    assert creds is not None
    assert creds["host"] == "imap.example.com"
    assert creds["user"] == "alice@example.com"


def test_resolve_imap_creds_file_fallback_local_only(monkeypatch, tmp_path):
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    monkeypatch.setenv("AUTH_ENABLED", "false")
    get_settings.cache_clear()

    from aethos_core.workspace_suite.email_triage import _resolve_imap_creds

    creds_path = tmp_path / "email_creds.json"
    creds_path.write_text(
        json.dumps({"imap_host": "file.host", "imap_user": "file@example.com", "imap_password": "file"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("aethos_core.workspace_suite.email_triage._store_root", lambda: tmp_path)

    with patch("aethos_core.production.deployment_mode.is_hosted_deployment", return_value=False):
        creds = _resolve_imap_creds()
    assert creds is not None
    assert creds["host"] == "file.host"
    assert creds["user"] == "file@example.com"


@patch("imaplib.IMAP4_SSL")
def test_imap_login_test(mock_imap):
    mock_conn = MagicMock()
    mock_imap.return_value = mock_conn

    from aethos_core.workspace_suite.email_credentials import _imap_login

    result = _imap_login(_fields())
    assert result["ok"] is True
    mock_conn.login.assert_called_once_with("alice@example.com", "secret-app-pass")
    mock_conn.select.assert_called_once_with("INBOX", readonly=True)
    mock_conn.logout.assert_called_once()


def test_email_credentials_api_roundtrip(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("MULTI_TENANT_ENABLED", "false")
    get_settings.cache_clear()

    with patch("imaplib.IMAP4_SSL") as mock_imap:
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn

        from aethos_core.api.main import app

        client = TestClient(app)
        resp = client.post(
            "/api/v1/human/workspace/email/credentials",
            json={"label": "My inbox", "fields": _fields()},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert "secret-app-pass" not in resp.text
        cid = body["credential"]["credential_id"]
        assert body["test"]["ok"] is True

        conn = client.get("/api/v1/human/workspace/email/connection").json()
        assert conn["configured"] is True
        assert conn["schema"]["primary_field"] == "imap_user"

        test_resp = client.post(f"/api/v1/human/workspace/email/credentials/{cid}/test")
        assert test_resp.status_code == 200 and test_resp.json()["test"]["ok"] is True

        rev = client.post(f"/api/v1/human/workspace/email/credentials/{cid}/revoke")
        assert rev.status_code == 200 and rev.json()["revoked"] is True


def test_imap_guidance_names_real_ui_surfaces():
    from aethos_core.chat.informational_turn_classifier import compose_email_imap_setup_guidance_reply

    body = compose_email_imap_setup_guidance_reply()
    assert "Providers" in body
    assert "Email (IMAP/SMTP)" in body
    assert "Workspaces → Email" in body
    assert "preflight" not in body.lower()
