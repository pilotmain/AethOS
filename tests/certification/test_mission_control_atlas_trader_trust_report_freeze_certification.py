# SPDX-License-Identifier: Apache-2.0
"""FIX 194 — Atlas Trader trust report freeze certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_194_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_contract import (
    ATLAS_TRADER_TRUST_REPORT_FREEZE_FIX,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_INVARIANT,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_PRINCIPLES,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_ROUTE_ID,
    ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    CROSS_REPO_AUTHORITY_FIX_194,
    PILOT_EXECUTION_AUTHORITY_FIX_194,
    TRUST_GRANTING_AUTHORITY_FIX_194,
    TRUST_INHERITANCE_ENABLED_FIX_194,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
    build_atlas_trader_trust_report_freeze,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-attrf-cert-194"


class TestMissionControlAtlasTraderTrustReportFreezeCertification:
    def test_fix_194_contract(self) -> None:
        assert ATLAS_TRADER_TRUST_REPORT_FREEZE_FIX == "FIX 194"
        assert ATLAS_TRADER_TRUST_REPORT_FREEZE_SCHEMA_VERSION == (
            "mission_control_atlas_trader_trust_report_freeze_v1"
        )
        assert TRUST_GRANTING_AUTHORITY_FIX_194 is False
        assert TRUST_INHERITANCE_ENABLED_FIX_194 is False
        assert PILOT_EXECUTION_AUTHORITY_FIX_194 is False
        assert CROSS_REPO_AUTHORITY_FIX_194 is False
        assert TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_194 is True

    def test_fix_194_trust_freeze_not_trust_granting(self) -> None:
        result = build_atlas_trader_trust_report_freeze(session_id=SESSION)
        board = result.atlas_trader_trust_report_freeze
        assert set(board["fix_194_certification_requirements"]) == set(FIX_194_CERTIFICATION_REQUIREMENTS)
        assert board["trust_granting_authority"] is False
        assert "trust_granting" in ATLAS_TRADER_TRUST_REPORT_FREEZE_INVARIANT

    def test_fix_194_sections_present(self) -> None:
        result = build_atlas_trader_trust_report_freeze(session_id=SESSION)
        sections = result.atlas_trader_trust_report_freeze["sections"]
        assert sections["atlas_trust_report"]
        assert sections["atlas_evidence_timeline"]
        assert sections["trust_review_dashboard"]
        assert sections["trust_boundary_matrix"]
        assert sections["expansion_recommendation"]
        assert sections["evidence_index"]
        assert len(ATLAS_TRADER_TRUST_REPORT_FREEZE_PRINCIPLES) >= 8

    def test_fix_194_certification_requirement_count(self) -> None:
        assert len(FIX_194_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_194_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_194_route_id(self) -> None:
        assert ATLAS_TRADER_TRUST_REPORT_FREEZE_ROUTE_ID == (
            "mission_control_atlas_trader_trust_report_freeze"
        )

    def test_fix_194_compose_only(self) -> None:
        result = build_atlas_trader_trust_report_freeze(session_id=SESSION)
        sources = result.atlas_trader_trust_report_freeze["sources"]
        assert sources["pilot_reexecution_performed"] is False
