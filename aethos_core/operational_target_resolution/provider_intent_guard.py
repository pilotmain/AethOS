# SPDX-License-Identifier: Apache-2.0
"""Provider intent guards — prevent Vercel/Railway cross-routing."""

from __future__ import annotations

import re

_EXPLICIT_PROVIDER_RX = re.compile(r"\b(railway|vercel|github|docker|kubernetes|aws|gcp|azure)\b", re.I)
_DEPLOY_VERB_RX = re.compile(r"\b(?:deploye?|deploy(?:ment)?|redeploy)\b", re.I)
_DIAGNOSTIC_INTENT_RX = re.compile(
    r"\b(?:error|fail(?:ed|ure)?|fix|broken|check|investigate|diagnos(?:e|is)|health|logs?|status|report\s+back)\b",
    re.I,
)
_RAILWAY_DEPLOY_OR_RESTART_RX = re.compile(
    r"\b(?:restart|redeploy|re-?deploy)\b.*\b(?:railway|pilotos-api|pilotos|pilotcore)\b"
    r"|\b(?:restart|redeploy)\b.*\b(?:in|on)\s+railway\b"
    r"|\brailway\b.*\b(?:restart|redeploy)\b",
    re.I,
)
_GARBAGE_PROJECT_HINTS = frozenset(
    {
        "vercel",
        "railway",
        "github",
        "deployment",
        "deployments",
        "deploy",
        "deploye",
        "error",
        "errors",
        "fix",
        "the",
        "and",
        "report",
        "back",
        "anything",
        "needed",
        "remote",
        "repo",
        "from",
        "any",
        "there",
        "health",
        "logs",
        "both",
        "them",
        "those",
        "these",
        "it",
        "everything",
        "all",
        "each",
        "every",
        "projects",
        "project",
        "services",
        "service",
        "apps",
        "app",
        "ui",
        "api",
        "stage",
        "staging",
        "latest",
        "commits",
        "commit",
        "changes",
        "change",
        "git",
        "hub",
        "github",
        "production",
        "main",
        "branch",
    }
)


def primary_explicit_provider(text: str) -> str:
    """When multiple providers appear, infer which one the user is operating on."""
    raw = (text or "").strip()
    if not raw:
        return ""
    providers = [m.group(1).lower() for m in _EXPLICIT_PROVIDER_RX.finditer(raw)]
    if not providers:
        return ""
    if len(providers) == 1:
        return providers[0]

    deploy_anchor = re.search(
        r"\b(?:redeploy|deploy(?:ment)?)\b[^.?!]{0,120}?\b(?:to\s+)?(railway|vercel)\b"
        r"|\b(?:to\s+)?(railway|vercel)\b[^.?!]{0,120}?\b(?:redeploy|deploy(?:ment)?)\b",
        raw,
        re.I,
    )
    if deploy_anchor:
        return (deploy_anchor.group(1) or deploy_anchor.group(2) or "").lower()

    diagnostic_anchor = re.search(
        r"\b(?:check|inspect|error|logs?|health|diagnos(?:e|is))\b[^.?!]{0,120}?\b(?:on|in)\s+(railway|vercel)\b"
        r"|\b(?:on|in)\s+(railway|vercel)\b[^.?!]{0,120}?\b(?:check|inspect|error|logs?|health)\b",
        raw,
        re.I,
    )
    if diagnostic_anchor:
        return (diagnostic_anchor.group(1) or diagnostic_anchor.group(2) or "").lower()

    return providers[-1]


def is_valid_vercel_project_hint(name: str) -> bool:
    token = (name or "").strip().lower()
    if not token or len(token) < 2:
        return False
    if token in _GARBAGE_PROJECT_HINTS:
        return False
    if token.isdigit():
        return False
    return True


def blocks_provider_readonly_diagnostics_route(text: str) -> bool:
    """True when the user wants deploy/mutation — not readonly provider diagnostics."""
    raw = (text or "").strip()
    if not raw:
        return False

    if _DEPLOY_VERB_RX.search(raw) and re.search(r"\brailway\b", raw, re.I):
        return True

    if re.search(r"\bgithub\b", raw, re.I) and re.search(r"\brailway\b", raw, re.I) and _DEPLOY_VERB_RX.search(raw):
        return True

    primary = primary_explicit_provider(raw)
    if primary == "railway" and (_DEPLOY_VERB_RX.search(raw) or _DIAGNOSTIC_INTENT_RX.search(raw)):
        return True

    from aethos_core.providers.railway.greenfield_deployment.greenfield_intent import (
        is_railway_greenfield_deployment_intent,
    )

    if is_railway_greenfield_deployment_intent(raw):
        return True

    if _RAILWAY_DEPLOY_OR_RESTART_RX.search(raw):
        return True

    return False


def requires_vercel_in_text_for_readonly(text: str, *, project_hint: str = "") -> bool:
    """Vercel readonly requires an explicit Vercel mention or a validated project hint."""
    raw = (text or "").strip()
    if re.search(r"\bvercel\b", raw, re.I):
        return True
    return bool(project_hint and is_valid_vercel_project_hint(project_hint))


def should_infer_vercel_readonly_from_text(text: str) -> bool:
    raw = (text or "").strip()
    if blocks_provider_readonly_diagnostics_route(raw):
        return False
    primary = primary_explicit_provider(raw)
    if primary and primary != "vercel":
        return False
    if not re.search(r"\bvercel\b", raw, re.I):
        return False
    return bool(_DIAGNOSTIC_INTENT_RX.search(raw))
