# SPDX-License-Identifier: Apache-2.0
"""Canonical browser / Vercel operational intent detection — routing source of truth."""

from __future__ import annotations

import re
from typing import Any, Literal

IntentKind = Literal[
    "browser_status",
    "browser_session_open",
    "browser_login",
    "vercel_inspection",
    "vercel_mutation",
    "vercel_ambiguous",
    None,
]

# Documented example phrases (tests + operator docs)
BROWSER_SESSION_OPEN_INTENTS = (
    "open supervised Vercel session",
    "open Vercel session",
    "start Vercel browser session",
    "launch browser for Vercel",
    "open Vercel dashboard",
    "connect to Vercel dashboard",
    "open browser automation for Vercel",
    "open vercel.com in browser automation",
)

BROWSER_LOGIN_INTENTS = (
    "login to Vercel",
    "authenticate to Vercel",
    "open logged-in Vercel dashboard",
    "login to vercel.com and check my dashboard",
)

VERCEL_INSPECTION_INTENTS = (
    "tell me all my Vercel apps",
    "show my Vercel apps",
    "what projects are on Vercel",
    "list my Vercel services",
    "check deployment status",
    "show service health",
)

VERCEL_MUTATION_INTENTS = (
    "restart deployment",
    "redeploy my app",
    "delete deployment",
    "change environment variables",
    "restart service",
)

_LAUNCH_RX = re.compile(
    r"\b(open|start|launch|connect|begin|create|run)\b",
    re.I,
)
_SESSION_RX = re.compile(r"\b(session|browser|automation)\b", re.I)
_DASHBOARD_RX = re.compile(r"\b(dashboard|console)\b", re.I)
_SUPERVISED_RX = re.compile(r"\b(supervised|operator[- ]?approved)\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel(?:\.com)?\b", re.I)

_BROWSER_STATUS_RX = re.compile(
    r"\b(can you|could you|do you)\b.*\b(use\s+)?browser\s+automation\b|"
    r"\bbrowser\s+automation\b.*\b(enabled|available|on|off|status)\b|"
    r"\bcan you\b.*\bbrowse\s+websites?\b|"
    r"\buse\s+browser\s+automation\b",
    re.I,
)

_BROWSER_LOGIN_RX = re.compile(
    r"\b(log\s*in\s+to|login\s+to|sign\s*in\s+to|authenticate\s+to|auth\s+to)\b.*\bvercel\b|"
    r"\bvercel\b.*\b(log\s*in|login|sign\s*in|authenticate)\b|"
    r"\b(log\s*in\s+to|login\s+to|sign\s*in\s+to)\b.*\b(dashboard|my\s+account)\b|"
    r"\b(logged[- ]?in|authenticated)\b.*\b(vercel\b.*\b)?dashboard\b|"
    r"\bcheck\s+my\s+dashboard\b|"
    r"\bvercel\b.*\bdashboard\b.*\b(login|sign\s*in)\b",
    re.I,
)

_BROWSER_NAV_LEGACY_RX = re.compile(
    r"\b(open|go\s+to|navigate\s+to|visit)\b.*\b(in\s+)?browser\b|"
    r"\b(open|go\s+to|visit)\b.*\b(https?://|\.com\b|\.org\b|\.io\b)",
    re.I,
)

_VERCEL_READONLY_RX = re.compile(
    r"\b(tell\s+me|list|show|what\s+are|what|which|all|my|give|want)\b.*\b(vercel\s+)?(apps?|projects?|services?)\b|"
    r"\b(vercel\s+)?(apps?|projects?|services?)\b.*\b(on\s+)?vercel\b|"
    r"\bvercel\b.*\b(apps?|projects?|services?)\b|"
    r"\b(service|services)\b.*\b(health|deployed)\b|"
    r"\bvercel\b.*\b(service|services)\b.*\b(health|deployed)\b|"
    r"\bwhich\b.*\b(apps?|projects?|services?)\b.*\b(healthy|down|up)\b|"
    r"\b(deployment|deployments)\b.*\b(status|summary)\b|"
    r"\bvercel\b.*\b(deployment|deployments)\b.*\b(status|summary)\b|"
    r"\bcheck\b.*\b(deployment|service)\b.*\b(status|health)\b|"
    r"\b(saved\s+session|using\s+saved)\b.*\bvercel\b|"
    r"\bvercel\b.*\b(saved\s+session|using\s+saved)\b|"
    r"\b(give|want|show|list).*\b(services?|apps?|projects?).*\bvercel\b|"
    r"\bvercel\b.*\b(deployed|deployment)\b.*\b(list|show)\b",
    re.I,
)

_VERCEL_MUTATION_RX = re.compile(
    r"\b(restart|redeploy|delete|remove|destroy|rollback|scale|purge|kill)\b.*\b"
    r"(app|service|project|deployment|instance)\b|"
    r"\b(redeploy|restart|delete)\b.*\bvercel\b|"
    r"\bchange\b.*\b(environment\s+variable|env\s+var)\b|"
    r"\bvercel\b.*\b(redeploy|restart|delete)\b",
    re.I,
)

