# SPDX-License-Identifier: Apache-2.0
"""Railway read-only inspection jobs — on-demand inventory (no operational memory)."""

from __future__ import annotations

import re
from typing import Any

_RAILWAY_INVENTORY_RX = re.compile(
    r"\b(show|list|what are)\b.*\b(my )?railway\b.*\b(apps|services|projects)\b|"
    r"\b(show|list)\b.*\b(railway)\b.*\b(apps|services|projects)\b|"
    r"\brailway\b.*\b(apps|services|projects)\b.*\b(list|inventory)\b",
    re.I,
)

RAILWAY_READONLY_JOB_TYPES = frozenset(
    {
        "railway_services_inventory",
    }
)


def is_railway_inventory_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw or not re.search(r"\brailway\b", raw, re.I):
        return False
    return bool(_RAILWAY_INVENTORY_RX.search(raw))


def infer_railway_readonly_job(text: str) -> tuple[str, str, dict[str, Any]] | None:
    """Return (title, job_type, params) or None."""
    raw = (text or "").strip()
    if not is_railway_inventory_request(raw):
        return None
    return (
        "Railway services inventory",
        "railway_services_inventory",
        {"user_request": raw, "provider": "railway", "scope": "railway"},
    )


def resolve_railway_auth_for_chat() -> dict[str, str | None]:
    from aethos_core.providers.railway.auth import RailwayAuthAdapter

    resolved = RailwayAuthAdapter().resolve_best_auth_method(operation="read_projects")
    method = str(resolved.get("method") or "")
    if method == "api_token":
        return {
            "auth_method": "api_token",
            "credential_id": str(resolved.get("credential_id") or ""),
            "block_reason": None,
        }
    return {
        "auth_method": None,
        "credential_id": None,
        "block_reason": "missing",
    }


def railway_connect_required_reply() -> str:
    return (
        "I need a **Railway API token** before I can list your services.\n\n"
        "Open **Mission Control → Advanced settings → Credentials → Railway** and add an API token.\n\n"
        "AethOS never asks for tokens in chat."
    )
