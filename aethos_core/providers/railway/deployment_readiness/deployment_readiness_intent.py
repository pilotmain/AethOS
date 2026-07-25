# SPDX-License-Identifier: Apache-2.0
"""Intent detection for Railway new-service deployment readiness."""

from __future__ import annotations

import re

_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)

_NEW_SERVICE_RX = re.compile(
    r"\b("
    r"create\s+(?:a\s+)?(?:new\s+)?(?:railway\s+)?service"
    r"|new\s+(?:railway\s+)?service(?:\s+deployment)?"
    r"|deploy\s+(?:a\s+)?(?:brand[\s-]?new\s+)?(?:railway\s+)?service"
    r"|deploy\s+(?:to\s+)?railway\s+from\s+scratch"
    r"|greenfield\s+railway"
    r"|railway\s+service\s+creation"
    r"|railway\s+new\s+service"
    r")\b",
    re.I,
)

_READINESS_RX = re.compile(
    r"\b("
    r"railway\s+deployment\s+readiness"
    r"|deployment\s+readiness\s+(?:for\s+)?railway"
    r"|run\s+(?:railway\s+)?(?:deployment\s+)?readiness(?:\s+checks?)?"
    r"|railway\s+readiness\s+checks?"
    r"|check\s+(?:if\s+)?(?:we\s+can\s+)?deploy\s+(?:a\s+)?new\s+(?:railway\s+)?service"
    r")\b",
    re.I,
)

_CAPABILITY_NEW_SERVICE_RX = re.compile(
    r"\b("
    r"can\s+you\s+deploy\s+(?:a\s+)?(?:brand[\s-]?new\s+)?(?:railway\s+)?service"
    r"|can\s+(?:you|aethos)\s+create\s+(?:a\s+)?(?:new\s+)?railway\s+service"
    r"|are\s+you\s+capable\s+of\s+(?:creating|deploying)\s+(?:a\s+)?(?:new\s+)?railway\s+service"
    r"|can\s+aethos\s+deploy\s+(?:a\s+)?new\s+service\s+(?:on\s+)?railway"
    r")\b",
    re.I,
)

_EXISTING_MUTATION_ONLY_RX = re.compile(
    r"^\s*(?:please\s+)?(?:restart|re-?deploy)(?:\s+(?:the\s+)?)?[\w.-]+\s*(?:in\s+railway)?\s*\.?\s*$",
    re.I,
)


def _is_existing_railway_mutation_only(text: str) -> bool:
    raw = (text or "").strip()
    if _EXISTING_MUTATION_ONLY_RX.match(raw):
        return True
    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent

    intent = detect_explicit_mutation_intent(raw)
    if intent is not None and intent.provider == "railway" and intent.operation in {"restart", "redeploy", "rollback"}:
        if intent.confidence >= 0.75 and "new" not in raw.lower() and "create" not in raw.lower():
            return True
    return False


def is_railway_new_service_capability_question(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_CAPABILITY_NEW_SERVICE_RX.search(raw))


def is_railway_deployment_readiness_intent(text: str) -> bool:
    """True when the turn should be owned by Railway deployment readiness (readonly plan lane)."""
    raw = (text or "").strip()
    if not raw:
        return False
    if _is_existing_railway_mutation_only(raw):
        return False
    from aethos_core.provider_e2e_readiness.readiness_intent import is_railway_provider_e2e_readiness_intent

    if is_railway_provider_e2e_readiness_intent(raw):
        return True
    if is_railway_new_service_capability_question(raw):
        return True
    if _READINESS_RX.search(raw):
        return True
    if _NEW_SERVICE_RX.search(raw) and (_RAILWAY_RX.search(raw) or "from scratch" in raw.lower()):
        return True
    if _NEW_SERVICE_RX.search(raw) and re.search(r"\bnew\b", raw, re.I):
        return True
    return False
