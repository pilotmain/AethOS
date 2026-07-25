# SPDX-License-Identifier: Apache-2.0
"""Unified Mission Control credential + inventory bridge for agent cloud tools."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.execution_brain.cloud_provider_catalog import (
    FIRST_CLASS_AGENT_PROVIDERS,
    SKILL_BACKED_PROVIDERS,
    list_agent_cloud_providers,
    normalize_provider_name,
    provider_display_name,
)

_MC_HINT = "Add or validate the token in **Mission Control → Providers**."


def resolve_provider_token(provider: str, *, require_validated: bool = False) -> tuple[str | None, str | None]:
    """Return (token, error) from Mission Control vault / canonical resolvers."""
    canonical = normalize_provider_name(provider)
    if not canonical:
        return None, f"unknown_provider:{provider}"
    try:
        from aethos_core.credentials import get_provider_api_token

        token = get_provider_api_token(canonical, require_validated=require_validated)
        if token:
            return str(token).strip(), None
    except Exception as exc:
        return None, str(exc)
    return None, f"{canonical}_token_not_configured"


def validate_provider_connection(provider: str, *, use_cache: bool = True) -> dict[str, Any]:
    canonical = normalize_provider_name(provider)
    if not canonical:
        return {"ok": False, "provider": provider, "error": "unknown_provider"}

    if use_cache:
        from aethos_core.execution_brain.provider_connection_cache import cache_get, cache_set

        cached = cache_get(canonical, op="validate")
        if cached is not None:
            return cached

    if canonical in FIRST_CLASS_AGENT_PROVIDERS:
        if canonical == "vercel":
            from aethos_core.provider_e2e_readiness.vercel_readiness_checks import run_vercel_readiness_checks

            checks = run_vercel_readiness_checks(session_id="default")
            ok = bool(checks.get("vercel_credential_ok")) and bool(checks.get("vercel_api_connection_ok"))
            payload = {
                "ok": ok,
                "provider": canonical,
                "credential_ok": bool(checks.get("vercel_credential_ok")),
                "api_connection_ok": bool(checks.get("vercel_api_connection_ok")),
                "project_count": int(checks.get("vercel_project_count") or 0),
                "detail": checks.get("vercel_api_connection_detail") or checks.get("vercel_credential_detail") or "",
            }
            if use_cache:
                cache_set(canonical, payload, op="validate")
            return payload
        token, token_error = resolve_provider_token("railway", require_validated=False)
        payload = {
            "ok": bool(token),
            "provider": canonical,
            "detail": "Railway token configured in Provider Inventory." if token else (token_error or _MC_HINT),
            "credential_source": "mission_control_vault",
        }
        if use_cache:
            cache_set(canonical, payload, op="validate")
        return payload

    token, token_error = resolve_provider_token(canonical, require_validated=False)
    if not token:
        return {
            "ok": False,
            "provider": canonical,
            "error": token_error or "token_not_configured",
            "detail": _MC_HINT,
        }

    from aethos_core.providers.cloud.validators import validate_cloud_provider_token

    validation = validate_cloud_provider_token(canonical, token)
    payload = {
        "ok": bool(validation.get("ok")),
        "provider": canonical,
        "label": provider_display_name(canonical),
        "detail": validation.get("detail") or validation.get("error"),
        "validation": validation,
        "credential_source": "mission_control_vault",
    }
    if use_cache:
        from aethos_core.execution_brain.provider_connection_cache import cache_set

        cache_set(canonical, payload, op="validate")
    return payload


def discover_provider_inventory(provider: str, *, session_id: str = "default") -> dict[str, Any]:
    canonical = normalize_provider_name(provider)
    if not canonical:
        return {"ok": False, "provider": provider, "error": "unknown_provider", "inventory": {}}

    if canonical in FIRST_CLASS_AGENT_PROVIDERS:
        from aethos_core.provider_skills.runtime import load_provider_skill

        skill = load_provider_skill(canonical)
        if skill is None:
            return {"ok": False, "provider": canonical, "error": f"{canonical}_skill_unavailable"}
        payload = skill.discover(force=True)
        return {
            "ok": bool(payload.get("ok")),
            "provider": canonical,
            "inventory": payload.get("inventory") or payload.get("result") or payload,
            "error": payload.get("error"),
            "session_id": session_id,
        }

    if canonical in SKILL_BACKED_PROVIDERS or canonical in {"github", "aws", "gcp", "azure", "cloudflare", "kubernetes", "docker"}:
        from aethos_core.provider_skills.runtime import load_provider_skill

        skill = load_provider_skill(canonical)
        if skill is not None:
            payload = skill.discover(force=True)
            return {
                "ok": bool(payload.get("ok")),
                "provider": canonical,
                "inventory": payload.get("inventory") or payload,
                "error": payload.get("error"),
                "session_id": session_id,
            }

    token, token_error = resolve_provider_token(canonical, require_validated=False)
    if not token:
        return {
            "ok": False,
            "provider": canonical,
            "error": token_error or "token_not_configured",
            "detail": _MC_HINT,
            "inventory": {},
        }

    from aethos_core.execution_brain.provider_inventory_registry import fetch_provider_inventory
    from aethos_core.providers.cloud.validators import validate_cloud_provider_token

    validation = validate_cloud_provider_token(canonical, token)
    if not validation.get("ok"):
        return {
            "ok": False,
            "provider": canonical,
            "error": validation.get("detail") or "token_invalid",
            "inventory": {},
            "validation": validation,
        }

    listed = fetch_provider_inventory(canonical, token)
    inventory = {
        "provider": canonical,
        "label": provider_display_name(canonical),
        "validation": validation,
        "resources": list(listed.get("resources") or []),
        "resource_count": int(listed.get("resource_count") or 0),
        "message": listed.get("message"),
    }
    ok = bool(listed.get("ok")) or bool(validation.get("ok"))
    return {
        "ok": ok,
        "provider": canonical,
        "inventory": inventory,
        "error": listed.get("error"),
        "session_id": session_id,
    }


def list_all_provider_inventory(*, session_id: str = "default", limit: int = 40, mode: str = "full") -> dict[str, Any]:
    """Scan every Mission Control provider — connection + optional inventory."""
    from aethos_core.execution_brain.provider_agent_ops import provider_inventory_all

    return provider_inventory_all(session_id=session_id, limit=limit, mode=mode)


def parse_aws_vault_token(token: str) -> dict[str, Any]:
    raw = (token or "").strip()
    access_key = ""
    secret_key = ""
    region = "us-east-1"
    if raw.startswith("{"):
        try:
            payload = json.loads(raw)
            access_key = str(payload.get("aws_access_key_id") or payload.get("access_key_id") or "").strip()
            secret_key = str(payload.get("aws_secret_access_key") or payload.get("secret_access_key") or "").strip()
            region = str(payload.get("region") or payload.get("aws_region") or region).strip()
        except json.JSONDecodeError:
            return {"ok": False, "error": "invalid_aws_json"}
    elif ":" in raw:
        access_key, secret_key = raw.split(":", 1)
        access_key = access_key.strip()
        secret_key = secret_key.strip()
    if not access_key or not secret_key:
        return {"ok": False, "error": "aws_credentials_incomplete"}
    return {"ok": True, "access_key": access_key, "secret_key": secret_key, "region": region}


def provider_names_for_prompt() -> str:
    names = list_agent_cloud_providers()
    chunks = [", ".join(names[i : i + 8]) for i in range(0, len(names), 8)]
    return "\n".join(f"- {line}" for line in chunks)
