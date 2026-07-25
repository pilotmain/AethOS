# SPDX-License-Identifier: Apache-2.0
"""Voice governance — voice never bypasses governance."""

from __future__ import annotations

from typing import Any

FORBIDDEN_VOICE_ACTIONS = frozenset({
    "purchase",
    "bank_transfer",
    "credential_export",
    "privilege_escalation",
    "destructive_action",
    "hidden_browser_action",
    "silent_mutation",
})


def validate_voice_action(*, action_type: str, requires_approval: bool = True) -> dict[str, Any]:
    """All voice-initiated actions require explicit governance."""
    if action_type in FORBIDDEN_VOICE_ACTIONS:
        return {
            "ok": False,
            "blocked": True,
            "reason": f"Voice action '{action_type}' is never allowed.",
            "autonomous_execution_blocked": True,
        }
    if not requires_approval:
        return {
            "ok": False,
            "blocked": True,
            "reason": "Voice actions must route through approval-gated action runtime.",
            "autonomous_execution_blocked": True,
        }
    return {"ok": True, "requires_approval": True, "governance_path": "action_runtime"}


def voice_turn_policy(*, channel: str = "web_voice") -> dict[str, Any]:
    return {
        "ok": True,
        "channel": channel,
        "push_to_talk": True,
        "interruption_handling": "enabled",
        "hidden_actions_blocked": True,
        "governance_invariant": "Voice never bypasses governance.",
        "autonomous_execution_blocked": True,
    }
