# SPDX-License-Identifier: Apache-2.0
"""FIX 193 — Atlas Trader pilot arc orchestrator certification."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_193_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_FIX,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_INVARIANT,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_PRINCIPLES,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
    CROSS_REPO_AUTHORITY_FIX_193,
    PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193,
    TRUST_GRANTING_AUTHORITY_FIX_193,
    TRUST_INHERITANCE_ENABLED_FIX_193,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_service import (
    build_atlas_trader_pilot_arc_orchestrator,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    RepoPilotReadinessDashboardResult,
)
from tests.test_mission_control_atlas_trader_pilot_arc_orchestrator import _atlas_arc_stack

pytestmark = pytest.mark.certification

SESSION = "mc-atpao-cert-193"


class TestMissionControlAtlasTraderPilotArcOrchestratorCertification:
    def test_fix_193_contract(self) -> None:
        assert ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_FIX == "FIX 193"
        assert ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION == (
            "mission_control_atlas_trader_pilot_arc_orchestrator_v1"
        )
        assert TRUST_GRANTING_AUTHORITY_FIX_193 is False
        assert TRUST_INHERITANCE_ENABLED_FIX_193 is False
        assert CROSS_REPO_AUTHORITY_FIX_193 is False
        assert PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_193 is True
        assert len(ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_PRINCIPLES) >= 7

    @patch(
        "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
        "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
    )
    def test_fix_193_composes_without_auto_trust(self, mock_readiness) -> None:
        mock_readiness.return_value = RepoPilotReadinessDashboardResult(
            ok=True,
            session_id="default",
            blockers=[],
        )
        _atlas_arc_stack()
        result = build_atlas_trader_pilot_arc_orchestrator(session_id=SESSION)
        assert result.ok is True
        report = result.atlas_trader_pilot_arc_orchestrator
        assert set(report["fix_193_certification_requirements"]) == set(FIX_193_CERTIFICATION_REQUIREMENTS)
        assert report["trust_granting_authority"] is False
        assert "trust_granting" in ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_INVARIANT

    @patch(
        "aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator."
        "atlas_trader_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
    )
    def test_fix_193_outputs_present(self, mock_readiness) -> None:
        mock_readiness.return_value = RepoPilotReadinessDashboardResult(
            ok=True,
            session_id="default",
            blockers=[],
        )
        _atlas_arc_stack()
        result = build_atlas_trader_pilot_arc_orchestrator(session_id=SESSION)
        sections = result.atlas_trader_pilot_arc_orchestrator["sections"]
        assert sections["atlas_evidence_registry"]
        assert sections["atlas_pilot_dashboard"]
        assert sections["atlas_trust_recommendation"]
        assert sections["pilot_progress_timeline"]
        assert sections["pilot_readiness_summary"]

    def test_fix_193_certification_requirement_count(self) -> None:
        assert len(FIX_193_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_193_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_193_route_id(self) -> None:
        assert ATLAS_TRADER_PILOT_ARC_ORCHESTRATOR_ROUTE_ID == (
            "mission_control_atlas_trader_pilot_arc_orchestrator"
        )
