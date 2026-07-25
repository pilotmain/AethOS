# SPDX-License-Identifier: Apache-2.0
"""Thinking boundaries — continuous analysis without autonomous execution."""

from __future__ import annotations

from typing import Any

ALLOWED_CAPABILITIES = frozenset({
    "continuous_analysis",
    "operational_recommendations",
    "replay_reconstruction",
    "governed_preflight_generation",
    "investigation_planning",
    "hypothesis_generation",
    "confidence_explanation",
})

FORBIDDEN_CAPABILITIES = frozenset({
    "silent_execution",
    "self_authorized_mutation",
    "hidden_browser_actions",
    "unrestricted_shell",
    "autonomous_deploy",
    "credential_export",
})


def assess_thinking_boundaries(*, proposed_capability: str | None = None) -> dict[str, Any]:
    """Think continuously. Act only with governance."""
    if proposed_capability:
        if proposed_capability in FORBIDDEN_CAPABILITIES:
            return {
                "ok": False,
                "allowed": False,
                "capability": proposed_capability,
                "reason": "Forbidden — autonomous execution blocked.",
                "autonomous_execution_blocked": True,
            }
        if proposed_capability in ALLOWED_CAPABILITIES:
            return {"ok": True, "allowed": True, "capability": proposed_capability, "requires_approval_for_action": True}

    return {
        "ok": True,
        "principle": "Think continuously. Act only with governance.",
        "allowed": sorted(ALLOWED_CAPABILITIES),
        "forbidden": sorted(FORBIDDEN_CAPABILITIES),
        "autonomous_execution_blocked": True,
    }
