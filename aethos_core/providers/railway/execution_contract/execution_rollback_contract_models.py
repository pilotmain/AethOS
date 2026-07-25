# SPDX-License-Identifier: Apache-2.0
"""FIX 110 — Rollback contract models (connect_source scope)."""

from __future__ import annotations

from typing import Final

# Forward phase and its governed rollback receipt phase (dry-run / future live).
CONNECT_SOURCE_FORWARD_PHASE: Final[str] = "connect_source"
CONNECT_SOURCE_ROLLBACK_PHASE: Final[str] = "rollback_connect_source"
CONNECT_SOURCE_ROLLBACK_ACTION: Final[str] = "disconnect_repo_source"

# FIX 110 — dry-run rollback steps (simulate only).
CONNECT_SOURCE_ROLLBACK_STEPS: Final[tuple[str, ...]] = (
    "verify_connect_source_forward_receipt",
    "simulate_disconnect_repo_source",
    "record_rollback_connect_source_receipt",
    "update_rollback_journal_disconnect_planned",
)

# FIX 111 — live rollback action (disconnect_repo_source adapter).
REAL_ROLLBACK_ACTIONS_FIX111: Final[tuple[str, ...]] = (CONNECT_SOURCE_ROLLBACK_ACTION,)

CONNECT_SOURCE_LIVE_ROLLBACK_STEPS: Final[tuple[str, ...]] = (
    "verify_connect_source_forward_mutation_receipt",
    "disconnect_repo_source",
    "record_rollback_connect_source_receipt",
    "update_rollback_journal_disconnect_completed",
)

# FIX 115 — live env rollback (revert_env_writes).
REVERT_ENV_ROLLBACK_ACTION: Final[str] = "revert_env_writes"
REVERT_ENV_ROLLBACK_PHASE: Final[str] = "rollback_configure_env"
DISABLE_DEPLOYS_ROLLBACK_ACTION: Final[str] = "disable_deploys"
DISABLE_DEPLOYS_ROLLBACK_PHASE: Final[str] = "rollback_disable_deploys"
REMOVE_SERVICE_ROLLBACK_ACTION: Final[str] = "remove_created_service"
REMOVE_SERVICE_ROLLBACK_PHASE: Final[str] = "rollback_remove_created_service"

LIVE_ROLLBACK_PHASES_FIX115: Final[tuple[str, ...]] = (
    CONNECT_SOURCE_ROLLBACK_PHASE,
    REVERT_ENV_ROLLBACK_PHASE,
)

SIMULATED_ONLY_ROLLBACK_PHASES_FIX115: Final[tuple[str, ...]] = (
    DISABLE_DEPLOYS_ROLLBACK_PHASE,
    REMOVE_SERVICE_ROLLBACK_PHASE,
)

LIVE_ROLLBACK_DISPATCH_ORDER: Final[tuple[str, ...]] = (
    CONNECT_SOURCE_ROLLBACK_PHASE,
    REVERT_ENV_ROLLBACK_PHASE,
    DISABLE_DEPLOYS_ROLLBACK_PHASE,
    REMOVE_SERVICE_ROLLBACK_PHASE,
)
