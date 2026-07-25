# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A3 — Nexora operational proof program contract."""

from __future__ import annotations

from typing import Final

NEXORA_OPERATIONAL_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_A3"
NEXORA_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_nexora_operational_proof_program_v1"
)

NEXORA_REPOSITORY: Final[str] = "pilotmain/nexora-monorepo-starter"
NEXORA_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "nexora-pilot-1",
    "nexora-pilot-2",
    "nexora-pilot-3",
)

NEXORA_OPERATIONAL_PROOF_PROGRAM_PHASES: Final[tuple[str, ...]] = (
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
    "nexora_readiness_report",
    "nexora_prerequisite_validation",
    "nexora_pilot1_evidence_bundle",
    "nexora_pilot2_evidence_bundle",
    "nexora_pilot3_evidence_bundle",
    "nexora_trust_freeze_artifact",
    "nexora_boundary_snapshot",
    "nexora_trust_recommendation_snapshot",
    "nexora_trust_decision_record",
    "nexora_evidence_density_report",
    "nexora_executive_visibility_report",
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