_VERCEL_AMBIGUOUS_RX = re.compile(
    r"^\s*(help\s+(me\s+)?with\s+vercel|vercel\s+help|about\s+vercel)\s*[?.!]?\s*$",
    re.I,
)


def _raw(text: str) -> str:
    return (text or "").strip()


def mentions_vercel(text: str) -> bool:
    return bool(_VERCEL_RX.search(_raw(text)))


def is_browser_status_request(text: str) -> bool:
    return bool(_BROWSER_STATUS_RX.search(_raw(text)))


def _matches_login(raw: str) -> bool:
    if _BROWSER_LOGIN_RX.search(raw):
        return True
    if mentions_vercel(raw) and re.search(
        r"\b(log\s*in|login|sign\s*in|authenticate|auth)\b", raw, re.I
    ):
        return True
    return False


def _matches_session_open(raw: str) -> bool:
    if _BROWSER_NAV_LEGACY_RX.search(raw):
        return True
    has_vercel = mentions_vercel(raw)
    has_launch = bool(_LAUNCH_RX.search(raw))
    has_session = bool(_SESSION_RX.search(raw))
    has_dashboard = bool(_DASHBOARD_RX.search(raw))
    has_supervised = bool(_SUPERVISED_RX.search(raw))
    has_browser_word = bool(re.search(r"\bbrowser\b", raw, re.I))
    if has_supervised and has_vercel and (has_session or has_browser_word):
        return True
    if has_launch and has_vercel and (has_session or has_dashboard or has_browser_word):
        return True
    if has_browser_word and has_vercel and (has_launch or has_session or has_dashboard):
        return True
    if re.search(r"\bconnect\s+to\b", raw, re.I) and has_vercel and has_dashboard:
        return True
    if re.search(r"\bbrowser\s+automation\b", raw, re.I) and has_vercel and has_launch:
        return True
    return False


def _matches_inspection(raw: str) -> bool:
    from aethos_core.conversation.provider_memory.active_provider_context import (
        explicit_provider_in_prompt,
        is_provider_neutral_health_phrase,
    )

    if is_provider_neutral_health_phrase(raw) and explicit_provider_in_prompt(raw) != "vercel":
        return False
    if not mentions_vercel(raw) and not re.search(
        r"\b(apps?|projects?|services?|deployment)\b", raw, re.I
    ):
        return False
    return bool(_VERCEL_READONLY_RX.search(raw))


def _matches_mutation(raw: str) -> bool:
    return bool(_VERCEL_MUTATION_RX.search(raw))


def is_browser_login_request(text: str) -> bool:
    raw = _raw(text)
    return bool(raw) and _matches_login(raw)


def is_browser_session_request(text: str) -> bool:
    """Supervised session launch — fuzzy open + vercel + session/dashboard/browser."""
    raw = _raw(text)
    if not raw:
        return False
    if is_browser_status_request(raw):
        return False
    if _matches_mutation(raw) or _matches_inspection(raw) or _matches_login(raw):
        return False
    return _matches_session_open(raw)


def is_vercel_inspection_request(text: str) -> bool:
    raw = _raw(text)
    if not raw:
        return False
    if _matches_mutation(raw) or _matches_session_open(raw) or _matches_login(raw):
        return False
    return _matches_inspection(raw)


def is_vercel_mutation_request(text: str) -> bool:
    raw = _raw(text)
    return bool(raw) and _matches_mutation(raw)


def is_vercel_ambiguous_request(text: str) -> bool:
    return bool(_VERCEL_AMBIGUOUS_RX.search(_raw(text)))


def is_operational_browser_intent(text: str) -> bool:
    """Any high-confidence operational route that must not hit provider first."""
    return (
        is_browser_status_request(text)
        or is_browser_session_request(text)
        or is_browser_login_request(text)
        or is_vercel_inspection_request(text)
        or is_vercel_mutation_request(text)
        or is_vercel_ambiguous_request(text)
    )


def classify_operational_intent(text: str) -> IntentKind:
    raw = _raw(text)
    if not raw:
        return None
    if is_vercel_mutation_request(raw):
        return "vercel_mutation"
    if is_vercel_inspection_request(raw):
        return "vercel_inspection"
    if is_browser_status_request(raw):
        return "browser_status"
    if is_browser_login_request(raw):
        return "browser_login"
    if is_browser_session_request(raw):
        return "browser_session_open"
    if is_vercel_ambiguous_request(raw):
        return "vercel_ambiguous"
    return None


def vercel_ambiguous_clarification_reply() -> str:
    return (
        "**How do you want to work with Vercel?**\n\n"
        "Pick one path:\n"
        "1. **Supervised browser session** — open the dashboard after approval; you log in manually.\n"
        "2. **Read-only inspection** — list apps/projects or health using a saved session (if you opted in).\n"
        "3. **CLI probe** — read-only `vercel` checks after approval.\n"
        "4. **Planning** — deployment or architecture notes (no live dashboard actions).\n\n"
        "I will not guess or give generic setup tutorials for operational tasks."
    )
