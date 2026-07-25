# SPDX-License-Identifier: Apache-2.0
"""Intent detection for Railway new-service deployment plan artifacts."""

from __future__ import annotations

import re

_PLAN_RX = re.compile(
    r"\b("
    r"create\s+(?:a\s+)?railway\s+deployment\s+plan"
    r"|prepare\s+(?:a\s+)?(?:new\s+)?railway\s+service\s+plan"
    r"|railway\s+new\s+service\s+deployment\s+plan"
    r"|new\s+railway\s+service\s+deployment\s+plan"
    r"|railway\s+deployment\s+plan\s+for"
    r"|deployment\s+plan\s+for\s+.*\brailway\b"
    r")\b",
    re.I,
)

_SHOW_SAVED_PLAN_RX = re.compile(
    r"\bshow\s+(?:the\s+)?(?:saved\s+)?railway\s+deployment\s+plan\b",
    re.I,
)

_REVIEW_PLAN_RX = re.compile(
    r"\b(?:review|show\s+review\s+for)\s+(?:the\s+)?railway\s+deployment\s+plan\b",
    re.I,
)

_CONFIRM_PLAN_RX = re.compile(
    r"\b("
    r"confirm\s+(?:the\s+)?railway\s+deployment\s+plan"
    r"|approve\s+(?:the\s+)?railway\s+deployment\s+plan"
    r"|i\s+confirm\s+(?:the\s+)?railway\s+deployment\s+plan"
    r"|railway\s+deployment\s+plan\s+(?:approved|confirmed)"
    r")\b",
    re.I,
)

_COMPLETE_PLAN_RX = re.compile(
    r"\b("
    r"inspect\s+repo\s+and\s+complete\s+(?:the\s+)?railway\s+deployment\s+plan"
    r"|complete\s+(?:the\s+)?railway\s+deployment\s+plan"
    r"|railway\s+deployment\s+plan\s+completion"
    r")\b",
    re.I,
)

_EXISTING_SERVICE_RX = re.compile(
    r"\b(?:restart|re-?deploy)\b.*\b(?:pilotos|pilotos-api|mongodb)\b",
    re.I,
)


def is_railway_deployment_plan_intent(text: str) -> bool:
    """True for any Railway new-service deployment plan lane (create/show/complete)."""
    return is_railway_new_service_plan_intent(text)


def is_railway_deployment_plan_review_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _REVIEW_PLAN_RX.search(raw))


def is_railway_deployment_plan_confirm_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _CONFIRM_PLAN_RX.search(raw))


def is_railway_deployment_plan_complete_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _COMPLETE_PLAN_RX.search(raw))


def is_show_railway_deployment_plan_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _SHOW_SAVED_PLAN_RX.search(raw))


def is_railway_new_service_plan_intent(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if _EXISTING_SERVICE_RX.search(raw):
        return False
    from aethos_core.chat.local_system_guidance import is_local_aethos_api_restart_intent

    if is_local_aethos_api_restart_intent(raw):
        return False
    if _SHOW_SAVED_PLAN_RX.search(raw):
        return True
    if is_railway_deployment_plan_complete_intent(raw):
        return True
    if is_railway_deployment_plan_review_intent(raw):
        return True
    if is_railway_deployment_plan_confirm_intent(raw):
        return True
    return bool(_PLAN_RX.search(raw))
