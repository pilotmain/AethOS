# SPDX-License-Identifier: Apache-2.0
"""Pure auth label helpers — no provider registration imports."""

from __future__ import annotations

AUTH_METHOD_LABELS: dict[str, str] = {
    "api_token": "Vercel API token",
    "browser": "Saved browser session",
    "browser_session": "Saved browser session",
    "cli": "Vercel CLI authentication",
    "username_password": "Username/password vault",
    "ask": "Ask each time",
    "none": "None",
}


def normalize_auth_method(method: str | None) -> str:
    if not method:
        return "none"
    key = method.strip().lower()
    if key in ("browser", "browser_session"):
        return "browser"
    if key in AUTH_METHOD_LABELS:
        return key
    return key


def auth_method_label(method: str | None) -> str:
    if not method:
        return "Unknown"
    return AUTH_METHOD_LABELS.get(normalize_auth_method(method), method.replace("_", " ").title())


def auth_method_label_for_provider(provider: str | None, method: str | None) -> str:
    prov = (provider or "").strip().lower()
    key = normalize_auth_method(method)
    if key == "api_token":
        if prov == "railway":
            return "Railway API token"
        if prov == "github":
            return "GitHub API token"
        return "Vercel API token"
    return auth_method_label(method)


def provider_auth_source_phrase(provider: str | None, method: str | None) -> str:
    """Provider-aware auth source phrase for progress/completion copy."""
    prov = (provider or "").strip().lower()
    key = normalize_auth_method(method)
    if key == "api_token":
        if prov == "railway":
            return "saved Railway API token"
        if prov == "github":
            return "saved GitHub API token"
        return "saved Vercel API token"
    if key == "browser":
        return "saved browser session"
    if key == "cli":
        if prov == "railway":
            return "Railway CLI authentication"
        return "Vercel CLI authentication"
    if key == "none":
        return "configured connection"
    return auth_method_label_for_provider(provider, method).lower()


def auth_source_phrase(method: str | None) -> str:
    """User-facing phrase for how auth was sourced (lowercase, mid-sentence)."""
    return provider_auth_source_phrase(None, method)
