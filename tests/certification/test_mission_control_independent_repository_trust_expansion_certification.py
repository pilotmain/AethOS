# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — independent repository trust expansion certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_187_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187,
    CROSS_REPO_AUTHORITY_ENABLED_FIX_187,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_FIX,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_INVARIANT,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_PRINCIPLES,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID,
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION,
    PILOT_EXECUTION_PERFORMED_FIX_187,
    TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187,
    TRUST_TRANSFER_ENABLED_FIX_187,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_service import (
    build_independent_repository_trust_expansion,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_independent_repository_trust_expansion import _trust_expansion_stack

pytestmark = pytest.mark.certification

SESSION = "mc-irte-cert-187"


class TestMissionControlIndependentRepositoryTrustExpansionCertification:
    def test_fix_187_contract(self) -> None:
        assert INDEPENDENT_REPOSITORY_TRUST_EXPANSION_FIX == "FIX 187"
        assert INDEPENDENT_REPOSITORY_TRUST_EXPANSION_SCHEMA_VERSION == (
            "mission_control_independent_repository_trust_expansion_v1"
        )
        assert TRUST_TRANSFER_ENABLED_FIX_187 is False
        assert AUTOMATIC_REPO_TRUST_INHERITANCE_ENABLED_FIX_187 is False
        assert CROSS_REPO_AUTHORITY_ENABLED_FIX_187 is False
        assert PILOT_EXECUTION_PERFORMED_FIX_187 is False
        assert TRUST_EXPANSION_COMPOSES_ARTIFACTS_ONLY_FIX_187 is True
        assert len(INDEPENDENT_REPOSITORY_TRUST_EXPANSION_PRINCIPLES) >= 8

    def test_fix_187_composes_without_trust_transfer(self) -> None:
        _trust_expansion_stack()
        result = build_independent_repository_trust_expansion(session_id=SESSION)
        assert result.ok is True
        report = result.independent_repository_trust_expansion
        assert set(report["fix_187_certification_requirements"]) == set(FIX_187_CERTIFICATION_REQUIREMENTS)
        assert report["trust_transfer_enabled"] is False
        assert "trust_transfer" in INDEPENDENT_REPOSITORY_TRUST_EXPANSION_INVARIANT

    def test_fix_187_outputs_present(self) -> None:
        _trust_expansion_stack()
        result = build_independent_repository_trust_expansion(session_id=SESSION)
        sections = result.independent_repository_trust_expansion["sections"]
        assert sections["repository_trust_registry"]
        assert sections["pilot_evidence_registry"]
        assert sections["expansion_approval_records"]
        assert sections["repository_trust_matrix"]

    def test_fix_187_certification_requirement_count(self) -> None:
        assert len(FIX_187_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_187_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_187_route_id(self) -> None:
        assert INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID == (
            "mission_control_independent_repository_trust_expansion"
        )
