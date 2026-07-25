# SPDX-License-Identifier: Apache-2.0
"""Intent detection for Railway service creation execution simulation (dry-run)."""

from __future__ import annotations

import re

_RUN_SIM_RX = re.compile(
    r"\b("
    r"simulate\s+railway\s+service\s+creation"
    r"|dry\s*[- ]?run\s+railway\s+service\s+creation"
    r"|check\s+if\s+railway\s+service\s+creation\s+can\s+execute"
    r"|validate\s+railway\s+service\s+creation\s+execution"
    r"|run\s+railway\s+service\s+creation\s+(?:execution\s+)?simulation"
    r")\b",
    re.I,
)

_SHOW_SIM_RX = re.compile(
    r"\bshow\s+(?:the\s+)?(?:saved\s+)?railway\s+service\s+creation\s+simulation\b",
    re.I,
)

_BLOCKING_RX = re.compile(
    r"\b("
    r"why\s+can'?t\s+(?:it|railway\s+service\s+creation)\s+execute\s+yet"
    r"|what\s+is\s+blocking\s+(?:railway\s+)?(?:service\s+creation\s+)?execution"
    r"|what\s+(?:is\s+)?blocking\s+execution"
    r")\b",
    re.I,
)

_PASSED_RX = re.compile(
    r"\bwhat\s+passed\s+in\s+the\s+dry\s*[- ]?run\b",
    re.I,
)

_FAILED_RX = re.compile(
    r"\bwhat\s+failed\s+in\s+the\s+dry\s*[- ]?run\b",
    re.I,
)


def is_railway_service_creation_simulator_run_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _RUN_SIM_RX.search(raw))


def is_railway_service_creation_simulator_show_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _SHOW_SIM_RX.search(raw))


def is_railway_service_creation_simulator_blocking_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _BLOCKING_RX.search(raw))


def is_railway_service_creation_simulator_passed_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _PASSED_RX.search(raw))


def is_railway_service_creation_simulator_failed_intent(text: str) -> bool:
    raw = (text or "").strip()
    return bool(raw and _FAILED_RX.search(raw))


def is_railway_service_creation_simulator_followup_intent(text: str) -> bool:
    return (
        is_railway_service_creation_simulator_blocking_intent(text)
        or is_railway_service_creation_simulator_passed_intent(text)
        or is_railway_service_creation_simulator_failed_intent(text)
    )


def is_railway_service_creation_simulator_intent(text: str) -> bool:
    return (
        is_railway_service_creation_simulator_run_intent(text)
        or is_railway_service_creation_simulator_show_intent(text)
        or is_railway_service_creation_simulator_followup_intent(text)
    )
