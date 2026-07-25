# SPDX-License-Identifier: Apache-2.0
"""Collaboration modes — companion, operator, mentor, executive, crisis."""

from __future__ import annotations

from typing import Any

from aethos_core.relational.human_signal_detection import detect_human_signals

MODES = frozenset({"companion", "operator", "mentor", "executive", "crisis", "coach"})


def select_collaboration_mode(
    text: str | None = None,
    *,
    operator_preference: str | None = None,
    operational_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Select adaptive interaction mode."""
    signals = detect_human_signals(text)
    ctx = operational_context or {}

    if signals.get("crisis") or ctx.get("truth_state") == "verification_failed":
        mode = "crisis"
        reason = "Crisis signals or verification failure — calm operational clarity."
    elif operator_preference and operator_preference in MODES:
        mode = operator_preference
        reason = f"Operator preference: {operator_preference}"
    elif signals.get("confused"):
        mode = "mentor"
        reason = "Confusion detected — explanatory mentor mode."
    elif signals.get("frustrated"):
        mode = "companion"
        reason = "Frustration detected — calmer companion guidance."
    elif any(k in (text or "").lower() for k in ("summary", "executive", "brief", "high level")):
        mode = "executive"
        reason = "Executive summary requested."
    elif any(k in (text or "").lower() for k in ("deploy", "workflow", "railway", "debug", "patch")):
        mode = "operator"
        reason = "Technical operational context — concise operator mode."
    else:
        mode = "companion"
        reason = "Default warm companion mode."

    return {
        "mode": mode,
        "reason": reason,
        "signals": signals,
        "verbosity": "low" if mode in ("crisis", "executive", "operator") else "medium",
        "warmth": "high" if mode in ("companion", "mentor", "coach") else "moderate",
    }
