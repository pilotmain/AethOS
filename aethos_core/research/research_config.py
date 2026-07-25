# SPDX-License-Identifier: Apache-2.0
"""Research configuration — diagnostics, validation, key preview."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from aethos_core.config import Settings, get_settings

_LOG = logging.getLogger("aethos.research")

_SUPPORTED_PROVIDERS = frozenset({"none", "tavily", "searxng"})


def research_config_source() -> str:
    if Path(".env").is_file():
        return ".env"
    return "environment"


def preview_api_key(key: str | None) -> str | None:
    raw = (key or "").strip()
    if not raw:
        return None
    if len(raw) <= 8:
        return "****"
    return f"{raw[:5]}-****{raw[-4:]}"


def research_config_errors(settings: Settings) -> list[str]:
    errors: list[str] = []
    if not settings.web_research_enabled:
        return errors
    provider = _normalized_provider(settings.web_search_provider)
    if provider in ("none", "", "disabled"):
        errors.append("WEB_SEARCH_PROVIDER is missing or none")
    elif provider not in _SUPPORTED_PROVIDERS - {"none"}:
        errors.append(f"WEB_SEARCH_PROVIDER '{provider}' is not supported (use: tavily, searxng)")
    elif provider == "tavily" and not (settings.web_search_api_key or "").strip():
        errors.append("WEB_SEARCH_API_KEY is missing")
    elif provider == "searxng" and not (getattr(settings, "web_search_base_url", None) or "").strip():
        errors.append("WEB_SEARCH_BASE_URL is missing")
    return errors


def is_research_search_configured(settings: Settings | None = None) -> bool:
    s = settings or get_settings()
    if not s.web_research_enabled:
        return False
    provider = _normalized_provider(s.web_search_provider)
    if provider in ("none", "", "disabled"):
        return False
    if provider == "tavily":
        return bool((s.web_search_api_key or "").strip())
    if provider == "searxng":
        return bool((getattr(s, "web_search_base_url", None) or "").strip())
    return provider in _SUPPORTED_PROVIDERS - {"none"}


def build_research_status(settings: Settings | None = None) -> dict[str, Any]:
    s = settings or get_settings()
    provider = _normalized_provider(s.web_search_provider)
    key = (s.web_search_api_key or "").strip()
    errors = research_config_errors(s)
    configured = is_research_search_configured(s)
    return {
        "enabled": bool(s.web_research_enabled),
        "provider": provider or "none",
        "api_key_configured": bool(key),
        "api_key_preview": preview_api_key(key),
        "max_results": int(s.web_research_max_results),
        "artifacts_dir": str(s.research_artifacts_dir),
        "configured": configured,
        "config_source": research_config_source(),
        "restart_required_hint": "Restart the API after changing .env research settings.",
        "errors": errors,
        "loaded": {
            "WEB_RESEARCH_ENABLED": bool(s.web_research_enabled),
            "WEB_SEARCH_PROVIDER": provider or "none",
            "WEB_SEARCH_API_KEY": f"configured={bool(key)}",
            "WEB_RESEARCH_MAX_RESULTS": int(s.web_research_max_results),
            "RESEARCH_ARTIFACTS_DIR": str(s.research_artifacts_dir),
        },
    }


def missing_env_lines(settings: Settings | None = None) -> list[str]:
    s = settings or get_settings()
    lines: list[str] = []
    provider = _normalized_provider(s.web_search_provider)
    if provider in ("none", "", "disabled"):
        lines.append("WEB_SEARCH_PROVIDER=tavily")
    if not (s.web_search_api_key or "").strip():
        lines.append("WEB_SEARCH_API_KEY=your_tavily_key_here")
    if not (s.research_artifacts_dir or "").strip():
        lines.append("RESEARCH_ARTIFACTS_DIR=data/research_artifacts")
    return lines


def format_incomplete_config_message(settings: Settings | None = None) -> str:
    s = settings or get_settings()
    status = build_research_status(s)
    lines = [
        "**Web research is enabled, but search provider is incomplete.**",
        "",
        "**Missing:**",
    ]
    for err in status["errors"]:
        lines.append(f"- {err}")
    for env_line in missing_env_lines(s):
        if env_line not in {e.split(" is ")[0] for e in status["errors"]}:
            lines.append(f"- `{env_line}`")
    lines.extend(
        [
            "",
            "**Current loaded config:**",
            f"- WEB_RESEARCH_ENABLED={str(status['enabled']).lower()}",
            f"- WEB_SEARCH_PROVIDER={status['provider']}",
            f"- WEB_SEARCH_API_KEY={status['loaded']['WEB_SEARCH_API_KEY']}",
            f"- RESEARCH_ARTIFACTS_DIR={status['artifacts_dir']}",
            f"- config_source={status['config_source']}",
            "",
            "**Add to `.env` then restart API:**",
            "```",
            "cat >> .env <<'EOF'",
        ]
    )
    for env_line in missing_env_lines(s) or ["WEB_SEARCH_PROVIDER=tavily", "WEB_SEARCH_API_KEY=your_tavily_key_here"]:
        lines.append(env_line)
    lines.extend(
        [
            "EOF",
            "```",
            "",
            "Then restart:",
            "```",
            "lsof -ti :8010 | xargs kill -9",
            ".venv/bin/uvicorn aethos_core.api.main:app --reload --port 8010",
            "```",
            "",
            "I can still inspect a **specific public URL** using governed browser evidence.",
        ]
    )
    return "\n".join(lines)


def validate_research_config_at_startup(settings: Settings | None = None) -> None:
    s = settings or get_settings()
    if not s.web_research_enabled:
        return
    provider = _normalized_provider(s.web_search_provider)
    if provider in ("none", "", "disabled"):
        _LOG.warning("[AethOS] Web research enabled but WEB_SEARCH_PROVIDER is missing.")
    if provider == "searxng" and not (getattr(s, "web_search_base_url", None) or "").strip():
        _LOG.warning("[AethOS] Web research enabled with searxng but WEB_SEARCH_BASE_URL is missing.")
    elif provider == "tavily" and not (s.web_search_api_key or "").strip():
        _LOG.warning("[AethOS] Web research enabled but WEB_SEARCH_API_KEY is missing.")


def _normalized_provider(raw: str | None) -> str:
    return (raw or "none").strip().lower()
