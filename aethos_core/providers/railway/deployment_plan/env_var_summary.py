# SPDX-License-Identifier: Apache-2.0
"""Categorized env var name summaries for deployment plans (names only)."""

from __future__ import annotations

import re
from typing import Any

_CATEGORY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "Core runtime",
        (
            "APP_ENV",
            "API_PORT",
            "PORT",
            "HOST",
            "NODE_ENV",
            "DATABASE_URL",
            "REDIS_URL",
            "LOG_LEVEL",
            "ENVIRONMENT",
            "ACTIVE_PROVIDER",
            "WORKERS",
            "WEB_CONCURRENCY",
        ),
    ),
    (
        "Browser automation",
        (
            "BROWSER_",
            "PLAYWRIGHT_",
            "PUPPETEER_",
        ),
    ),
    (
        "AI providers",
        (
            "ANTHROPIC_",
            "OPENAI_",
            "WEB_SEARCH_",
            "LLM_",
            "GEMINI_",
            "COHERE_",
            "MISTRAL_",
        ),
    ),
    (
        "Integrations",
        (
            "TELEGRAM_",
            "GITHUB_",
            "RAILWAY_",
            "NGROK_",
            "SLACK_",
            "VERCEL_",
            "LINEAR_",
            "STRIPE_",
            "CLERK_",
        ),
    ),
)

_MAX_PER_CATEGORY = 6


def _matches_prefix(name: str, prefix: str) -> bool:
    if prefix.endswith("_"):
        return name.startswith(prefix)
    return name == prefix


def categorize_env_var_names(names: list[str]) -> dict[str, Any]:
    """Group env var names for plan display; never include values."""
    ordered = sorted({str(n).strip() for n in names if str(n).strip()})
    assigned: set[str] = set()
    groups: dict[str, list[str]] = {}

    for label, rules in _CATEGORY_RULES:
        matched: list[str] = []
        for name in ordered:
            if name in assigned:
                continue
            if any(_matches_prefix(name, rule) for rule in rules):
                matched.append(name)
                assigned.add(name)
        if matched:
            groups[label] = matched[:_MAX_PER_CATEGORY]

    additional = [name for name in ordered if name not in assigned]
    return {
        "groups": groups,
        "additional_count": len(additional),
        "total_count": len(ordered),
    }


def format_env_var_section_lines(
    names: list[str],
    *,
    categorized: dict[str, Any] | None = None,
) -> list[str]:
    summary = categorized or categorize_env_var_names(names)
    groups: dict[str, list[str]] = dict(summary.get("groups") or {})
    additional = int(summary.get("additional_count") or 0)
    total = int(summary.get("total_count") or len(names))

    lines = ["Required env vars:"]
    if total == 0:
        lines.extend(
            [
                "- unknown until app inspection",
                "- no secret values requested in chat",
            ]
        )
        return lines
    for label, items in groups.items():
        lines.append(f"- {label}:")
        for name in items:
            lines.append(f"  - {name}")
    if additional > 0:
        lines.append("- Additional vars detected:")
        lines.append(f"  - {additional} more (names only)")
    lines.append("- no secret values requested in chat")
    return lines


def format_env_var_names_inline(names: list[str], *, categorized: dict[str, Any] | None = None) -> str:
    """Compact summary for completion header."""
    summary = categorized or categorize_env_var_names(names)
    groups: dict[str, list[str]] = dict(summary.get("groups") or {})
    parts: list[str] = []
    for label, items in groups.items():
        parts.append(f"{label}: {', '.join(items[:4])}")
    additional = int(summary.get("additional_count") or 0)
    if additional:
        parts.append(f"+{additional} more")
    return "; ".join(parts) if parts else "none detected"
