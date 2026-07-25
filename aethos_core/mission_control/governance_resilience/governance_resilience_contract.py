# SPDX-License-Identifier: Apache-2.0
"""FIX 154 — governance resilience + stress simulation contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_RESILIENCE_SCHEMA_VERSION: Final[str] = "mission_control_governance_resilience_v1"
GOVERNANCE_RESILIENCE_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_resilience_record_v1"
GOVERNANCE_RESILIENCE_FIX: Final[str] = "FIX 154"

MUTATION_PERFORMED_FIX_154: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_154: Final[bool] = False
AUTOMATIC_GOVERNANCE_ADAPTATION_ENABLED_FIX_154: Final[bool] = False
AUTONOMOUS_RESILIENCE_CORRECTION_ENABLED_FIX_154: Final[bool] = False
SELF_HEALING_GOVERNANCE_ENABLED_FIX_154: Final[bool] = False
OVERRIDE_AUTHORITY_ENABLED_FIX_154: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_154: Final[bool] = False

GOVERNANCE_RESILIENCE_ROUTE_ID: Final[str] = "mission_control_governance_resilience"

GOVERNANCE_RESILIENCE_INVARIANT: Final[str] = (
    "governance_resilience_is_institutional_stress_simulation_only_no_autonomous_adaptation_correction_or_override"
)

RESILIENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "stress_scenario",
    "resilience_observation",
    "recovery_posture_note",
    "handoff_stress_note",
    "breach_simulation_note",
)

RESILIENCE_COGNITION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("simulation_not_adaptation", "Stress simulation evaluates resilience; it does not adapt live governance."),
    ("resilience_not_correction", "Resilience scoring is advisory; it does not autonomously correct governance."),
    ("stress_hypothetical_only", "All stress scenarios are hypothetical — never applied to live policy."),
    ("overload_visibility", "Approval-chain overload is modeled for institutional visibility only."),
    ("crisis_reasoning_advisory", "Crisis resilience analysis assists human governance under stress."),
    ("handoff_not_delegation", "Operator loss/handoff resilience does not grant delegated authority."),
    ("breach_simulation_only", "Trust-boundary breach scenarios are simulated, never executed."),
    ("human_sovereignty_under_stress", "Recovery posture recommendations require human governance sovereignty."),
)

STRESS_SCENARIO_CATALOG: Final[tuple[tuple[str, str, str], ...]] = (
    ("approval_chain_overload", "high", "Simulate concurrent approval gate saturation across lanes."),
    ("incident_surge", "critical", "Simulate elevated incident exposure with governance review backlog."),
    ("quorum_failure", "high", "Simulate insufficient reviewers for advisory quorum composition."),
    ("governance_fragmentation", "moderate", "Simulate policy fragmentation under multi-gate missions."),
    ("operator_loss_handoff", "high", "Simulate primary operator unavailability and handoff continuity."),
    ("doctrine_conflict_escalation", "critical", "Simulate unresolved doctrine conflicts under mission pressure."),
    ("trust_boundary_breach", "critical", "Simulate hypothetical trust-zone boundary violation."),
    ("recovery_posture", "moderate", "Simulate post-stress governance recovery readiness."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
    ("FIX 152", "Governance policy interpretation invariant"),
    ("FIX 153", "Governance coherence invariant"),
    ("FIX 154", "Governance resilience invariant"),
)

RESILIENCE_SIMULATION_EXECUTABLE: Final[bool] = False

MAX_RESILIENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_RESILIENCE_RECORDS: Final[int] = 500
