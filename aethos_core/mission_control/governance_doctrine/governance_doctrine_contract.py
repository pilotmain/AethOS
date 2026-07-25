# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — governance doctrine + policy charter contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_DOCTRINE_SCHEMA_VERSION: Final[str] = "mission_control_governance_doctrine_v1"
GOVERNANCE_DOCTRINE_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_doctrine_record_v1"
GOVERNANCE_DOCTRINE_FIX: Final[str] = "FIX 151"

MUTATION_PERFORMED_FIX_151: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151: Final[bool] = False
AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151: Final[bool] = False
SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_151: Final[bool] = False

GOVERNANCE_DOCTRINE_ROUTE_ID: Final[str] = "mission_control_governance_doctrine"

GOVERNANCE_DOCTRINE_INVARIANT: Final[str] = (
    "governance_doctrine_is_institutional_constitutionality_amendment_proposals_only_no_autonomous_policy_mutation"
)

DOCTRINE_RECORD_KINDS: Final[tuple[str, ...]] = (
    "governance_charter",
    "doctrine_version",
    "policy_rationale",
    "policy_amendment_proposal",
    "governance_precedent",
    "constitutional_reference",
    "policy_freeze_snapshot",
)

GOVERNANCE_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("human_authority_primacy", "All execution authority remains with explicit human governance."),
    ("deliberation_not_execution", "Deliberation and collaboration memory do not grant execution rights."),
    ("review_delegation_not_authority", "Review handoff is allowed; execution authority delegation is forbidden."),
    ("explicit_approval_phrases", "Gates advance only through chat-governed approval phrases."),
    ("replay_safe_boundaries", "Mutation boundaries remain replay-safe and contract-frozen."),
    ("frozen_contract_respect", "Phase 2 and Mission Control freeze contracts are constitutional baselines."),
    ("no_autonomous_doctrine_evolution", "Doctrine evolves only through human-reviewed amendment proposals."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 135", "Mission Control operator console freeze"),
    ("FIX 126", "Software delivery phase 2 freeze"),
    ("FIX 124", "Phase 2 readiness contract"),
    ("FIX 148", "Governance deliberation invariant"),
    ("FIX 149", "Multi-operator collaboration invariant"),
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
)

AMENDMENT_PROPOSAL_EXECUTABLE: Final[bool] = False

MAX_DOCTRINE_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_DOCTRINE_RECORDS: Final[int] = 500

DOCTRINE_VERSION_BASE: Final[str] = "aethos_governance_doctrine_v1"
