# SPDX-License-Identifier: Apache-2.0
"""Models and constants for the Railway execution contract."""

from __future__ import annotations

from typing import Final, Literal

ExecutionState = Literal[
    "draft",
    "review_confirmed",
    "preflight_created",
    "preflight_approved",
    "simulation_complete",
    "execution_requested",
    "execution_locked",
    "execution_phase_create_service",
    "execution_phase_connect_source",
    "execution_phase_configure_env",
    "execution_phase_trigger_deploy",
    "execution_phase_verify",
    "execution_completed",
    "execution_partial_failure",
    "execution_rolled_back",
    "execution_failed",
]

ExecutionPhaseName = Literal[
    "create_service",
    "connect_source",
    "configure_env",
    "trigger_deploy",
    "verify_runtime",
]

def execution_runtime_allows_real_mutation() -> bool:
    """Runtime policy allows real greenfield Railway mutations (default false)."""
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        execution_runtime_allows_real_mutation as _policy_allows,
    )

    return _policy_allows()


# Back-compat alias — prefer execution_runtime_allows_real_mutation() or enablement policy.
EXECUTION_ENABLED: Final[bool] = False

EXECUTION_PHASES: Final[tuple[ExecutionPhaseName, ...]] = (
    "create_service",
    "connect_source",
    "configure_env",
    "trigger_deploy",
    "verify_runtime",
)

# FIX 108 — only create_service may perform live Railway mutations.
REAL_MUTATION_PHASES_FIX108: Final[tuple[ExecutionPhaseName, ...]] = ("create_service",)

# FIX 109 — only connect_source may perform live GitHub binding mutations.
REAL_MUTATION_PHASES_FIX109: Final[tuple[ExecutionPhaseName, ...]] = ("connect_source",)

# FIX 112 — only configure_env may perform live secure-store env writes.
REAL_MUTATION_PHASES_FIX112: Final[tuple[ExecutionPhaseName, ...]] = ("configure_env",)

# FIX 113 — only trigger_deploy may perform live Railway deployment trigger.
REAL_MUTATION_PHASES_FIX113: Final[tuple[ExecutionPhaseName, ...]] = ("trigger_deploy",)

# FIX 114 — verify_runtime is readonly (receipt phase only; no Railway mutation).
VERIFY_RUNTIME_PHASE: Final[ExecutionPhaseName] = "verify_runtime"

STATE_TO_PHASE: Final[dict[str, ExecutionPhaseName]] = {
    "execution_phase_create_service": "create_service",
    "execution_phase_connect_source": "connect_source",
    "execution_phase_configure_env": "configure_env",
    "execution_phase_trigger_deploy": "trigger_deploy",
    "execution_phase_verify": "verify_runtime",
}

PHASE_TO_STATE: Final[dict[ExecutionPhaseName, ExecutionState]] = {
    phase: state  # type: ignore[misc]
    for state, phase in STATE_TO_PHASE.items()
}

TERMINAL_STATES: Final[frozenset[str]] = frozenset(
    {
        "execution_completed",
        "execution_partial_failure",
        "execution_rolled_back",
        "execution_failed",
    }
)

LOCK_STALE_SECONDS: Final[int] = 3600

ROLLBACK_ACTIONS: Final[tuple[str, ...]] = (
    "remove_created_service",
    "disconnect_repo_source",
    "disable_deploys",
    "revert_env_writes",
    "mark_execution_rolled_back",
)
