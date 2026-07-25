# SPDX-License-Identifier: Apache-2.0
"""P4.2 — AWS readonly inventory adapter for operational kernel (credential-gated)."""

from __future__ import annotations

from typing import Any


def fetch_aws_readonly_inventory(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    if not settings.aws_readonly_inventory_enabled:
        return {
            "ok": False,
            "error": "AWS readonly inventory is disabled. Set AWS_READONLY_INVENTORY_ENABLED=true after credentials are configured.",
        }
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token("aws")
        if not token:
            return {"ok": False, "error": "AWS credentials are not configured in Mission Control → Advanced settings → Credentials."}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    return {
        "ok": True,
        "accounts": [],
        "message": "AWS readonly inventory adapter registered; wire boto3 list calls in a follow-up when credentials are live.",
        "session_id": session_id,
    }
