# SPDX-License-Identifier: Apache-2.0
"""Generic per-channel credential flow — vault store/resolve/test/revoke, multi-field."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.config import get_settings


@pytest.fixture(autouse=True)
def _isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "creds"))
    get_settings.cache_clear()
    from aethos_core.channels.channel_registry import reset_channel_registry_for_tests
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    reset_channel_registry_for_tests()
    yield
    reset_credential_vault_for_tests()
    reset_channel_registry_for_tests()
    get_settings.cache_clear()


def _spec_module():
    import aethos_core.channels.channel_credentials as mod

    return mod


def test_schema_lists_required_fields_with_secret_flags():
    mod = _spec_module()
    slack = mod.get_channel_credential_spec("slack")
    assert slack is not None
    schema = slack.to_schema()
    field_ids = {f["id"] for f in schema["fields"]}
    assert "bot_token" in field_ids and "signing_secret" in field_ids
    assert schema["primary_field"] == "bot_token"
    bot = next(f for f in schema["fields"] if f["id"] == "bot_token")
    assert bot["secret"] is True


def test_store_resolve_roundtrip_multifield():
    mod = _spec_module()
    record = mod.store_channel_credentials(
        channel_id="slack",
        label="Workspace bot",
        fields={"bot_token": "xoxb-abc123", "signing_secret": "sec-xyz"},
    )
    assert record.provider == "slack"
    resolved = mod.resolve_channel_credentials("slack")
    assert resolved["bot_token"] == "xoxb-abc123"
    assert resolved["signing_secret"] == "sec-xyz"
    assert mod.channel_has_vault_credentials("slack") is True


def test_store_requires_primary_field():
    mod = _spec_module()
    with pytest.raises(mod.ChannelCredentialError):
        mod.store_channel_credentials(channel_id="slack", label="x", fields={"signing_secret": "only"})


def test_secret_is_masked_and_not_plaintext():
    mod = _spec_module()
    record = mod.store_channel_credentials(
        channel_id="whatsapp",
        label="wa",
        fields={"access_token": "supersecrettoken", "phone_number_id": "999"},
    )
    public = record.to_public_dict()
    assert "supersecrettoken" not in str(public)
    creds = mod.list_channel_credentials("whatsapp")
    assert "supersecrettoken" not in str(creds)


def test_revoke_removes_credential():
    mod = _spec_module()
    record = mod.store_channel_credentials(
        channel_id="discord", label="d", fields={"bot_token": "dtok", "public_key": "abcd"}
    )
    assert mod.channel_has_vault_credentials("discord") is True
    assert mod.revoke_channel_credential("discord", record.credential_id) is True
    assert mod.channel_has_vault_credentials("discord") is False


def test_unregistered_or_unknown_channel_not_supported():
    mod = _spec_module()
    # Matrix has a schema but no registered adapter → not connectable from UI.
    assert mod.get_channel_credential_spec("matrix") is not None
    assert mod.channel_supports_credentials("matrix") is False
    # Pure unknown.
    assert mod.channel_supports_credentials("nope") is False


def test_resolve_reads_telegram_plain_token_backcompat():
    mod = _spec_module()
    from aethos_core.security.credential_vault import get_credential_vault

    get_credential_vault().store_api_token(provider="telegram", label="tg", token="123:plainTOKEN")
    resolved = mod.resolve_channel_credentials("telegram")
    assert resolved.get("token") == "123:plainTOKEN"
    assert mod.channel_has_vault_credentials("telegram") is True


def test_generic_credentials_endpoint_roundtrip():
    from aethos_core.api.main import app

    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/channels/slack/credentials",
            json={"label": "Slack bot", "fields": {"bot_token": "xoxb-zzz", "signing_secret": "shh"}},
        )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["ok"] is True
        assert "xoxb-zzz" not in resp.text
        cid = body["credential"]["credential_id"]

        conn = client.get("/api/v1/channels/slack/connection").json()
        assert conn["configured"] is True
        assert conn["schema"]["primary_field"] == "bot_token"

        test_resp = client.post(f"/api/v1/channels/slack/credentials/{cid}/test")
        assert test_resp.status_code == 200 and test_resp.json()["test"]["ok"] is True

        rev = client.post(f"/api/v1/channels/slack/credentials/{cid}/revoke")
        assert rev.status_code == 200 and rev.json()["revoked"] is True


def test_endpoint_404_for_unregistered_adapter():
    from aethos_core.api.main import app

    client = TestClient(app)
    resp = client.post(
        "/api/v1/channels/matrix/credentials",
        json={"label": "m", "fields": {"homeserver_url": "https://x", "access_token": "t"}},
    )
    assert resp.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
