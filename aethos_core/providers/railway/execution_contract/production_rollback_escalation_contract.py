# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation contract (manual only, no autonomous rollback)."""

from __future__ import annotations

from typing import Final, Literal

RollbackDecisionState = Literal[
    "recommendation_recorded",
    "pending_incident_commander_review",
    "incident_commander_acknowledged",
    "rollback_rehearsal_quorum_recorded",
    "shadow_rehearsal_authorized",
    "shadow_rehearsal_completed",
    "human_declined_rollback",
    "escalation_closed",
]

RollbackRecommendation = Literal[
    "none",
    "advise_manual_review",
    "advise_shadow_rollback_rehearsal",
    "advise_incident_escalation",
    "blocked_pending_evidence",
]

INCIDENT_COMMANDER_ACK_PHRASE: Final[str] = (
    "I acknowledge production rollback escalation as incident commander."
)
PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE: Final[str] = (
    "I confirm operator quorum for production Railway rollback rehearsal."
)

AUTONOMOUS_PRODUCTION_ROLLBACK_PERMITTED: Final[bool] = False

ESCALATION_SCHEMA_VERSION: Final[str] = "production_rollback_escalation_v1"
