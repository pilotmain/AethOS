# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A1 — PilotOS UI operational proof program contract."""

from __future__ import annotations

from typing import Final

PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID: Final[str] = "WORKSTREAM_A1"
PILOTOS_OPERATIONAL_PROOF_PROGRAM_SCHEMA_VERSION: Final[str] = (
    "workstream_pilotos_operational_proof_program_v1"
)

PILOTOS_UI_REPOSITORY: Final[str] = "pilotmain/pilot-os-ui"
PILOTOS_PILOT_SESSIONS: Final[tuple[str, ...]] = (
    "pilotos-pilot-1",
    "pilotos-pilot-2",
    "pilotos-pilot-3",
)

PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES: Final[tuple[str, ...]] = (
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
    "pilotos_readiness_report",
    "pilotos_prerequisite_validation",
    "pilotos_pilot1_evidence_bundle",
    "pilotos_pilot2_evidence_bundle",
    "pilotos_pilot3_evidence_bundle",
    "pilotos_trust_freeze_artifact",
    "trust_boundary_snapshot",
    "trust_recommendation_snapshot",
    "pilotos_trust_decision_record",
    "pilotos_evidence_density_report",
    "pilotos_executive_visibility_report",
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
    "FIX 324",
    "FIX 325",
    "FIX 326",
    "FIX 327",
    "FIX 328",
    "FIX 329",
    "FIX 330",
)
