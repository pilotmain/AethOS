# SPDX-License-Identifier: Apache-2.0
"""Actionable error messages — what failed, why, what to check, next step."""

from __future__ import annotations

from typing import Any

_ERROR_CATALOG: dict[str, dict[str, str]] = {
    "api_unreachable": {
        "what": "AethOS API is not reachable",
        "why": "The API process may not be running or is bound to a different port.",
        "check": "Confirm uvicorn is running and API_PORT matches your .env.",
        "next": "./run.sh  OR  uvicorn aethos_core.api.main:app --host 0.0.0.0 --port 8010",
        "details": "Mission Control → System Health, or GET /api/v1/health",
    },
    "web_unreachable": {
        "what": "Web UI is not reachable",
        "why": "Next.js dev server may not be running on port 3000.",
        "check": "Confirm web/.env.local has NEXT_PUBLIC_API_BASE pointing at the API.",
        "next": "cd web && npm run dev",
        "details": "Open http://localhost:3000 after the dev server starts.",
    },
    "telegram_token_missing": {
        "what": "Telegram is enabled but no bot token is configured",
        "why": "TELEGRAM_ENABLED=true without TELEGRAM_BOT_TOKEN or vault credential.",
        "check": "Add token via Mission Control → Advanced settings → Credentials or .env.",
        "next": "Set TELEGRAM_BOT_TOKEN in .env and restart the API.",
        "details": "docs/TELEGRAM_SETUP.md",
    },
    "tunnel_not_configured": {
        "what": "Telegram tunnel is enabled but ngrok is not ready",
        "why": "NGROK_AUTHTOKEN missing or tunnel process failed to start.",
        "check": "Verify NGROK_AUTHTOKEN and TELEGRAM_TUNNEL_ENABLED in .env.",
        "next": "Mission Control → Runtime Tunnel → Start tunnel",
        "details": "docs/TELEGRAM_SETUP.md#tunnel",
    },
    "research_misconfigured": {
        "what": "Web research is enabled but search provider is not configured",
        "why": "WEB_RESEARCH_ENABLED=true without WEB_SEARCH_PROVIDER and API key.",
        "check": "Set WEB_SEARCH_PROVIDER=tavily and WEB_SEARCH_API_KEY.",
        "next": "Edit .env and restart the API.",
        "details": "docs/RESEARCH_SETUP.md",
    },
    "browser_not_ready": {
        "what": "Browser automation is enabled but Playwright is not ready",
        "why": "Playwright or Chromium may not be installed.",
        "check": "pip install playwright && playwright install chromium",
        "next": "aethos doctor --category browser",
        "details": "Mission Control → Browser Evidence",
    },
    "vault_unhealthy": {
        "what": "Credential vault is not healthy",
        "why": "cryptography missing or credentials directory not writable.",
        "check": "pip install cryptography and verify data/credentials permissions.",
        "next": "aethos doctor --category vault",
        "details": "docs/PROVIDER_CREDENTIALS.md",
    },
    "mutation_unsafe": {
        "what": "Unsafe mutation defaults detected",
        "why": "Production mutation tier or unrestricted execution may be enabled.",
        "check": "Review MUTATION_EXECUTION_ENABLED and MUTATION_T3_PRODUCTION_ENABLED.",
        "next": "Set both to false unless explicitly approved.",
        "details": "docs/GETTING_STARTED.md#safe-defaults",
    },
}


def build_actionable_error(code: str, *, detail: str | None = None) -> dict[str, Any]:
    """Return structured actionable error — never includes secrets."""
    base = dict(_ERROR_CATALOG.get(code, {}))
    if not base:
        base = {
            "what": code.replace("_", " "),
            "why": detail or "Unknown failure.",
            "check": "Run aethos doctor for full diagnostics.",
            "next": "aethos doctor",
            "details": "docs/TROUBLESHOOTING.md",
        }
    return {
        "code": code,
        "what_failed": base.get("what", code),
        "likely_cause": base.get("why", ""),
        "what_to_check": base.get("check", ""),
        "next_command": base.get("next", "aethos doctor"),
        "where_for_details": base.get("details", "docs/TROUBLESHOOTING.md"),
        "detail": detail,
    }


def format_actionable_error_text(err: dict[str, Any]) -> str:
    """Human-readable actionable error block."""
    lines = [
        f"What failed: {err.get('what_failed')}",
        f"Likely cause: {err.get('likely_cause')}",
        f"What to check: {err.get('what_to_check')}",
        f"Next step: {err.get('next_command')}",
        f"Details: {err.get('where_for_details')}",
    ]
    if err.get("detail"):
        lines.insert(1, f"Detail: {err['detail']}")
    return "\n".join(lines)
