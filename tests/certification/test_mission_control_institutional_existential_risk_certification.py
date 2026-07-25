# SPDX-License-Identifier: Apache-2.0
"""FIX 158 — institutional existential risk certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158,
    AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158,
    AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158,
    CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158,
    EXISTENTIAL_RISK_PRINCIPLES,
    EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE,
    EXISTENTIAL_RISK_RECORD_KINDS,
    EXTINCTION_PATH_CATALOG,
    FRAGILITY_INDICATORS,
    GOVERNANCE_COLLAPSE_SCENARIOS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_158,
    INSTITUTIONAL_EXISTENTIAL_RISK_FIX,
    INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION,
    INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158,
    MUTATION_PERFORMED_FIX_158,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_service import (
    build_institutional_existential_risk,
)
from aethos_core.mission_control.institutional_existential_risk.institutional_existential_risk_store import (
    append_institutional_existential_risk_record,
    clear_institutional_existential_risk_records_for_tests,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-existential-cert-158"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_existential_risk_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()
    clear_institutional_existential_risk_records_for_tests()


class TestMissionControlInstitutionalExistentialRiskCertification:
    def test_fix_158_contract(self) -> None:
        assert INSTITUTIONAL_EXISTENTIAL_RISK_FIX == "FIX 158"
        assert INSTITUTIONAL_EXISTENTIAL_RISK_SCHEMA_VERSION == (
            "mission_control_institutional_existential_risk_v1"
        )
        assert MUTATION_PERFORMED_FIX_158 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_158 is False
        assert AUTONOMOUS_SELF_PRESERVATION_ENABLED_FIX_158 is False
        assert AUTONOMOUS_CONTINUITY_ENFORCEMENT_ENABLED_FIX_158 is False
        assert CONSTITUTIONAL_OVERRIDE_AUTHORITY_ENABLED_FIX_158 is False
        assert INSTITUTIONAL_SELF_DEFENSE_AUTHORITY_ENABLED_FIX_158 is False
        assert GOVERNANCE_MUTATION_PERFORMED_FIX_158 is False
        assert EXISTENTIAL_RISK_RECOMMENDATION_EXECUTABLE is False
        assert "continuity_risk_observation" in EXISTENTIAL_RISK_RECORD_KINDS
        assert len(EXISTENTIAL_RISK_PRINCIPLES) >= 8
        assert len(GOVERNANCE_COLLAPSE_SCENARIOS) >= 4
        assert len(FRAGILITY_INDICATORS) >= 4
        assert len(EXTINCTION_PATH_CATALOG) >= 4

    def test_institutional_existential_risk_cognition_layer(self) -> None:
        _full_stack(SESSION)
        record, blockers = append_institutional_existential_risk_record(
            session_id=SESSION,
            kind="preservation_recommendation",
            content="Advisory: preserve human sovereignty over institutional continuity decisions.",
        )
        assert not blockers
        assert record is not None
        assert record["executable"] is False

        result = build_institutional_existential_risk(session_id=SESSION)
        assert result.ok is True
        assert result.existential_risk["institutional_existential_continuity_cognition"] is True
        assert result.existential_risk["existential_risk_record_count"] == 1

    def test_operator_api_includes_institutional_existential_risk_routes(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/institutional-existential-risk" in paths
        assert "/mission-control/institutional-existential-risk/record" in paths
