# SPDX-License-Identifier: Apache-2.0
"""Bring-your-own-subscription credential bridge (§B7)."""

from __future__ import annotations

from typing import Any

from aethos_core.security.credential_vault import get_credential_vault

_SUBSCRIPTION_KIND = "chat_subscription"


def register_subscription_credential(
    *,
    provider: str,
    subscription_token: str,
    label: str = "",
) -> dict[str, Any]:
    """Store a governed subscription credential in the vault (never logged)."""
    token = (subscription_token or "").strip()
    if not token:
        return {"ok": False, "error": "subscription_token_required"}
    provider_key = (provider or "openai").strip().lower()
    rec = get_credential_vault().store_api_token(
        provider=provider_key,
        label=label or f"{provider_key} chat subscription",
        token=token,
        scope=["chat_completion"],
        write_allowed=False,
    )
    return {
        "ok": True,
        "credential_id": rec.credential_id,
        "provider": provider_key,
        "kind": _SUBSCRIPTION_KIND,
    }


def list_subscription_credentials(*, provider: str | None = None) -> dict[str, Any]:
    creds = get_credential_vault().list_credentials(provider=provider)
    rows = [
        c.to_public_dict()
        for c in creds
        if "subscription" in (c.label or "").lower() or c.type.name == "API_TOKEN"
    ]
    return {"ok": True, "credentials": rows, "count": len(rows)}
