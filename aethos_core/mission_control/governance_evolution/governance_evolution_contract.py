# SPDX-License-Identifier: Apache-2.0
"""FIX 155 — governance evolution + institutional continuity contract."""

from __future__ import annotations

from typing import Final

GOVERNANCE_EVOLUTION_SCHEMA_VERSION: Final[str] = "mission_control_governance_evolution_v1"
GOVERNANCE_EVOLUTION_RECORD_SCHEMA_VERSION: Final[str] = "mission_control_governance_evolution_record_v1"
GOVERNANCE_EVOLUTION_FIX: Final[str] = "FIX 155"

MUTATION_PERFORMED_FIX_155: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_155: Final[bool] = False
AUTONOMOUS_GOVERNANCE_EVOLUTION_ENABLED_FIX_155: Final[bool] = False
SELF_DIRECTED_INSTITUTIONAL_TRANSFORMATION_ENABLED_FIX_155: Final[bool] = False
AUTOMATIC_DOCTRINE_MIGRATION_ENABLED_FIX_155: Final[bool] = False
POLICY_MUTATION_AUTHORITY_ENABLED_FIX_155: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_155: Final[bool] = False

GOVERNANCE_EVOLUTION_ROUTE_ID: Final[str] = "mission_control_governance_evolution"

GOVERNANCE_EVOLUTION_INVARIANT: Final[str] = (
    "governance_evolution_is_institutional_temporal_cognition_recommendation_only_no_autonomous_evolution_or_doctrine_migration"
)

EVOLUTION_RECORD_KINDS: Final[tuple[str, ...]] = (
    "doctrine_era",
    "generation_marker",
    "transition_note",
    "continuity_observation",
    "narrative_record",
)

TEMPORAL_COGNITION_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("evolution_not_mutation", "Governance evolution is tracked and reasoned about; it is never autonomously executed."),
    ("continuity_not_transformation", "Institutional continuity analysis does not self-direct institutional change."),
    ("era_visibility", "Doctrine eras are surfaced for human governance across long horizons."),
    ("freeze_respect", "Freeze-era continuity honors contract-frozen governance baselines."),
    ("drift_advisory", "Long-horizon drift is detected and surfaced, never auto-corrected."),
    ("epoch_comparison_advisory", "Constitutional epoch comparisons assist human transition planning."),
    ("migration_reasoning_only", "Governance migration reasoning does not migrate live policy."),
    ("human_sovereignty_over_time", "All temporal governance cognition requires human institutional sovereignty."),
)

CONSTITUTIONAL_EPOCHS: Final[tuple[tuple[str, str, str], ...]] = (
    ("epoch_operational", "FIX 128–140", "Operational memory and Mission Control observability era"),
    ("epoch_institutional_memory", "FIX 148–149", "Deliberation and collaboration memory era"),
    ("epoch_constitutional_topology", "FIX 150", "Governance role architecture and trust boundaries era"),
    ("epoch_constitutional_doctrine", "FIX 151", "Governance doctrine and policy charter era"),
    ("epoch_constitutional_reasoning", "FIX 152–153", "Interpretation and coherence cognition era"),
    ("epoch_constitutional_resilience", "FIX 154", "Institutional resilience cognition era"),
    ("epoch_temporal_continuity", "FIX 155", "Governance evolution and institutional continuity era"),
)

GOVERNANCE_GENERATIONS: Final[tuple[tuple[str, str], ...]] = (
    ("gen_1_operational", "Operational intelligence and Mission Control (FIX 128–147)"),
    ("gen_2_institutional_memory", "Governance deliberation and collaboration (FIX 148–149)"),
    ("gen_3_constitutional", "Constitutional governance stack (FIX 150–155)"),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 150", "Governance role architecture invariant"),
    ("FIX 151", "Governance doctrine invariant"),
    ("FIX 152", "Governance policy interpretation invariant"),
    ("FIX 153", "Governance coherence invariant"),
    ("FIX 154", "Governance resilience invariant"),
    ("FIX 155", "Governance evolution invariant"),
)

EVOLUTION_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_EVOLUTION_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_EVOLUTION_RECORDS: Final[int] = 500

MATURITY_STAGES: Final[tuple[str, ...]] = (
    "operational",
    "institutional_memory",
    "constitutional_topology",
    "constitutional_doctrine",
    "constitutional_reasoning",
    "constitutional_coherence",
    "constitutional_resilience",
    "temporal_continuity",
)
