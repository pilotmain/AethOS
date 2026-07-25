# SPDX-License-Identifier: Apache-2.0
"""FIX 118 — Production shadow rehearsal phase contract (isolated from staging dry-run)."""

from __future__ import annotations

from typing import Final

ShadowForwardPhase = str
ShadowRollbackPhase = str

PRODUCTION_SHADOW_EXECUTION_MODE: Final[str] = "production_shadow"

PRODUCTION_VERIFICATION_SHADOW_PHASE: Final[str] = "verify_runtime_shadow"

FORWARD_SHADOW_PHASES: Final[tuple[ShadowForwardPhase, ...]] = (
    "create_service_shadow",
    "connect_source_shadow",
    "configure_env_shadow",
    "trigger_deploy_shadow",
    PRODUCTION_VERIFICATION_SHADOW_PHASE,
)

ROLLBACK_SHADOW_PHASES: Final[tuple[ShadowRollbackPhase, ...]] = (
    "disconnect_repo_source_shadow",
    "revert_env_writes_shadow",
    "disable_deploys_shadow",
    "remove_created_service_shadow",
    "rollback_shadow_finalize",
)

FULL_SHADOW_TIMELINE: Final[tuple[str, ...]] = FORWARD_SHADOW_PHASES + ("rollback_shadow",)

# Map shadow phases to policy assessment labels (not staging phase names).
SHADOW_PHASE_POLICY_LABELS: Final[dict[str, str]] = {
    "create_service_shadow": "forward_create_service",
    "connect_source_shadow": "forward_connect_source",
    "configure_env_shadow": "forward_configure_env",
    "trigger_deploy_shadow": "forward_trigger_deploy",
    "verify_runtime_shadow": "forward_verify_runtime",
    "disconnect_repo_source_shadow": "rollback_disconnect_source",
    "revert_env_writes_shadow": "rollback_revert_env",
    "disable_deploys_shadow": "rollback_disable_deploys_simulated",
    "remove_created_service_shadow": "rollback_remove_service_simulated",
    "rollback_shadow_finalize": "rollback_finalize",
    "rollback_shadow": "rollback_orchestration",
}
