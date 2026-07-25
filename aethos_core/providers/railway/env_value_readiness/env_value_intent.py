# SPDX-License-Identifier: Apache-2.0
"""Intent detection for Railway env value readiness."""

from __future__ import annotations

import re

_CHECK_RX = re.compile(
    r"\b("
    r"check\s+railway\s+env\s+value\s+readiness"
    r"|check\s+env\s+readiness\s+for\s+railway\s+deployment"
    r"|show\s+missing\s+railway\s+env\s+values"
    r"|what\s+env\s+values\s+are\s+missing"
    r")\b",
    re.I,
)

_CONFIGURE_RX = re.compile(
    r"\bhow\s+do\s+i\s+configure\s+env\s+values\s+securely\b",
    re.I,
)

_MARK_RX = re.compile(
    r"\bmark\s+railway\s+env\s+values\s+configured\b",
    re.I,
)

_REFRESH_RX = re.compile(
    r"\brefresh\s+railway\s+env\s+readiness\b",
    re.I,
)

_SECURE_SUMMARY_RX = re.compile(
    r"\bshow\s+secure\s+railway\s+env\s+readiness\b",
    re.I,
)

_MINIMUM_SECRETS_RX = re.compile(
    r"\bwhat\s+minimum\s+secrets\s+are\s+required\b",
    re.I,
)


def is_railway_env_value_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(
        raw
        and (
            _CHECK_RX.search(raw)
            or _CONFIGURE_RX.search(raw)
            or _MARK_RX.search(raw)
            or             _REFRESH_RX.search(raw)
            or _SECURE_SUMMARY_RX.search(raw)
            or _MINIMUM_SECRETS_RX.search(raw)
        )
    )


def is_railway_env_value_check_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _CHECK_RX.search(raw))


def is_railway_env_value_configure_intent(text: str) -> bool:
    return bool(_CONFIGURE_RX.search((text or "").strip()))


def is_railway_env_value_mark_intent(text: str) -> bool:
    return bool(_MARK_RX.search((text or "").strip()))


def is_railway_env_value_refresh_intent(text: str) -> bool:
    return bool(_REFRESH_RX.search((text or "").strip()))


def is_railway_env_value_secure_summary_intent(text: str) -> bool:
    return bool(_SECURE_SUMMARY_RX.search((text or "").strip()))


def is_railway_env_value_minimum_secrets_intent(text: str) -> bool:
    return bool(_MINIMUM_SECRETS_RX.search((text or "").strip()))
