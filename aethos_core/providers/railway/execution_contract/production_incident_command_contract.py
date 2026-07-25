# SPDX-License-Identifier: Apache-2.0
"""FIX 123 — production incident command contract."""

from __future__ import annotations

from typing import Final, Literal

IncidentStatus = Literal[
    "open",
    "triage",
    "incident_commander_assigned",
    "mitigation_planning",
    "rollback_recommended",
    "rollback_rehearsal_authorized",
    "manual_action_required",
    "resolved",
    "closed",
]

IncidentSeverity = Literal["sev1", "sev2", "sev3", "sev4"]

INCIDENT_COMMAND_SCHEMA_VERSION: Final[str] = "production_incident_command_v1"

INCIDENT_COMMANDER_ACCEPTANCE_PHRASE: Final[str] = (
    "I accept incident commander responsibility for this Railway production incident."
)

AUTONOMOUS_INCIDENT_MUTATION_PERMITTED: Final[bool] = False
AUTONOMOUS_INCIDENT_ROLLBACK_PERMITTED: Final[bool] = False
AUTOMATIC_INCIDENT_CLOSURE_PERMITTED: Final[bool] = False

ALLOWED_INCIDENT_DECISIONS: Final[frozenset[str]] = frozenset(
    {
        "begin_triage",
        "mitigation_plan_recorded",
        "authorize_rollback_rehearsal",
        "manual_action_required",
        "mark_resolved",
        "escalate_to_manual_review",
    }
)
