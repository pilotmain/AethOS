# SPDX-License-Identifier: Apache-2.0
"""Deterministic intent detection for provider deployment readiness prompts."""

from __future__ import annotations

import re
from typing import Literal

ProviderReadinessKind = Literal["railway", "vercel"]

_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_VERCEL_RX = re.compile(r"\bvercel\b", re.I)

_RAILWAY_READINESS_RX = re.compile(
    r"\b("
    r"railway\s+deployment\s+readiness"
    r"|deployment\s+readiness\s+(?:for\s+)?railway"
    r"|check\s+(?:if\s+)?(?:aethos\s+is\s+)?ready\s+(?:to\s+)?deploy(?:\s+\w+){0,6}\s+(?:to\s+)?railway"
    r"|(?:is\s+)?(?:aethos\s+)?ready\s+for\s+railway\s+deployment"
    r"|check\s+railway\s+deployment\s+readiness"
    r"|can\s+railway\s+deploy(?:\s+\w+){0,6}(?:\s+right\s+now|\s+now|\s+today)?"
    r"|what\s+is\s+blocking\s+railway\s+deployment"
    r"|is\s+(?:the\s+)?railway\s+service\s+configured"
    r"|show\s+railway\s+deployment\s+readiness(?:\s+report)?"
    r"|run\s+(?:railway\s+)?(?:deployment\s+)?readiness(?:\s+checks?)?"
    r")\b",
    re.I,
)

_VERCEL_READINESS_RX = re.compile(
    r"\b("
    r"vercel\s+deployment\s+readiness"
    r"|deployment\s+readiness\s+(?:for\s+)?vercel"
    r"|check\s+(?:if\s+)?(?:aethos\s+is\s+)?ready\s+(?:to\s+)?deploy(?:\s+\w+){0,6}\s+(?:to\s+)?vercel"
    r"|(?:is\s+)?(?:aethos\s+)?ready\s+for\s+vercel\s+deployment"
    r"|check\s+vercel\s+deployment\s+readiness"
    r"|what\s+is\s+blocking\s+vercel\s+deployment"
    r"|show\s+vercel\s+deployment\s+readiness(?:\s+report)?"
    r")\b",
    re.I,
)

_E2E_EXECUTION_EXCLUDE_RX = re.compile(
    r"\b("
    r"env(?:ironment)?(?:\s+vars?|\s+variables?)?"
    r"|config(?:ure|uration)?"
    r"|end[\s-]to[\s-]end"
    r"|e2e\b"
    r"|verify|report back"
    r")\b",
    re.I,
)


def _normalized(text: str) -> str:
    return (text or "").strip()


def is_railway_provider_e2e_readiness_intent(text: str) -> bool:
    raw = _normalized(text)
    if not raw or not _RAILWAY_RX.search(raw):
        return False
    return bool(_RAILWAY_READINESS_RX.search(raw))


def is_vercel_provider_e2e_readiness_intent(text: str) -> bool:
    raw = _normalized(text)
    if not raw or not _VERCEL_RX.search(raw):
        return False
    return bool(_VERCEL_READINESS_RX.search(raw))


def detect_provider_e2e_readiness_kind(text: str) -> ProviderReadinessKind | None:
    raw = _normalized(text)
    if not raw:
        return None
    railway = is_railway_provider_e2e_readiness_intent(raw)
    vercel = is_vercel_provider_e2e_readiness_intent(raw)
    if railway and vercel:
        return None
    if railway:
        return "railway"
    if vercel:
        return "vercel"
    return None


def is_provider_e2e_readiness_intent(text: str) -> bool:
    """Pure readiness inspection — not deploy+env+verify execution."""
    raw = _normalized(text)
    if not raw:
        return False
    from aethos_core.provider_e2e_execution.provider_e2e_execution_intent import is_provider_e2e_execution_intent

    if is_provider_e2e_execution_intent(raw):
        return False
    return detect_provider_e2e_readiness_kind(raw) is not None
