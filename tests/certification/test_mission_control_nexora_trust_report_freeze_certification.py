# SPDX-License-Identifier: Apache-2.0
"""FIX 196 — Nexora trust report freeze certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_196_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_contract import (
    CROSS_REPO_AUTHORITY_FIX_196,
    NEXORA_TRUST_REPORT_FREEZE_FIX,
    NEXORA_TRUST_REPORT_FREEZE_INVARIANT,
    NEXORA_TRUST_REPORT_FREEZE_PRINCIPLES,
    NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID,
    NEXORA_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    PILOT_EXECUTION_AUTHORITY_FIX_196,
    TRUST_GRANTING_AUTHORITY_FIX_196,
    TRUST_INHERITANCE_ENABLED_FIX_196,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_196,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)

pytestmark = pytest.mark.certification

SESSION = "mc-ntrf-cert-196"


class TestMissionControlNexoraTrustReportFreezeCertification:
    def test_fix_196_contract(self) -> None:
        assert NEXORA_TRUST_REPORT_FREEZE_FIX == "FIX 196"
        assert NEXORA_TRUST_REPORT_FREEZE_SCHEMA_VERSION == (
            "mission_control_nexora_trust_report_freeze_v1"
        )
        assert TRUST_GRANTING_AUTHORITY_FIX_196 is False
        assert TRUST_INHERITANCE_ENABLED_FIX_196 is False
        assert PILOT_EXECUTION_AUTHORITY_FIX_196 is False
        assert CROSS_REPO_AUTHORITY_FIX_196 is False
        assert TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_196 is True

    def test_fix_196_trust_freeze_not_trust_granting(self) -> None:
        result = build_nexora_trust_report_freeze(session_id=SESSION)
        board = result.nexora_trust_report_freeze
        assert set(board["fix_196_certification_requirements"]) == set(FIX_196_CERTIFICATION_REQUIREMENTS)
        assert board["trust_granting_authority"] is False
        assert "trust_granting" in NEXORA_TRUST_REPORT_FREEZE_INVARIANT

    def test_fix_196_sections_present(self) -> None:
        result = build_nexora_trust_report_freeze(session_id=SESSION)
        sections = result.nexora_trust_report_freeze["sections"]
        assert sections["nexora_trust_report"]
        assert sections["nexora_evidence_timeline"]
        assert sections["trust_review_dashboard"]
        assert sections["trust_boundary_matrix"]
        assert sections["expansion_recommendation"]
        assert sections["evidence_index"]
        assert len(NEXORA_TRUST_REPORT_FREEZE_PRINCIPLES) >= 8

    def test_fix_196_certification_requirement_count(self) -> None:
        assert len(FIX_196_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_196_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_196_route_id(self) -> None:
        assert NEXORA_TRUST_REPORT_FREEZE_ROUTE_ID == "mission_control_nexora_trust_report_freeze"

    def test_fix_196_compose_only(self) -> None:
        result = build_nexora_trust_report_freeze(session_id=SESSION)
        sources = result.nexora_trust_report_freeze["sources"]
        assert sources["pilot_reexecution_performed"] is False
