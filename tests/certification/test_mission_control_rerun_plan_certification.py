# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — governed rerun plan certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.rerun_planning.rerun_plan_contract import (
    MUTATION_PERFORMED_FIX_138,
    RERUN_EXECUTION_ENABLED_FIX_138,
    RERUN_PLAN_FIX,
    RERUN_PLAN_SCHEMA_VERSION,
)
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-rerun-cert-138"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    yield
    clear_for_tests()


class TestMissionControlRerunPlanCertification:
    def test_fix_138_contract(self) -> None:
        assert RERUN_PLAN_FIX == "FIX 138"
        assert RERUN_PLAN_SCHEMA_VERSION == "mission_control_rerun_plan_v1"
        assert MUTATION_PERFORMED_FIX_138 is False
        assert RERUN_EXECUTION_ENABLED_FIX_138 is False

    def test_rerun_plan_readonly_from_replay(self) -> None:
        _full_stack(SESSION)
        result = build_governed_rerun_plan(session_id=SESSION)
        assert result.ok is True
        assert result.plan["read_only"] is True
        assert result.plan["rerun_execution_enabled"] is False
        assert result.plan["replay_derived_plan"]["step_count"] is not None

    def test_operator_api_includes_rerun_plan_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/rerun-plan" in paths
