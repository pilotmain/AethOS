# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — multi-stage production rollout orchestration contract."""

from __future__ import annotations

from typing import Final, Literal

RolloutStage = Literal["shadow", "canary", "staged_rollout", "full_rollout"]
RolloutStageStatus = Literal["pending", "in_progress", "checkpoint_passed", "completed", "blocked"]
RolloutOrchestrationState = Literal["not_enrolled", "active", "paused", "completed", "blocked"]

ROLLOUT_STAGES: Final[tuple[RolloutStage, ...]] = (
    "shadow",
    "canary",
    "staged_rollout",
    "full_rollout",
)

BLAST_RADIUS_BY_STAGE: Final[dict[RolloutStage, str]] = {
    "shadow": "local",
    "canary": "service",
    "staged_rollout": "environment",
    "full_rollout": "platform",
}

ROLLOUT_SCHEMA_VERSION: Final[str] = "production_rollout_orchestration_v1"
ROLLOUT_RECEIPT_PHASE_PREFIX: Final[str] = "production_rollout_"

AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED: Final[bool] = False

ROLLOUT_ADVANCE_APPROVAL_PHRASE: Final[str] = (
    "I authorize advancing the governed production Railway rollout stage."
)
ROLLOUT_PAUSE_PHRASE: Final[str] = "I authorize pausing the governed production Railway rollout."
ROLLOUT_RESUME_PHRASE: Final[str] = "I authorize resuming the governed production Railway rollout."
