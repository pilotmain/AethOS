# SPDX-License-Identifier: Apache-2.0
"""Regression guardrails — live grounding must-not-regress checks."""

from __future__ import annotations

import re
from typing import Any

_BANNED = (
    "i need more context about which specific deployment",
    "i'd need more context",
    "executed the restart for you",
    "i restarted the service",
    "fully resolved",
    "completely healthy",
    "approval-gated execution",
    "i'm still thinking",
    "still thinking",
    "analyzing competitors",
    "the agents are analyzing",
    "recovery verified successfully",
    "the agents are working",
    "analyzing competitors right now",
)
_GOVERNANCE_SPAM = ("governance:", "autonomous execution blocked", "no autonomous action")
_FORMULAIC = ("extended monitoring remains active", "verification windows", "topology convergence")


def assess_regression_guardrails(*, reply: str, grounded: bool = True) -> dict[str, Any]:
    lower = reply.lower()
    violations: list[str] = []

    for phrase in _BANNED:
        if phrase in lower:
            violations.append(f"banned:{phrase}")

    if grounded:
        gov_hits = sum(1 for g in _GOVERNANCE_SPAM if g in lower)
        if gov_hits >= 2:
            violations.append("governance_spam")

    formulaic_hits = sum(1 for f in _FORMULAIC if f in lower)
    if formulaic_hits >= 3:
        violations.append("formulaic_density")

    if re.search(r"\bexecuted\b.*\b(restart|deploy|rerun)\b", lower):
        violations.append("fake_execution_claim")

    qualified = len(violations) == 0
    return {
        "guardrails_qualified": qualified,
        "violations": violations,
        "summary": "Live grounding regression guardrails clear." if qualified else f"Guardrail violations: {', '.join(violations)}.",
    }
