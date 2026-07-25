# SPDX-License-Identifier: Apache-2.0
"""Execution state machine — single forward transition, explicit illegal-transition errors."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.execution_contract_models import (
    TERMINAL_STATES,
    ExecutionState,
)

# Allowed forward transitions (one step at a time).
_VALID_TRANSITIONS: dict[str, frozenset[str]] = {
    "draft": frozenset({"review_confirmed"}),
    "review_confirmed": frozenset({"preflight_created"}),
    "preflight_created": frozenset({"preflight_approved"}),
    "preflight_approved": frozenset({"simulation_complete"}),
    "simulation_complete": frozenset({"execution_requested"}),
    "execution_requested": frozenset({"execution_locked"}),
    "execution_locked": frozenset({"execution_phase_create_service"}),
    "execution_phase_create_service": frozenset(
        {"execution_phase_connect_source", "execution_partial_failure", "execution_failed"}
    ),
    "execution_phase_connect_source": frozenset(
        {"execution_phase_configure_env", "execution_partial_failure", "execution_failed"}
    ),
    "execution_phase_configure_env": frozenset(
        {"execution_phase_trigger_deploy", "execution_partial_failure", "execution_failed"}
    ),
    "execution_phase_trigger_deploy": frozenset(
        {"execution_phase_verify", "execution_partial_failure", "execution_failed"}
    ),
    "execution_phase_verify": frozenset(
        {"execution_completed", "execution_partial_failure", "execution_failed"}
    ),
    "execution_partial_failure": frozenset({"execution_rolled_back"}),
    "execution_failed": frozenset({"execution_rolled_back"}),
    "execution_completed": frozenset(),
    "execution_rolled_back": frozenset(),
}


class IllegalExecutionTransitionError(ValueError):
    """Raised when a state transition is not permitted by the contract."""

    def __init__(self, *, from_state: str, to_state: str, detail: str = "") -> None:
        self.from_state = from_state
        self.to_state = to_state
        message = f"Illegal execution transition: {from_state} -> {to_state}"
        if detail:
            message = f"{message} ({detail})"
        super().__init__(message)


def can_transition(*, from_state: str, to_state: str) -> bool:
    if from_state in TERMINAL_STATES and from_state != to_state:
        return False
    allowed = _VALID_TRANSITIONS.get(from_state, frozenset())
    return to_state in allowed


def assert_transition(*, from_state: str, to_state: str) -> None:
    if from_state == to_state:
        raise IllegalExecutionTransitionError(
            from_state=from_state,
            to_state=to_state,
            detail="no-op transition",
        )
    if not can_transition(from_state=from_state, to_state=to_state):
        raise IllegalExecutionTransitionError(from_state=from_state, to_state=to_state)


def transition_journal_state(
    journal: dict[str, Any],
    *,
    to_state: ExecutionState,
) -> dict[str, Any]:
    """Return updated journal after a validated single forward transition."""
    from_state = str(journal.get("state") or "draft")
    assert_transition(from_state=from_state, to_state=to_state)
    updated = dict(journal)
    updated["state"] = to_state
    history = list(updated.get("state_history") or [])
    history.append({"from": from_state, "to": to_state})
    updated["state_history"] = history
    return updated


def lifecycle_state_for_approvals(
    *,
    review_confirmed: bool,
    preflight_exists: bool,
    preflight_approved: bool,
    simulation_complete: bool,
) -> ExecutionState:
    """Map approval flags to the highest lifecycle-aligned execution state."""
    if simulation_complete and preflight_approved and review_confirmed:
        return "simulation_complete"
    if preflight_approved and review_confirmed:
        return "preflight_approved"
    if preflight_exists and review_confirmed:
        return "preflight_created"
    if review_confirmed:
        return "review_confirmed"
    return "draft"
