# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — dogfood pilot trust report freeze certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_186_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186,
    DIRECT_EXECUTION_PERFORMED_FIX_186,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_FIX,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_INVARIANT,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_PRINCIPLES,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID,
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_186,
    FORBIDDEN_TRUST_REPORT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_186,
    MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186,
    MUTATION_PERFORMED_FIX_186,
    PILOT_REEXECUTION_PERFORMED_FIX_186,
    TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_dogfood_pilot_trust_report_freeze import _dogfood_trust_stack

pytestmark = pytest.mark.certification

SESSION = "mc-dptrf-cert-186"


class TestMissionControlDogfoodPilotTrustReportFreezeCertification:
    def test_fix_186_contract(self) -> None:
        assert DOGFOOD_PILOT_TRUST_REPORT_FREEZE_FIX == "FIX 186"
        assert DOGFOOD_PILOT_TRUST_REPORT_FREEZE_SCHEMA_VERSION == (
            "mission_control_dogfood_pilot_trust_report_freeze_v1"
        )
        assert MUTATION_PERFORMED_FIX_186 is False
        assert EXECUTION_PERFORMED_FIX_186 is False
        assert DIRECT_EXECUTION_PERFORMED_FIX_186 is False
        assert DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_186 is False
        assert PILOT_REEXECUTION_PERFORMED_FIX_186 is False
        assert AUTONOMOUS_TRUST_REPORT_EXECUTION_ENABLED_FIX_186 is False
        assert GATE_BYPASS_ENABLED_FIX_186 is False
        assert TRUST_REPORT_COMPOSES_ARTIFACTS_ONLY_FIX_186 is True
        assert MULTI_REPO_EXPANSION_BLOCKED_BY_DEFAULT_FIX_186 is True
        assert len(DOGFOOD_PILOT_TRUST_REPORT_FREEZE_PRINCIPLES) >= 8
        assert len(FORBIDDEN_TRUST_REPORT_ACTIONS) >= 10
        assert "pilot_reexecution" in {a for a, _ in FORBIDDEN_TRUST_REPORT_ACTIONS}

    def test_fix_186_composes_artifacts_without_reexecution(self) -> None:
        _dogfood_trust_stack()
        result = build_dogfood_pilot_trust_report_freeze(session_id=SESSION)
        assert result.ok is True
        report = result.dogfood_pilot_trust_report_freeze
        assert set(report["fix_186_certification_requirements"]) == set(FIX_186_CERTIFICATION_REQUIREMENTS)
        assert report["pilot_reexecution_performed"] is False
        assert report["trust_report_composes_artifacts_only"] is True
        assert "trust_report_freeze" in DOGFOOD_PILOT_TRUST_REPORT_FREEZE_INVARIANT

    def test_fix_186_trust_boundary_and_expansion_gate(self) -> None:
        _dogfood_trust_stack()
        result = build_dogfood_pilot_trust_report_freeze(session_id=SESSION)
        sections = result.dogfood_pilot_trust_report_freeze["sections"]
        assert len(sections["frozen_evidence_timeline"]) == 3
        assert sections["trust_boundary_matrix"]
        expansion = sections["expansion_recommendation"][0]
        assert expansion["proceed"] is False
        assert expansion["multi_repo_expansion_blocked"] is True
        assert sections["scaling_gate"][0]["no_inherited_trust"] is True

    def test_fix_186_certification_requirement_count(self) -> None:
        assert len(FIX_186_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_186_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_186_route_id(self) -> None:
        assert DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID == (
            "mission_control_dogfood_pilot_trust_report_freeze"
        )
