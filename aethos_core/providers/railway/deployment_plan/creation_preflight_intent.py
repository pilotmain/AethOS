# SPDX-License-Identifier: Apache-2.0
"""Intent detection for Railway new-service creation preflight (no execution)."""

from __future__ import annotations

import re

_CREATE_PREFLIGHT_RX = re.compile(
    r"\b("
    r"create\s+(?:a\s+)?(?:governed\s+)?railway\s+(?:new\s+)?service\s+(?:creation\s+)?preflight"
    r"|run\s+(?:a\s+)?railway\s+(?:new\s+)?service\s+(?:creation\s+)?preflight"
    r"|railway\s+(?:new\s+)?service\s+creation\s+preflight"
    r"|preflight\s+railway\s+(?:new\s+)?service\s+creation"
    r")\b",
    re.I,
)

_SHOW_PREFLIGHT_RX = re.compile(
    r"\bshow\s+(?:the\s+)?(?:saved\s+)?railway\s+(?:new\s+)?service\s+creation\s+preflight\b",
    re.I,
)

_APPROVE_PREFLIGHT_RX = re.compile(
    r"\b("
    r"approve\s+(?:the\s+)?railway\s+(?:new\s+)?service\s+creation\s+preflight"
    r"|confirm\s+(?:the\s+)?railway\s+(?:new\s+)?service\s+creation\s+preflight"
    r"|i\s+approve\s+(?:the\s+)?railway\s+(?:new\s+)?service\s+creation\s+preflight"
    r")\b",
    re.I,
)


def is_railway_service_creation_preflight_create_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _CREATE_PREFLIGHT_RX.search(raw))


def is_railway_service_creation_preflight_show_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _SHOW_PREFLIGHT_RX.search(raw))


def is_railway_service_creation_preflight_approve_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _APPROVE_PREFLIGHT_RX.search(raw))


def is_railway_service_creation_preflight_intent(text: str) -> bool:
    return (
        is_railway_service_creation_preflight_create_intent(text)
        or is_railway_service_creation_preflight_show_intent(text)
        or is_railway_service_creation_preflight_approve_intent(text)
    )
