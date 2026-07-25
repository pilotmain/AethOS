# SPDX-License-Identifier: Apache-2.0
"""FIX 188 — PilotOS UI pilot arc orchestrator certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_188_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_FIX,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_PRINCIPLES,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID,
    PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION,
    PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188,
    TRUST_TRANSFER_ENABLED_FIX_188,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_service import (
    build_pilotos_ui_pilot_arc_orchestrator,
)
from tests.test_mission_control_pilotos_ui_pilot_arc_orchestrator import _pilotos_arc_stack

pytestmark = pytest.mark.certification

SESSION = "mc-puiao-cert-188"


class TestMissionControlPilotosUiPilotArcOrchestratorCertification:
    def test_fix_188_contract(self) -> None:
        assert PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_FIX == "FIX 188"
        assert PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_SCHEMA_VERSION == (
            "mission_control_pilotos_ui_pilot_arc_orchestrator_v1"
        )
        assert TRUST_TRANSFER_ENABLED_FIX_188 is False
        assert AUTOMATIC_TRUST_GRANTING_ENABLED_FIX_188 is False
        assert PILOT_ARC_ROUTES_THROUGH_FIX_181_FIX_188 is True
        assert len(PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_PRINCIPLES) >= 7

    def test_fix_188_composes_without_auto_trust(self) -> None:
        _pilotos_arc_stack()
        result = build_pilotos_ui_pilot_arc_orchestrator(session_id=SESSION)
        assert result.ok is True
        report = result.pilotos_ui_pilot_arc_orchestrator
        assert set(report["fix_188_certification_requirements"]) == set(FIX_188_CERTIFICATION_REQUIREMENTS)
        assert report["automatic_trust_granting_enabled"] is False
        assert "automatic_trust" in PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT or (
            "trust_granting" in PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_INVARIANT
        )

    def test_fix_188_outputs_present(self) -> None:
        _pilotos_arc_stack()
        result = build_pilotos_ui_pilot_arc_orchestrator(session_id=SESSION)
        sections = result.pilotos_ui_pilot_arc_orchestrator["sections"]
        assert sections["pilot_evidence_registry"]
        assert sections["pilotos_ui_trust_report"]
        assert sections["pilotos_ui_evidence_bundle"]
        assert sections["pilotos_ui_trust_recommendation"]
        assert sections["expansion_readiness_assessment"]

    def test_fix_188_certification_requirement_count(self) -> None:
        assert len(FIX_188_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_188_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_188_route_id(self) -> None:
        assert PILOTOS_UI_PILOT_ARC_ORCHESTRATOR_ROUTE_ID == (
            "mission_control_pilotos_ui_pilot_arc_orchestrator"
        )
