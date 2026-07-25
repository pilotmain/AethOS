# SPDX-License-Identifier: Apache-2.0
"""FIX 145 — mission strategy certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_strategy.mission_strategy_contract import (
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145,
    AUTONOMOUS_PLANNING_ENABLED_FIX_145,
    MISSION_STRATEGY_FIX,
    MISSION_STRATEGY_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_145,
    ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145,
    STRATEGY_RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.mission_strategy.mission_strategy_service import build_mission_strategy
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-strategy-cert-145"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlMissionStrategyCertification:
    def test_fix_145_contract(self) -> None:
        assert MISSION_STRATEGY_FIX == "FIX 145"
        assert MISSION_STRATEGY_SCHEMA_VERSION == "mission_control_mission_strategy_v1"
        assert MUTATION_PERFORMED_FIX_145 is False
        assert AUTONOMOUS_PLANNING_ENABLED_FIX_145 is False
        assert ORGANIZATIONAL_SELF_DIRECTION_ENABLED_FIX_145 is False
        assert AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_145 is False
        assert STRATEGY_RECOMMENDATION_EXECUTABLE is False

    def test_mission_strategy_readonly_strategic_layer(self) -> None:
        _full_stack(SESSION)
        result = build_mission_strategy(session_id=SESSION)
        assert result.ok is True
        assert result.strategy["read_only"] is True
        assert result.strategy["sections"]["organizational_risk_concentration"]

    def test_operator_api_includes_mission_strategy_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/mission-strategy" in paths
