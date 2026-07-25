# SPDX-License-Identifier: Apache-2.0
"""Configuration center — .env status without secrets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.config import Settings, get_settings
from aethos_core.enterprise.safe_defaults import audit_safe_defaults
from aethos_core.research.research_config import preview_api_key, research_config_errors


_SECRET_KEYS = frozenset(
    {
        "ANTHROPIC_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "WEB_SEARCH_API_KEY",
        "WEB_API_TOKEN",
        "NGROK_AUTHTOKEN",
    }
)

_FEATURE_FLAGS: list[tuple[str, str, bool]] = [
    ("USE_REAL_LLM", "LLM reasoning", False),
    ("BROWSER_AUTOMATION_ENABLED", "Governed browser observation", False),
    ("WEB_RESEARCH_ENABLED", "Web research", False),
    ("TELEGRAM_ENABLED", "Telegram channel", False),
    ("TELEGRAM_TUNNEL_ENABLED", "Ngrok tunnel", False),
    ("MUTATION_EXECUTION_ENABLED", "Mutation execution", False),
    ("MUTATION_T3_PRODUCTION_ENABLED", "Production mutations (T3)", False),
    ("HOST_EXECUTOR_ENABLED", "Governed execution runtime", False),
]


def _env_file_status() -> dict[str, Any]:
    path = Path(".env")
    example = Path(".env.example")
    present = path.is_file()
    keys_in_env: set[str] = set()
    if present:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            keys_in_env.add(line.split("=", 1)[0].strip().upper())
    example_keys: set[str] = set()
    if example.is_file():
        for line in example.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            example_keys.add(line.split("=", 1)[0].strip().upper())
    missing_recommended = sorted(k for k in example_keys if k not in keys_in_env and k not in _SECRET_KEYS)[:20]
    return {
        "env_present": present,
        "env_path": str(path.resolve()) if present else None,
        "keys_configured": len(keys_in_env),
        "missing_recommended_keys": missing_recommended,
        "restart_required_hint": "Restart API and web dev server after changing .env",
    }


def _mask_settings(s: Settings) -> dict[str, Any]:
    return {
        "app_env": s.app_env,
        "api_port": s.api_port,
        "use_real_llm": s.use_real_llm,
        "active_provider": s.active_provider,
        "anthropic_api_key": preview_api_key(s.anthropic_api_key) if s.anthropic_api_key else None,
        "browser_automation_enabled": s.browser_automation_enabled,
        "web_research_enabled": s.web_research_enabled,
        "web_search_provider": s.web_search_provider,
        "web_search_api_key": preview_api_key(s.web_search_api_key) if s.web_search_api_key else None,
        "telegram_enabled": s.telegram_enabled,
        "telegram_bot_token": "configured" if s.telegram_bot_token.strip() else None,
        "telegram_tunnel_enabled": s.telegram_tunnel_enabled,
        "ngrok_authtoken": "configured" if s.ngrok_authtoken.strip() else None,
        "mutation_execution_enabled": s.mutation_execution_enabled,
        "host_executor_enabled": s.host_executor_enabled,
    }


def build_configuration_center() -> dict[str, Any]:
    """One place for config clarity — no raw secrets."""
    s = get_settings()
    env_status = _env_file_status()
    research_errors = research_config_errors(s)

    enabled: list[str] = []
    disabled: list[str] = []
    for env_key, label, safe_off in _FEATURE_FLAGS:
        val = getattr(s, env_key.lower(), None)
        if val is True:
            enabled.append(label)
        elif val is False and safe_off:
            disabled.append(label)

    return {
        "ok": True,
        "env": env_status,
        "settings_preview": _mask_settings(s),
        "enabled_features": enabled,
        "disabled_features": disabled,
        "research_errors": research_errors,
        "safe_defaults": audit_safe_defaults(),
        "no_secrets_exposed": True,
    }
