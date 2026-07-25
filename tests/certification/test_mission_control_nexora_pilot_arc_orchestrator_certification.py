# SPDX-License-Identifier: Apache-2.0
"""FIX 195 — Nexora pilot arc orchestrator certification."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_195_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    CROSS_REPO_AUTHORITY_FIX_195,
    NEXORA_PILOT_ARC_ORCHESTRATOR_FIX,
    NEXORA_PILOT_ARC_ORCHESTRATOR_INVARIANT,
    NEXORA_PILOT_ARC_ORCHESTRATOR_PRINCIPLES,
    NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    NEXORA_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
    PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195,
    TRUST_GRANTING_AUTHORITY_FIX_195,
    TRUST_INHERITANCE_ENABLED_FIX_195,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_service import (
    build_nexora_pilot_arc_orchestrator,
)
from aethos_core.mission_control.repo_pilot_readiness_dashboard.repo_pilot_readiness_dashboard_service import (
    RepoPilotReadinessDashboardResult,
)
from tests.test_mission_control_nexora_pilot_arc_orchestrator import _nexora_arc_stack

pytestmark = pytest.mark.certification

SESSION = "mc-npao-cert-195"


class TestMissionControlNexoraPilotArcOrchestratorCertification:
    def test_fix_195_contract(self) -> None:
        assert NEXORA_PILOT_ARC_ORCHESTRATOR_FIX == "FIX 195"
        assert NEXORA_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION == (
            "mission_control_nexora_pilot_arc_orchestrator_v1"
        )
        assert TRUST_GRANTING_AUTHORITY_FIX_195 is False
        assert TRUST_INHERITANCE_ENABLED_FIX_195 is False
        assert CROSS_REPO_AUTHORITY_FIX_195 is False
        assert PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_195 is True
        assert len(NEXORA_PILOT_ARC_ORCHESTRATOR_PRINCIPLES) >= 7

    @patch(
        "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
        "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
    )
    def test_fix_195_composes_without_auto_trust(self, mock_readiness) -> None:
        mock_readiness.return_value = RepoPilotReadinessDashboardResult(
            ok=True,
            session_id="default",
            blockers=[],
        )
        _nexora_arc_stack()
        result = build_nexora_pilot_arc_orchestrator(session_id=SESSION)
        assert result.ok is True
        report = result.nexora_pilot_arc_orchestrator
        assert set(report["fix_195_certification_requirements"]) == set(FIX_195_CERTIFICATION_REQUIREMENTS)
        assert report["trust_granting_authority"] is False
        assert "trust_granting" in NEXORA_PILOT_ARC_ORCHESTRATOR_INVARIANT

    @patch(
        "aethos_core.mission_control.nexora_pilot_arc_orchestrator."
        "nexora_pilot_arc_orchestrator_service.build_repo_pilot_readiness_dashboard"
    )
    def test_fix_195_outputs_present(self, mock_readiness) -> None:
        mock_readiness.return_value = RepoPilotReadinessDashboardResult(
            ok=True,
            session_id="default",
            blockers=[],
        )
        _nexora_arc_stack()
        result = build_nexora_pilot_arc_orchestrator(session_id=SESSION)
        sections = result.nexora_pilot_arc_orchestrator["sections"]
        assert sections["nexora_evidence_registry"]
        assert sections["nexora_pilot_dashboard"]
        assert sections["nexora_trust_recommendation"]
        assert sections["pilot_progress_timeline"]
        assert sections["trust_readiness_summary"]

    def test_fix_195_certification_requirement_count(self) -> None:
        assert len(FIX_195_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_195_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_195_route_id(self) -> None:
        assert NEXORA_PILOT_ARC_ORCHESTRATOR_ROUTE_ID == "mission_control_nexora_pilot_arc_orchestrator"
