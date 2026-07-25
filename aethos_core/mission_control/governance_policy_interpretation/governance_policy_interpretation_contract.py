# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — governance policy interpretation + precedent application contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_POLICY_INTERPRETATION_SCHEMA_VERSION: Final[str] = (
    "mission_control_governance_policy_interpretation_v1"
)
GOVERNANCE_POLICY_INTERPRETATION_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_governance_policy_interpretation_record_v1"
)
GOVERNANCE_POLICY_INTERPRETATION_FIX: Final[str] = "FIX 152"

MUTATION_PERFORMED_FIX_152: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_152: Final[bool] = False
AUTOMATIC_DOCTRINE_ENFORCEMENT_ENABLED_FIX_152: Final[bool] = False
AUTONOMOUS_GOVERNANCE_RULINGS_ENABLED_FIX_152: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_152: Final[bool] = False

GOVERNANCE_POLICY_INTERPRETATION_ROUTE_ID: Final[str] = "mission_control_governance_policy_interpretation"

GOVERNANCE_POLICY_INTERPRETATION_INVARIANT: Final[str] = (
    "governance_policy_interpretation_is_institutional_constitutional_reasoning_assistance_only_no_autonomous_enforcement_or_rulings"
)

INTERPRETATION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "doctrine_interpretation",
    "precedent_application",
    "interpretation_guidance",
    "rationale_mapping",
    "doctrine_review_linkage",
    "competing_interpretation",
    "ambiguity_surfacing",
    "historical_interpretation",
)

INTERPRETATION_ASSISTANCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("interpretation_not_enforcement", "Interpretation assists governance reasoning; it does not enforce doctrine."),
    ("precedent_not_ruling", "Precedent application is advisory; it does not constitute an automatic ruling."),
    ("human_ratification_required", "All constitutional interpretations require human governance ratification."),
    ("competing_views_preserved", "Competing interpretations are surfaced, not collapsed into a single ruling."),
    ("ambiguity_explicit", "Governance ambiguity is surfaced explicitly rather than resolved autonomously."),
    ("doctrine_linkage_advisory", "Doctrine-to-review linkages are advisory continuity, not execution gates."),
    ("constitutional_consistency_check_only", "Consistency checks flag issues; they do not mutate doctrine."),
    ("no_autonomous_policy_mutation", "Interpretation never mutates live policy or doctrine."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 148", "Governance deliberation invariant"),
    ("FIX 149", "Multi-operator collaboration invariant"),
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
    ("FIX 152", "Governance policy interpretation invariant"),
)

INTERPRETATION_EXECUTABLE: Final[bool] = False

MAX_INTERPRETATION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_INTERPRETATION_RECORDS: Final[int] = 500
