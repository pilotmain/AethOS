# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — pilot validation trust board certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_183_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_contract import (
    AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183,
    DIRECT_EXECUTION_PERFORMED_FIX_183,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183,
    EXECUTION_PERFORMED_FIX_183,
    FORBIDDEN_VALIDATION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_183,
    MUTATION_PERFORMED_FIX_183,
    PILOT_REEXECUTION_PERFORMED_FIX_183,
    PILOT_VALIDATION_TRUST_BOARD_FIX,
    PILOT_VALIDATION_TRUST_BOARD_INVARIANT,
    PILOT_VALIDATION_TRUST_BOARD_PRINCIPLES,
    PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID,
    PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
    VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183,
)
from aethos_core.mission_control.pilot_validation_trust_board.pilot_validation_trust_board_service import (
    build_pilot_validation_trust_board,
)
from tests.test_mission_control_pilot_validation_trust_board import _validation_stack

pytestmark = pytest.mark.certification

SESSION = "mc-pvtb-cert-183"


class TestMissionControlPilotValidationTrustBoardCertification:
    def test_fix_183_contract(self) -> None:
        assert PILOT_VALIDATION_TRUST_BOARD_FIX == "FIX 183"
        assert PILOT_VALIDATION_TRUST_BOARD_SCHEMA_VERSION == "mission_control_pilot_validation_trust_board_v1"
        assert MUTATION_PERFORMED_FIX_183 is False
        assert EXECUTION_PERFORMED_FIX_183 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_183 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_183 is False
        assert PILOT_REEXECUTION_PERFORMED_FIX_183 is False
        assert AUTONOMOUS_VALIDATION_EXECUTION_ENABLED_FIX_183 is False
        assert GATE_BYPASS_ENABLED_FIX_183 is False
        assert VALIDATION_COMPOSES_AUDITS_ONLY_FIX_183 is True
        assert len(PILOT_VALIDATION_TRUST_BOARD_PRINCIPLES) >= 10
        assert len(FORBIDDEN_VALIDATION_ACTIONS) >= 8
        assert "pilot_reexecution" in {a for a, _ in FORBIDDEN_VALIDATION_ACTIONS}

    def test_fix_183_composes_fix_181_audits_without_duplication(self) -> None:
        _validation_stack(SESSION)
        result = build_pilot_validation_trust_board(session_id=SESSION)
        assert result.ok is True
        board = result.pilot_validation_trust_board
        assert set(board["fix_183_certification_requirements"]) == set(FIX_183_CERTIFICATION_REQUIREMENTS)
        assert board["composes_upstream_layers_not_duplicates"] is True
        section_keys = set(board.get("sections") or {})
        assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
        assert board["pilot_reexecution_performed"] is False
        assert "validation" in PILOT_VALIDATION_TRUST_BOARD_INVARIANT.lower()

    def test_fix_183_trust_metrics_present(self) -> None:
        _validation_stack(SESSION)
        result = build_pilot_validation_trust_board(session_id=SESSION)
        sections = result.pilot_validation_trust_board["sections"]
        assert sections["stage_completion_summary"]
        assert sections["approval_friction_metrics"]
        assert sections["re_engagement_metrics"]
        assert sections["human_effort_scoring"]
        assert sections["trust_recommendation"]

    def test_fix_183_certification_requirement_count(self) -> None:
        assert len(FIX_183_CERTIFICATION_REQUIREMENTS) >= 8

    def test_fix_183_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_183_route_id(self) -> None:
        assert PILOT_VALIDATION_TRUST_BOARD_ROUTE_ID == "mission_control_pilot_validation_trust_board"
