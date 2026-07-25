# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A2 — Atlas Trader operational proof program contract."""

from __future__ import annotations

from typing import Final

ATLAS_OPERATIONAL_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_A2"
ATLAS_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_atlas_operational_proof_program_v1"
)

ATLAS_TRADER_REPOSITORY: Final[str] = "pilotmain/atlas-trader"
ATLAS_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "atlas-pilot-1",
    "atlas-pilot-2",
    "atlas-pilot-3",
)

ATLAS_OPERATIONAL_PROOF_PROGRAM_PHASES: Final[tuple[str, ...]] = (
    "phase_1_repository_readiness",
    "phase_2_pilot_1_execution",
    "phase_3_pilot_2_execution",
    "phase_4_pilot_3_execution",
    "phase_5_trust_freeze",
    "phase_6_trust_review",
    "phase_7_evidence_density_review",
    "phase_8_executive_dashboard_validation",
)

PHASE_OUTPUTS: Final[tuple[str, ...]] = (
    "atlas_readiness_report",
    "atlas_prerequisite_validation",
    "atlas_pilot1_evidence_bundle",
    "atlas_pilot2_evidence_bundle",
    "atlas_pilot3_evidence_bundle",
    "atlas_trust_freeze_artifact",
    "atlas_boundary_snapshot",
    "atlas_trust_recommendation_snapshot",
    "atlas_trust_decision_record",
    "atlas_evidence_density_report",
    "atlas_executive_visibility_report",
)

PROGRAM_NON_GOALS: Final[tuple[str, ...]] = (
    "no_new_intelligence_modules",
    "no_new_governance_modules",
    "no_new_executive_modules",
    "no_provider_expansion",
    "no_architecture_redesign",
)

EVIDENCE_DENSITY_LEVELS: Final[tuple[str, ...]] = (
    "INSUFFICIENT",
    "PARTIAL",
    "ADEQUATE",
    "STRONG",
)

EXECUTIVE_FIX_MODULES: Final[tuple[str, ...]] = (
    "FIX 191",
    "FIX 260",
    "FIX 324",
    "FIX 325",
    "FIX 326",
    "FIX 327",
    "FIX 328",
    "FIX 329",
    "FIX 330",
)
