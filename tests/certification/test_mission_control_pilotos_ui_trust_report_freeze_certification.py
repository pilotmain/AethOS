# SPDX-License-Identifier: Apache-2.0
"""FIX 192 — PilotOS UI trust report freeze certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_192_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_contract import (
    CROSS_REPO_AUTHORITY_FIX_192,
    PILOTOS_UI_TRUST_REPORT_FREEZE_FIX,
    PILOTOS_UI_TRUST_REPORT_FREEZE_INVARIANT,
    PILOTOS_UI_TRUST_REPORT_FREEZE_PRINCIPLES,
    PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID,
    PILOTOS_UI_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    PILOT_EXECUTION_AUTHORITY_FIX_192,
    TRUST_GRANTING_AUTHORITY_FIX_192,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_192,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface

pytestmark = pytest.mark.certification

SESSION = "mc-putrf-cert-192"


class TestMissionControlPilotosUiTrustReportFreezeCertification:
    def test_fix_192_contract(self) -> None:
        assert PILOTOS_UI_TRUST_REPORT_FREEZE_FIX == "FIX 192"
        assert PILOTOS_UI_TRUST_REPORT_FREEZE_SCHEMA_VERSION == (
            "mission_control_pilotos_ui_trust_report_freeze_v1"
        )
        assert TRUST_GRANTING_AUTHORITY_FIX_192 is False
        assert PILOT_EXECUTION_AUTHORITY_FIX_192 is False
        assert CROSS_REPO_AUTHORITY_FIX_192 is False
        assert TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_192 is True

    def test_fix_192_trust_freeze_not_trust_granting(self) -> None:
        result = build_pilotos_ui_trust_report_freeze(session_id=SESSION)
        board = result.pilotos_ui_trust_report_freeze
        assert set(board["fix_192_certification_requirements"]) == set(FIX_192_CERTIFICATION_REQUIREMENTS)
        assert board["trust_granting_authority"] is False
        assert "trust_granting" in PILOTOS_UI_TRUST_REPORT_FREEZE_INVARIANT

    def test_fix_192_sections_present(self) -> None:
        result = build_pilotos_ui_trust_report_freeze(session_id=SESSION)
        sections = result.pilotos_ui_trust_report_freeze["sections"]
        assert sections["pilotos_ui_trust_report"]
        assert sections["pilotos_ui_evidence_timeline"]
        assert sections["trust_review_dashboard"]
        assert sections["trust_boundary_matrix"]
        assert sections["expansion_recommendation"]
        assert sections["evidence_index"]
        assert len(PILOTOS_UI_TRUST_REPORT_FREEZE_PRINCIPLES) >= 8

    def test_fix_192_certification_requirement_count(self) -> None:
        assert len(FIX_192_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_192_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_192_route_id(self) -> None:
        assert PILOTOS_UI_TRUST_REPORT_FREEZE_ROUTE_ID == (
            "mission_control_pilotos_ui_trust_report_freeze"
        )

    def test_fix_192_compose_only(self) -> None:
        result = build_pilotos_ui_trust_report_freeze(session_id=SESSION)
        sources = result.pilotos_ui_trust_report_freeze["sources"]
        assert sources["pilot_reexecution_performed"] is False
