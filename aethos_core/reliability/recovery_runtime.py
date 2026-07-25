# SPDX-License-Identifier: Apache-2.0
"""Recovery runtime — graceful degraded-state handling."""

from __future__ import annotations

from typing import Any


def assess_recovery_options(
    *,
    reliability: dict[str, Any],
    replay_integrity: dict[str, Any] | None = None,
    telemetry: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Recommend bounded recovery actions — never autonomous execution."""
    truth = str(reliability.get("truth_state") or "")
    replay = replay_integrity or reliability.get("replay_integrity") or {}
    tel = telemetry or {}

    options: list[dict[str, Any]] = []
    if truth in ("replay_incomplete", "degraded_confidence"):
        options.append(
            {
                "action": "replay_repair",
                "label": "Reconstruct missing replay evidence (readonly)",
                "bounded_retries": 2,
                "autonomous": False,
            }
        )
    if bool(tel.get("stale")) or str(tel.get("telemetry_quality")) == "low":
        options.append(
            {
                "action": "telemetry_refresh",
                "label": "Refresh stale telemetry via governed observation cycle",
                "bounded_retries": 1,
                "autonomous": False,
            }
        )
    if truth == "execution_unverified":
        options.append(
            {
                "action": "verification_retry",
                "label": "Bounded verification retry (approval required)",
                "bounded_retries": 2,
                "autonomous": False,
            }
        )
    if replay.get("repair_recommended"):
        options.append(
            {
                "action": "replay_reconstruct",
                "label": "Incident replay reconstruction from available evidence",
                "bounded_retries": 1,
                "autonomous": False,
            }
        )

    return {
        "degraded_mode": truth not in ("verified_healthy",),
        "recovery_options": options[:4],
        "provider_fallback": "readonly_secondary_routes",
        "autonomous_execution_blocked": True,
        "hidden_retries_blocked": True,
    }


def execute_bounded_recovery(*, action: str, operator_id: str = "default") -> dict[str, Any]:
    """Execute bounded recovery — readonly only, no silent mutations."""
    allowed = {"replay_repair", "telemetry_refresh", "verification_retry", "replay_reconstruct"}
    if action not in allowed:
        return {"ok": False, "error": "recovery_action_not_allowed", "autonomous_execution_blocked": True}

    if action == "telemetry_refresh":
        from aethos_core.operations.reality_loop import run_reality_loop_cycle

        cycle = run_reality_loop_cycle(source=f"recovery:{operator_id}")
        return {"ok": True, "action": action, "cycle": {"replay_id": cycle.get("replay_id")}, "readonly": True}

    if action in ("replay_repair", "replay_reconstruct"):
        from aethos_core.replay_intelligence.incident_reconstruction import reconstruct_incident_timeline

        story = reconstruct_incident_timeline(window_hours=48)
        return {"ok": True, "action": action, "reconstruction": story, "readonly": True}

    return {
        "ok": True,
        "action": action,
        "status": "verification_retry_queued",
        "approval_required": True,
        "autonomous_execution_blocked": True,
    }
