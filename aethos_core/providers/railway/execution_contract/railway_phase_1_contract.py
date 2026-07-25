# SPDX-License-Identifier: Apache-2.0
"""
FIX 116 — Frozen Phase 1 Railway staging lifecycle contract (machine-readable).

Import this module in certification tests to prevent silent drift of phase order,
route IDs, and approval phrases before production hardening (FIX 117+).
"""

from __future__ import annotations

from typing import Final

from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    ROLLBACK_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_ROLLBACK_ACTION,
    DISABLE_DEPLOYS_ROLLBACK_ACTION,
    LIVE_ROLLBACK_DISPATCH_ORDER,
    LIVE_ROLLBACK_PHASES_FIX115,
    REMOVE_SERVICE_ROLLBACK_ACTION,
    REVERT_ENV_ROLLBACK_ACTION,
    SIMULATED_ONLY_ROLLBACK_PHASES_FIX115,
)

PHASE_1_FIX_RANGE: Final[str] = "FIX 108–FIX 115"
PHASE_1_FREEZE_FIX: Final[str] = "FIX 116"

# Governed forward path (staging live when flags + phrases allow).
PHASE_1_FORWARD_LIVE_ORDER: Final[tuple[str, ...]] = (
    "create_service",
    "connect_source",
    "configure_env",
    "trigger_deploy",
    "verify_runtime",
)

# Governed live rollback actions (staging only; production hard-blocked).
PHASE_1_ROLLBACK_LIVE_ACTIONS: Final[tuple[str, ...]] = (
    CONNECT_SOURCE_ROLLBACK_ACTION,
    REVERT_ENV_ROLLBACK_ACTION,
)

PHASE_1_ROLLBACK_SIMULATED_ACTIONS: Final[tuple[str, ...]] = (
    DISABLE_DEPLOYS_ROLLBACK_ACTION,
    REMOVE_SERVICE_ROLLBACK_ACTION,
)

PHASE_1_FORWARD_APPROVAL_PHRASE: Final[str] = NON_PRODUCTION_FINAL_PHRASE
PHASE_1_ROLLBACK_APPROVAL_PHRASE: Final[str] = ROLLBACK_FINAL_PHRASE

# Meta route_id for all execution_router prompts (sub-stage in execution_contract_stage).
PHASE_1_EXECUTION_ROUTE_ID: Final[str] = "railway_execution_contract"

# execution_contract_stage values certified for Phase 1 operator commands.
PHASE_1_EXECUTION_STAGES: Final[frozenset[str]] = frozenset(
    {
        "contract",
        "rollback",
        "rollback_readiness",
        "rollback_audit",
        "rollback_timeline",
        "rollback_receipts",
        "readiness_gate",
        "execution_requested",
        "execution_timeline",
        "receipts",
        "deploy_trigger_readiness",
        "runtime_verification_readiness",
        "rollback_executed",
    }
)

assert LIVE_ROLLBACK_DISPATCH_ORDER == (
    LIVE_ROLLBACK_PHASES_FIX115 + SIMULATED_ONLY_ROLLBACK_PHASES_FIX115
)
