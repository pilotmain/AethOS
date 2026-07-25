# SPDX-License-Identifier: Apache-2.0
"""Railway deployment truth — deployment state verification."""

from __future__ import annotations

from typing import Any


def assess_deployment_truth(
    *,
    provider_result: dict[str, Any],
    readonly_artifact: dict[str, Any],
    before_snapshot: dict[str, Any] | None = None,
    approved_at: str | float | None = None,
) -> dict[str, Any]:
    rollback = provider_result.get("rollback_metadata") or {}
    if not isinstance(rollback, dict):
        rollback = {}
    state_before = str(rollback.get("deployment_state_before") or provider_result.get("deployment_state_before") or "")
    state_after = str(rollback.get("deployment_state_after") or provider_result.get("deployment_state_after") or "")
    deployment_id = rollback.get("deployment_id") or provider_result.get("deployment_id")

    evidence = readonly_artifact.get("evidence") or readonly_artifact.get("items") or []
    observed_state = None
    if isinstance(evidence, list):
        for item in evidence:
            if isinstance(item, dict):
                observed_state = item.get("state") or item.get("status")
                if observed_state:
                    break

    snapshot_before = before_snapshot or rollback.get("deployment_snapshot_before")
    service_id = str(
        rollback.get("service_id")
        or provider_result.get("service_id")
        or (snapshot_before or {}).get("service_id")
        or ""
    )
    transition_detected = False
    restart_state = None
    if isinstance(snapshot_before, dict) and service_id:
        from aethos_core.providers.railway.hardening.restart_transition import verify_railway_restart_transition

        restart = verify_railway_restart_transition(
            service_id=service_id,
            before_snapshot=snapshot_before,
            approved_at=approved_at or rollback.get("approved_at"),
            provider_result=provider_result,
            readonly_artifact=readonly_artifact,
            provider_request_accepted=bool(provider_result.get("ok")),
        )
        transition_detected = restart.transition_detected
        restart_state = restart.state
    elif state_before and state_after and state_before != state_after:
        transition_detected = True

    stabilized = str(observed_state or state_after).lower() in ("success", "running", "ready", "active")

    return {
        "transition_detected": transition_detected,
        "stabilized": stabilized,
        "deployment_id": deployment_id,
        "state_before": state_before or None,
        "state_after": state_after or observed_state,
        "observed_state": observed_state,
        "restart_verification_state": restart_state,
    }
