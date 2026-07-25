# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — institutional existential risk + continuity preservation contract."""

from __future__ import annotations

from typing import Final

INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION: Final[str] = (
    "mission_control_institutional_existential_risk_v1"
)
INSTITUTIONAL_EXISTENTIAL_RISK_RECORD_SCHEMA_VERSION: Final[str] = (
    "mission_control_institutional_existential_risk_record_v1"
)
INSTITUTIONAL_EXISTENTIAL_RISK_FIX: Final[str] = "FIX 158"

MUTATION_PERFORMED_FIX_158: Final[bool] = False
AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158: Final[bool] = False
AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158: Final[bool] = False
AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158: Final[bool] = False
CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158: Final[bool] = False
INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158: Final[bool] = False
GOVERNANCE_MUTATION_PERFORMED_FIX_158: Final[bool] = False

INSTITUTIONAL_EXISTENTIAL_RISK_ROUTE_ID: Final[str] = "mission_control_institutional_existential_risk"

INSTITUTIONAL_EXISTENTIAL_RISK_INVARIANT: Final[str] = (
    "institutional_existential_risk_is_continuity_cognition_recommendation_only_no_autonomous_self_preservation_or_constitutional_override"
)

EXISTENTIAL_RISK_RECORD_KINDS: Final[tuple[str, ...]] = (
    "continuity_risk_observation",
    "dependency_concentration_note",
    "collapse_scenario",
    "identity_erosion_signal",
    "sovereignty_degradation_note",
    "preservation_recommendation",
)

EXISTENTIAL_RISK_PRINCIPLES: Final[tuple[tuple[str, str], ...]] = (
    ("risk_surfaced_not_auto_mitigated", "Existential risks are analyzed and surfaced; they are never autonomously mitigated."),
    ("continuity_recommended_not_enforced", "Continuity preservation recommendations assist human stewardship; never auto-enforced."),
    ("sovereignty_preserved_not_overridden", "Constitutional sovereignty boundaries are preserved; existential cognition grants no override authority."),
    ("no_autonomous_self_preservation", "Institutional self-preservation is never autonomous — humans govern continuity decisions."),
    ("extinction_paths_modeled_not_executed", "Constitutional extinction paths are modeled for analysis; never executed autonomously."),
    ("dependency_concentration_advisory", "Dependency concentration is advisory — no autonomous rebalancing or provider realignment."),
    ("identity_erosion_detected_not_redirected", "Mission identity erosion is detected and surfaced; never auto-corrected or redirected."),
    ("civilization_dependencies_mapped_not_aligned", "Civilization-scale dependencies are mapped for reasoning; never autonomously aligned."),
)

GOVERNANCE_COLLAPSE_SCENARIOS: Final[tuple[tuple[str, str, str], ...]] = (
    ("doctrine_fragmentation", "moderate", "Governance doctrine fragments across lanes without constitutional coherence."),
    ("approval_bypass_drift", "elevated", "External provider mutation bypasses chat-governed approval boundaries."),
    ("identity_mission_drift", "moderate", "Institutional mission identity erodes relative to constitutional intent."),
    ("sovereignty_delegation_creep", "critical", "Institutional sovereignty gradually delegated to external providers."),
    ("operational_memory_loss", "moderate", "Cross-session operational memory discontinuity threatens institutional continuity."),
)

FRAGILITY_INDICATORS: Final[tuple[tuple[str, str], ...]] = (
    ("provider_concentration", "Elevated dependency on single external provider lanes."),
    ("governance_layer_gaps", "Missing or weak constitutional cognition layer coverage."),
    ("external_influence_drift", "External influence on institutional values detected."),
    ("identity_preservation_weak", "Institutional identity preservation signals below threshold."),
    ("continuity_record_sparse", "Sparse continuity preservation records for long-horizon analysis."),
)

EXTINCTION_PATH_CATALOG: Final[tuple[tuple[str, str], ...]] = (
    ("constitutional_override_creep", "Gradual autonomous override of constitutional boundaries."),
    ("sovereignty_extinction", "Complete delegation of institutional sovereignty to external ecosystems."),
    ("identity_dissolution", "Mission identity erosion beyond constitutional recognition."),
    ("governance_collapse", "Governance stack fragmentation without human institutional recovery."),
)

CONSTITUTIONAL_REFERENCES: Final[tuple[tuple[str, str], ...]] = (
    ("FIX 156", "Institutional identity invariant"),
    ("FIX 157", "Institutional external relations invariant"),
    ("FIX 158", "Institutional existential risk invariant"),
)

EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE: Final[bool] = False

MAX_EXISTENTIAL_RISK_CONTENT_LEN: Final[int] = 4000
MAX_PERSISTED_EXISTENTIAL_RISK_RECORDS: Final[int] = 500
