# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — operational memory certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.operational_memory_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
    MUTATION_PERFORMED_FIX_139,
    OPERATIONAL_MEMORY_FIX,
    OPERATIONAL_MEMORY_SCHEMA_VERSION,
)
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-op-memory-cert-139"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    yield
    clear_for_tests()


class TestMissionControlOperationalMemoryCertification:
    def test_fix_139_contract(self) -> None:
        assert OPERATIONAL_MEMORY_FIX == "FIX 139"
        assert OPERATIONAL_MEMORY_SCHEMA_VERSION == "mission_control_operational_memory_v1"
        assert MUTATION_PERFORMED_FIX_139 is False
        assert AUTONOMOUS_ADAPTATION_ENABLED_FIX_139 is False

    def test_operational_memory_readonly_from_evidence(self) -> None:
        _full_stack(SESSION)
        result = build_operational_memory_graph(session_id=SESSION)
        assert result.ok is True
        assert result.graph["read_only"] is True
        assert result.graph["autonomous_adaptation_enabled"] is False
        assert result.graph["graph"]["stats"]["node_count"] >= 1

    def test_operator_api_includes_operational_memory_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/operational-memory" in paths
