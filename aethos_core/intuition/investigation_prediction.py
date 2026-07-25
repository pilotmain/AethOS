# SPDX-License-Identifier: Apache-2.0
"""Investigation prediction — anticipates next debugging steps."""

from __future__ import annotations

from typing import Any


def predict_investigation_steps(*, session_id: str = "default", context: str | None = None) -> dict[str, Any]:
    from aethos_core.human_centered.continuity_memory import load_continuity_memory

    record = load_continuity_memory(session_id=session_id)
    focus = (context or record.get("focus") or "").lower()
    steps: list[str] = []

    if "replay" in focus or "living" in focus:
        steps = [
            "investigate replay stitching across long-running sessions",
            "review human_runtime_replay artifacts",
            "generate a governed patch proposal",
            "summarize the operational timeline",
        ]
    elif "api" in focus or "route" in focus:
        steps = [
            "verify route registration in Runtime Integrity",
            "confirm Mission Control mcFetch alignment",
            "replay runtime integrity chain",
        ]
    else:
        steps = [
            "review continuity memory accuracy",
            "check Runtime Integrity route health",
            "open a calm collaboration room if needed",
        ]

    return {
        "ok": True,
        "predicted_steps": steps,
        "confidence": float(record.get("confidence") or 0.72),
        "autonomous_execution_blocked": True,
    }
