# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — governance insights certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.governance_insights.governance_insights_contract import (
    AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143,
    GOVERNANCE_INSIGHTS_FIX,
    GOVERNANCE_INSIGHTS_SCHEMA_VERSION,
    GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143,
    INSIGHT_EXECUTABLE,
    MUTATION_PERFORMED_FIX_143,
    POLICY_AUTO_TUNING_ENABLED_FIX_143,
)
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-gov-insights-cert-143"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlGovernanceInsightsCertification:
    def test_fix_143_contract(self) -> None:
        assert GOVERNANCE_INSIGHTS_FIX == "FIX 143"
        assert GOVERNANCE_INSIGHTS_SCHEMA_VERSION == "mission_control_governance_insights_v1"
        assert MUTATION_PERFORMED_FIX_143 is False
        assert POLICY_AUTO_TUNING_ENABLED_FIX_143 is False
        assert GOVERNANCE_SELF_MODIFICATION_ENABLED_FIX_143 is False
        assert AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_143 is False
        assert INSIGHT_EXECUTABLE is False

    def test_governance_insights_readonly_meta_layer(self) -> None:
        _full_stack(SESSION)
        result = build_governance_insights(session_id=SESSION)
        assert result.ok is True
        assert result.insights["read_only"] is True
        assert "governance_health_metrics" in result.insights.get("insights", {})

    def test_operator_api_includes_governance_insights_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/governance-insights" in paths
