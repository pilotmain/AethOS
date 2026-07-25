# SPDX-License-Identifier: Apache-2.0
"""Supabase env completion — constants and detection."""

from __future__ import annotations

import re
from typing import Any

SUPABASE_ENV_COMPLETION_JOB_TYPE = "supabase_env_completion"

SUPABASE_API_SETTINGS_URL = "https://supabase.com/dashboard/project/_/settings/api"

SUPABASE_ENV_VAR_NAMES = (
    "NEXT_PUBLIC_SUPABASE_URL",
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
)

OPTIONAL_SUPABASE_ENV_VAR_NAMES = (
    "SUPABASE_SERVICE_ROLE_KEY",
    "NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY",
)

_SUPABASE_COMPLETION_RX = re.compile(
    r"\b("
    r"complete(?:\s+\w+){0,4}\s+(?:env|environment)\s+(?:setup|config(?:uration)?)"
    r"|fix(?:\s+\w+){0,4}\s+supabase(?:\s+\w+){0,3}\s+deploy"
    r"|supabase\s+env\s+completion"
    r"|complete\s+supabase\s+env"
    r"|set\s+up\s+supabase(?:\s+\w+){0,3}\s+for"
    r")\b",
    re.I,
)


def is_supabase_env_completion_request(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _SUPABASE_COMPLETION_RX.search(raw):
        return True
    lower = raw.lower()
    if "supabase" in lower and any(token in lower for token in ("env", "environment", "credentials", "keys")):
        if any(token in lower for token in ("complete", "fix", "setup", "finish", "missing")):
            return True
    return False


def supabase_env_names_for_plan(*, required_names: list[str] | None = None) -> list[str]:
    required = [str(n).strip().upper() for n in (required_names or []) if str(n).strip()]
    out: list[str] = []
    for name in SUPABASE_ENV_VAR_NAMES:
        if not required or name in required:
            out.append(name)
    return out


def missing_supabase_env_names(
    *,
    plan: dict[str, Any],
    required_names: list[str] | None = None,
) -> list[str]:
    from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import build_target_key_for_plan
    from aethos_core.providers.railway.env_value_readiness.env_value_inventory import probe_env_var_presence

    names = supabase_env_names_for_plan(required_names=required_names)
    missing: list[str] = []
    for name in names:
        presence = probe_env_var_presence(name, plan=plan)
        if not presence.get("present"):
            missing.append(name)
    _ = build_target_key_for_plan(plan)
    return missing
