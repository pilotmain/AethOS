# SPDX-License-Identifier: Apache-2.0
"""P4.3 — readonly inventory adapters for cloud providers (credential-gated)."""

from __future__ import annotations

from typing import Any

_EXPANDED_PROVIDERS = ("aws", "gcp", "azure", "kubernetes", "cloudflare")


def list_cloud_readonly_inventory(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    if not bool(getattr(settings, "cloud_readonly_inventory_enabled", False)):
        return {
            "ok": False,
            "enabled": False,
            "error": "Cloud readonly inventory is disabled. Set CLOUD_READONLY_INVENTORY_ENABLED=true.",
            "providers": [],
        }
    rows: list[dict[str, Any]] = []
    for provider in _EXPANDED_PROVIDERS:
        row = fetch_cloud_readonly_inventory(provider=provider, session_id=session_id)
        rows.append(
            {
                "provider": provider,
                "ok": bool(row.get("ok")),
                "error": row.get("error"),
                "inventory": row.get("inventory"),
            }
        )
    ok_count = sum(1 for row in rows if row.get("ok"))
    return {
        "ok": ok_count > 0,
        "enabled": True,
        "session_id": session_id,
        "providers": rows,
        "summary": f"{ok_count}/{len(rows)} provider probes ok",
    }


def fetch_cloud_readonly_inventory(*, provider: str, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.execution_brain.cloud_agent_bridge import discover_provider_inventory
    from aethos_core.execution_brain.cloud_provider_catalog import is_registered_provider, normalize_provider_name

    provider_key = normalize_provider_name(provider) or (provider or "").strip().lower()
    if is_registered_provider(provider_key):
        payload = discover_provider_inventory(provider_key, session_id=session_id)
        return {
            "ok": bool(payload.get("ok")),
            "provider": provider_key,
            "inventory": payload.get("inventory"),
            "error": payload.get("error"),
            "session_id": session_id,
            "credential_source": "mission_control_vault",
        }

    from aethos_core.config import get_settings

    settings = get_settings()
    if not bool(getattr(settings, "cloud_readonly_inventory_enabled", False)):
        return {
            "ok": False,
            "provider": provider_key,
            "error": "Cloud readonly inventory is disabled. Set CLOUD_READONLY_INVENTORY_ENABLED=true.",
        }
    if provider_key in _EXPANDED_PROVIDERS:
        return _discover_via_provider_skill(provider=provider_key, session_id=session_id)
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token(provider_key)
        if not token:
            return {
                "ok": False,
                "provider": provider_key,
                "error": f"{provider_key} credentials are not configured in Mission Control → Advanced settings → Credentials.",
            }
    except Exception as exc:
        return {"ok": False, "provider": provider_key, "error": str(exc)}
    return {
        "ok": True,
        "provider": provider_key,
        "resources": [],
        "message": f"{provider_key} readonly inventory adapter registered; wire provider SDK list calls when credentials are live.",
        "session_id": session_id,
    }


def _discover_via_provider_skill(*, provider: str, session_id: str) -> dict[str, Any]:
    from aethos_core.operational_skill_runtime.skill_registry import get_provider_skill

    skill = get_provider_skill(provider)
    if skill is None:
        return {"ok": False, "provider": provider, "error": f"No provider skill registered for {provider}."}
    try:
        payload = skill.discover(force=True)
    except Exception as exc:
        return {"ok": False, "provider": provider, "error": str(exc), "session_id": session_id}
    inventory = payload.get("inventory") if isinstance(payload, dict) else {}
    return {
        "ok": bool(payload.get("ok")),
        "provider": provider,
        "inventory": inventory or payload,
        "error": payload.get("error"),
        "session_id": session_id,
    }
