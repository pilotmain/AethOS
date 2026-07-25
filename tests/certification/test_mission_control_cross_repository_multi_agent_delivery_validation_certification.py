# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — cross-repository multi-agent delivery validation certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_191_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_FIX,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_INVARIANT,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_PRINCIPLES,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_191,
    MERGE_AUTHORITY_FIX_191,
    TRUST_TRANSFER_ENABLED_FIX_191,
    VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191,
    VALIDATION_REPOSITORIES,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_dogfood_pilot_trust_report_freeze import _seed_dogfood_pilot_audits
from tests.test_mission_control_pilotos_ui_pilot_arc_orchestrator import (
    _seed_pilotos_expansion_approval,
    _seed_pilotos_pilot_audits,
)

pytestmark = pytest.mark.certification

SESSION = "mc-crmadv-cert-191"


class TestMissionControlCrossRepositoryMultiAgentDeliveryValidationCertification:
    def test_fix_191_contract(self) -> None:
        assert CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_FIX == "FIX 191"
        assert CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_SCHEMA_VERSION == (
            "mission_control_cross_repository_multi_agent_delivery_validation_v1"
        )
        assert CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191 is False
        assert EXECUTION_PERFORMED_FIX_191 is False
        assert VALIDATION_COMPOSES_ARTIFACTS_ONLY_FIX_191 is True
        assert MERGE_AUTHORITY_FIX_191 is False
        assert TRUST_TRANSFER_ENABLED_FIX_191 is False
        assert len(VALIDATION_REPOSITORIES) == 4
        assert len(CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_PRINCIPLES) >= 8

    def test_fix_191_validation_not_trust_granting(self) -> None:
        _seed_dogfood_pilot_audits()
        _seed_pilotos_expansion_approval()
        _seed_pilotos_pilot_audits()
        result = build_cross_repository_multi_agent_delivery_validation(session_id=SESSION)
        report = result.cross_repository_multi_agent_delivery_validation
        assert set(report["fix_191_certification_requirements"]) == set(FIX_191_CERTIFICATION_REQUIREMENTS)
        assert report["cross_repo_validation_grants_trust"] is False
        assert "trust" in CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_INVARIANT

    def test_fix_191_outputs_present(self) -> None:
        _seed_dogfood_pilot_audits()
        result = build_cross_repository_multi_agent_delivery_validation(session_id=SESSION)
        sections = result.cross_repository_multi_agent_delivery_validation["sections"]
        assert sections["cross_repository_validation_matrix"]
        assert sections["cross_repo_evidence_registry"] is not None
        assert sections["delivery_generalization_assessment"]
        assert sections["forbidden_validation_actions"]

        matrix = sections["cross_repository_validation_matrix"]
        for row in matrix:
            assert "pilot_progression" in row
            assert "trust_progression" in row
            assert row["trust_progression"]["trust_granted_by_validation"] is False

    def test_fix_191_certification_requirement_count(self) -> None:
        assert len(FIX_191_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_191_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_191_route_id(self) -> None:
        assert CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID == (
            "mission_control_cross_repository_multi_agent_delivery_validation"
        )
