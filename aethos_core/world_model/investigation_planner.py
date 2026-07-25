# SPDX-License-Identifier: Apache-2.0
"""Investigation action planning from world model."""

from __future__ import annotations

from aethos_core.world_model.investigation_state import InvestigationState


def plan_next_action_from_state(state: InvestigationState) -> tuple[str, str]:
    if state.next_best_action:
        return state.next_best_action, state.next_best_action_key or "planned"
    if "stale_service_events" in state.evidence:
        return (
            "Refresh Railway service events and inspect logs around the latest failure window.",
            "refresh_events_and_fetch_failure_window_logs",
        )
    if "logs_unavailable" in state.evidence:
        return ("Fetch deployment/runtime logs near the failure timestamp.", "fetch_failure_window_logs")
    return ("Inspect surrounding logs and Railway service events before proposing mutation.", "investigate")


def mark_completed_check(state: InvestigationState, check: str) -> InvestigationState:
    label = (check or "").strip()
    if label and label not in state.completed_checks:
        state.completed_checks.append(label)
    return state
