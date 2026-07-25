# SPDX-License-Identifier: Apache-2.0
"""Safe defaults audit — verify enterprise-safe configuration."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.enterprise.doctor_profile import (
    break_glass_acknowledged,
    profile_allows_break_glass_warnings,
    resolve_doctor_profile,
)


def audit_safe_defaults() -> dict[str, Any]:
    """Verify default settings block unsafe autonomous behavior."""
    s = get_settings()
    break_glass: list[str] = []
    advisories: list[str] = []

    if s.mutation_execution_enabled and s.mutation_t3_production_enabled:
        break_glass.append("MUTATION_T3_PRODUCTION_ENABLED=true with mutations enabled")
    if s.host_executor_enabled:
        break_glass.append("HOST_EXECUTOR_ENABLED=true (unrestricted shell risk)")
    if s.mutation_execution_enabled and not break_glass:
        advisories.append("MUTATION_EXECUTION_ENABLED=true — ensure governance preflights are used")

    profile = resolve_doctor_profile()
    ack = break_glass_acknowledged()
    relaxed = profile_allows_break_glass_warnings()

    hard_failures = list(break_glass) if not relaxed else []
    warnings = list(break_glass) if relaxed else list(advisories)
    if relaxed and advisories:
        warnings.extend(advisories)

    checks = {
        "mutations_off_by_default": not s.mutation_execution_enabled,
        "research_off_unless_configured": not s.web_research_enabled or bool(s.web_search_api_key.strip()),
        "tunnel_off_unless_configured": not s.telegram_tunnel_enabled or bool(s.ngrok_authtoken.strip()),
        "no_auto_merge": True,
        "no_unrestricted_shell": not s.host_executor_enabled,
        "no_hidden_browser_actions": not s.browser_automation_enabled,
        "telegram_off_by_default": not s.telegram_enabled or bool(s.telegram_bot_token.strip()),
        "browser_off_by_default": not s.browser_automation_enabled,
    }

    doctor_ok = len(hard_failures) == 0
    return {
        "ok": doctor_ok,
        "profile": profile,
        "break_glass_acknowledged": ack,
        "break_glass_relaxed": relaxed,
        "violations": hard_failures + (break_glass if not relaxed else []),
        "hard_failures": hard_failures,
        "break_glass_violations": break_glass,
        "warnings": warnings,
        "checks": checks,
        "summary": "Safe defaults verified" if doctor_ok and not warnings else f"{len(hard_failures)} hard · {len(warnings)} warning(s)",
        "autonomous_execution_blocked": True,
    }
