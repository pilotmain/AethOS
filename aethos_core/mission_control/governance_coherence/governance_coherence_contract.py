# SPDX-License-Identifier: Apache-2.0
"""FIX 153 — governance coherence + constitutional integrity contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_COHERENCE_SCHEMA_VERSION: Final[str] = "mission_control_governance_coherence_v1"
GOVERNANCE_COHERENCE_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_coherence_record_v1"
GOVERNANCE_COHERENCE_FIX: Final[str] = "FIX 153"

MUTATION_PERFORMED_FIX_153: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_153: Final[bool] = False
AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_153: Final[bool] = False
AUTONOMOUS_GOVERNANCE_CORRECTION_ENABLED_FIX_153: Final[bool] = False
SELF_HEALING_GOVERNANCE_ENABLED_FIX_153: Final[bool] = False
CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_153: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_153: Final[bool] = False

GOVERNANCE_COHERENCE_ROUTE_ID: Final[str] = "mission_control_governance_coherence"

GOVERNANCE_COHERENCE_INVARIANT: Final[str] = (
    "governance_coherence_is_institutional_constitutional_integrity_intelligence_recommendation_only_no_autonomous_correction_or_override"
)

COHERENCE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "coherence_observation",
    "contradiction_report",
    "drift_signal",
    "integrity_note",
    "stability_note",
)

COHERENCE_INTELLIGENCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("coherence_not_enforcement", "Coherence analysis recommends; it does not enforce doctrine."),
    ("integrity_not_override", "Integrity scoring is advisory; it grants no constitutional override authority."),
    ("drift_surfaced_not_corrected", "Precedent drift is detected and surfaced, never auto-corrected."),
    ("contradiction_preserved", "Governance contradictions are surfaced for human reconciliation."),
    ("fragmentation_visibility", "Policy fragmentation is analyzed for institutional visibility only."),
    ("cross_session_advisory", "Cross-session coherence checks are advisory continuity signals."),
    ("stability_not_self_healing", "Stability indicators do not trigger self-healing governance."),
    ("human_sovereignty_primacy", "All coherence recommendations require human governance sovereignty."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
    ("FIX 152", "Governance policy interpretation invariant"),
    ("FIX 153", "Governance coherence invariant"),
)

COHERENCE_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_COHERENCE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_COHERENCE_RECORDS: Final[int] = 500
