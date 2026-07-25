# SPDX-License-Identifier: Apache-2.0
"""Certification — governance friction & human approval architectural principle."""

from __future__ import annotations

from pathlib import Path

import pytest

from aethos_core.governance.governance_friction_approval_contract import (
    APPROVAL_TIER_IDS,
    AUTHORITY_EXPANSION_FORBIDDEN_EXAMPLES,
    COGNITION_NOT_AUTHORITY_INVARIANT,
    DESIRED_OPERATOR_EXPERIENCE,
    FIX_170_CERTIFICATION_REQUIREMENTS,
    FIX_170_MISSION_AUTHORIZATION_FIX,
    FIX_170_PLUS_TARGET_PIPELINE,
    GOVERNANCE_FRICTION_APPROVAL_ADDITIVE_ONLY,
    GOVERNANCE_FRICTION_APPROVAL_PRINCIPLE_FIX,
    GOVERNANCE_FRICTION_APPROVAL_SCHEMA_VERSION,
    GOVERNANCE_SCALES_WITH_RISK_INVARIANT,
    HUMAN_REENGAGEMENT_NOT_REQUIRED,
    HUMAN_REENGAGEMENT_REQUIRED_TRIGGERS,
    HUMAN_SOVEREIGNTY_INVARIANT,
    MISSION_AUTHORIZATION_CANNOT_EXPAND_AUTHORITY_INVARIANT,
    MISSION_AUTHORIZATION_DIMENSIONS,
    MISSION_AUTHORIZATION_MUST_NOT_BYPASS_GATES_INVARIANT,
    MISSION_AUTHORIZATION_PREFERRED_INVARIANT,
    NON_BREAKING_PROTECTED_GUARANTEES,
    TIER_0_COGNITION_EXAMPLES,
    TIER_ESCALATION_FORBIDDEN_INVARIANT,
)

pytestmark = pytest.mark.certification

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestGovernanceFrictionApprovalPrincipleCertification:
    def test_principle_contract_identity(self) -> None:
        assert GOVERNANCE_FRICTION_APPROVAL_PRINCIPLE_FIX == "ARCH-PRINCIPLE-GOV-FRICTION"
        assert GOVERNANCE_FRICTION_APPROVAL_SCHEMA_VERSION == "aethos_governance_friction_approval_v2"
        assert GOVERNANCE_FRICTION_APPROVAL_ADDITIVE_ONLY is True

    def test_core_invariants(self) -> None:
        assert "risk" in GOVERNANCE_SCALES_WITH_RISK_INVARIANT.lower()
        assert "workflow" in GOVERNANCE_SCALES_WITH_RISK_INVARIANT.lower()
        assert "cognition" in COGNITION_NOT_AUTHORITY_INVARIANT.lower()
        assert "mission" in MISSION_AUTHORIZATION_PREFERRED_INVARIANT.lower()
        assert "sovereignty" in HUMAN_SOVEREIGNTY_INVARIANT.lower()

    def test_approval_tier_model(self) -> None:
        assert len(APPROVAL_TIER_IDS) == 5
        assert APPROVAL_TIER_IDS[0] == "tier_0_read_only_cognition"
        assert APPROVAL_TIER_IDS[4] == "tier_4_critical_authority_events"
        assert "readiness_lane_admission_fix_169" in TIER_0_COGNITION_EXAMPLES

    def test_reengagement_triggers_disjoint_from_non_triggers(self) -> None:
        required = set(HUMAN_REENGAGEMENT_REQUIRED_TRIGGERS)
        not_required = set(HUMAN_REENGAGEMENT_NOT_REQUIRED)
        assert not required.intersection(not_required)

    def test_non_breaking_guarantees_preserve_frozen_stacks(self) -> None:
        protected = set(NON_BREAKING_PROTECTED_GUARANTEES)
        assert "software_delivery_gates" in protected
        assert "railway_governance_protections" in protected
        assert "certification_guarantees" in protected
        assert "constitutional_governance_layers" in protected

    def test_fix_170_plus_pipeline_includes_mission_authorization(self) -> None:
        assert FIX_170_PLUS_TARGET_PIPELINE[0] == "human_decision"
        assert "mission_authorization" in FIX_170_PLUS_TARGET_PIPELINE
        assert "bounded_execution" in FIX_170_PLUS_TARGET_PIPELINE
        assert len(MISSION_AUTHORIZATION_DIMENSIONS) >= 6

    def test_principle_document_exists(self) -> None:
        doc = REPO_ROOT / "docs" / "AETHOS_GOVERNANCE_FRICTION_AND_APPROVAL_PRINCIPLE.md"
        assert doc.is_file()
        text = doc.read_text(encoding="utf-8")
        assert "cognition ≠ authority" in text or "cognition" in text.lower()
        assert "humans decide what matters" in text.lower()

    def test_fix_170_mission_authorization_certification_requirements(self) -> None:
        assert FIX_170_MISSION_AUTHORIZATION_FIX == "FIX 170"
        assert len(FIX_170_CERTIFICATION_REQUIREMENTS) >= 7
        assert "mission_authorization_cannot_expand_authority_beyond_granted_envelope" in FIX_170_CERTIFICATION_REQUIREMENTS
        assert "tier_1_2_authorization_cannot_satisfy_tier_3_4_approval_requirements" in FIX_170_CERTIFICATION_REQUIREMENTS
        assert "bounded_work_envelope_routes_through_existing_gates_not_around_them" in FIX_170_CERTIFICATION_REQUIREMENTS
        assert "expand" in MISSION_AUTHORIZATION_CANNOT_EXPAND_AUTHORITY_INVARIANT.lower()
        assert "bypass" in MISSION_AUTHORIZATION_MUST_NOT_BYPASS_GATES_INVARIANT.lower()
        assert "tier_3" in TIER_ESCALATION_FORBIDDEN_INVARIANT.lower()
        assert len(AUTHORITY_EXPANSION_FORBIDDEN_EXAMPLES) >= 3
