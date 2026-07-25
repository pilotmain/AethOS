# SPDX-License-Identifier: Apache-2.0
"""Browser evidence policy — tiers T0–T3+, blocked interaction patterns."""

from __future__ import annotations

import re
from typing import Any

T0_METADATA = "T0"
T1_READONLY_CAPTURE = "T1"
T2_INTERACTIVE = "T2"
T3_BLOCKED = "T3"

_BLOCKED_INTERACTION_RX = re.compile(
    r"\b("
    r"click|submit|autofill|purchase|buy|pay|checkout|"
    r"captcha|force\s+click|auto[- ]?click|automatically\s+click|"
    r"hidden\s+click|form\s+submit|credential\s+harvest|"
    r"download|upload|inject\s+js|execute\s+script|eval\("
    r")\b",
    re.I,
)

_BLOCKED_CAPTURE_TYPES = frozenset({"click", "submit", "interaction", "mutation"})

_CAPTURE_TYPE_ALIASES: dict[str, str] = {
    "screenshot": "screenshot",
    "screen": "screenshot",
    "metadata": "metadata",
    "meta": "metadata",
    "page_metadata": "metadata",
    "full": "full",
    "deployment_evidence": "full",
    "evidence": "full",
}


def normalize_capture_type(value: str | None) -> str:
    key = (value or "screenshot").strip().lower()
    return _CAPTURE_TYPE_ALIASES.get(key, key)


def classify_user_request(text: str) -> dict[str, Any]:
    raw = (text or "").strip()
    if _BLOCKED_INTERACTION_RX.search(raw):
        return {
            "allowed": False,
            "risk_tier": T3_BLOCKED,
            "failure_class": "blocked_interaction",
            "detail": "Interactive or destructive browser actions are blocked in Phase 9.8B.",
        }
    capture_type = "metadata" if re.search(r"\b(metadata|inspect\s+page|page\s+metadata)\b", raw, re.I) else "screenshot"
    if re.search(r"\b(deployment\s+evidence|full\s+evidence|browser\s+evidence)\b", raw, re.I):
        capture_type = "full"
    return {
        "allowed": True,
        "risk_tier": T0_METADATA if capture_type == "metadata" else T1_READONLY_CAPTURE,
        "capture_type": capture_type,
        "approved": True,
    }


def evaluate_capture_request(
    *,
    url: str,
    capture_type: str,
    user_request: str = "",
    approved: bool = True,
) -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    normalized = normalize_capture_type(capture_type)
    if normalized in _BLOCKED_CAPTURE_TYPES:
        return _deny("blocked_capture_type", T3_BLOCKED, f"Capture type `{normalized}` is not allowed.")

    intent = classify_user_request(user_request)
    if not intent.get("allowed"):
        return intent

    if not settings.browser_automation_enabled:
        return _deny(
            "browser_disabled",
            T3_BLOCKED,
            "Browser automation is disabled. Set BROWSER_AUTOMATION_ENABLED=true and restart the API.",
        )

    if settings.browser_capture_approval_required and not approved:
        return _deny("approval_required", T2_INTERACTIVE, "Browser capture requires approval.")

    tier = T0_METADATA if normalized == "metadata" else T1_READONLY_CAPTURE
    if tier == T2_INTERACTIVE:
        return _deny("interactive_blocked", T3_BLOCKED, "Interactive browser tier is blocked in 9.8B.")

    if not url.strip():
        return _deny("missing_url", T3_BLOCKED, "Target URL is required.")

    return {
        "allowed": True,
        "risk_tier": tier,
        "capture_type": normalized,
        "approved": approved,
        "policy_tier": tier,
    }


def _deny(failure_class: str, tier: str, detail: str) -> dict[str, Any]:
    return {
        "allowed": False,
        "failure_class": failure_class,
        "risk_tier": tier,
        "detail": detail,
    }
