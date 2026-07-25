# SPDX-License-Identifier: Apache-2.0
"""FIX 156 — institutional identity + constitutional intent contract."""

from __future__ import annotations

from typing import Final

INSTITUTIONAL_IDENTITY_SCHEMA_VERSION: Final[str] = "mission_control_institutional_identity_v1"
INSTITUTIONAL_IDENTITY_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_institutional_identity_record_v1"
INSTITUTIONAL_IDENTITY_FIX: Final[str] = "FIX 156"

MUTATION_PERFORMED_FIX_156: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_156: Final[bool] = False
AUTONOMOUS_INSTITUTIONAL_REDIRECTION_ENABLED_FIX_156: Final[bool] = False
SELF_AUTHORED_MISSION_CHANGES_ENABLED_FIX_156: Final[bool] = False
AUTOMATIC_CONSTITUTIONAL_REWRITING_ENABLED_FIX_156: Final[bool] = False
GOVERNANCE_SOVEREIGNTY_DELEGATED_FIX_156: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_156: Final[bool] = False

INSTITUTIONAL_IDENTITY_ROUTE_ID: Final[str] = "mission_control_institutional_identity"

INSTITUTIONAL_IDENTITY_INVARIANT: Final[str] = (
    "institutional_identity_is_enduring_identity_cognition_recommendation_only_no_autonomous_redirection_or_constitutional_rewriting"
)

IDENTITY_RECORD_KINDS: Final[tuple[str, ...]] = (
    "mission_identity",
    "constitutional_intent",
    "philosophy_record",
    "purpose_preservation",
    "identity_continuity",
    "narrative_continuity",
)

IDENTITY_COGNITION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("identity_not_redirection", "Institutional identity is preserved and reasoned about; it is never autonomously redirected."),
    ("intent_not_rewrite", "Constitutional intent lineage is advisory; it does not rewrite live governance."),
    ("philosophy_continuity_advisory", "Operational philosophy continuity assists human institutional stewardship."),
    ("purpose_preserved_not_mutated", "Governance purpose preservation does not mutate mission authority."),
    ("value_drift_surfaced", "Institutional value drift is detected and surfaced, never auto-corrected."),
    ("alignment_advisory", "Constitutional mission alignment checks are advisory only."),
    ("identity_continuity_human", "Organizational identity continuity requires human governance sovereignty."),
    ("no_self_authored_mission", "Mission identity evolves only through human institutional authorship."),
)

INSTITUTIONAL_MISSION_IDENTITY: Final[tuple[tuple[str, str], ...]] = (
    ("human_governance_sovereignty", "All execution and constitutional authority remains with explicit human governance."),
    ("governed_operational_intelligence", "Operational intelligence assists without autonomous execution authority."),
    ("constitutional_cognition_without_authority", "The system reasons about governance without possessing governance sovereignty."),
    ("institutional_memory_persistence", "Deliberation, collaboration, and doctrine memory persist institutional continuity."),
    ("replay_safe_governance", "Evidence, replay, and audit preserve replay-safe governance boundaries."),
)

CONSTITUTIONAL_INTENT_LINEAGE: Final[tuple[tuple[str, str], ...]] = (
    ("intent_operational_governance", "Mission Control observability with governed approval only (FIX 128–135)"),
    ("intent_institutional_memory", "Governance deliberation and collaboration as institutional memory (FIX 148–149)"),
    ("intent_constitutional_stack", "Six-layer constitutional cognition without sovereign authority (FIX 150–156)"),
    ("intent_enduring_identity", "Institutional identity and constitutional intent persist across eras (FIX 156)"),
)

OPERATIONAL_PHILOSOPHY: Final[tuple[tuple[str, str], ...]] = (
    ("philosophy_governed_not_autonomous", "Governed orchestration — never autonomous mission execution."),
    ("philosophy_memory_not_mutation", "Memory layers record; they do not mutate live policy."),
    ("philosophy_simulation_not_enforcement", "Simulation and stress modeling inform; they do not enforce."),
    ("philosophy_recommendation_not_sovereignty", "All cognition recommends; human governance decides."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
    ("FIX 155", "Governance evolution invariant"),
    ("FIX 156", "Institutional identity invariant"),
)

IDENTITY_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_IDENTITY_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_IDENTITY_RECORDS: Final[int] = 500
