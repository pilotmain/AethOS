# SPDX-License-Identifier: Apache-2.0
"""BYO subscription credential bridge (§B7)."""

from __future__ import annotations

from aethos_core.providers.cloud.subscription_bridge import register_subscription_credential


def test_register_subscription_credential_stores_in_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIAL_VAULT_DIR", str(tmp_path / "vault"))
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    out = register_subscription_credential(provider="openai", subscription_token="sub-token-abc", label="Copilot seat")
    assert out["ok"] is True
    assert out["credential_id"].startswith("cred-")
    get_settings.cache_clear()
