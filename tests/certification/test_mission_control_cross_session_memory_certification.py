# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — cross-session operational memory certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
    AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140,
    CROSS_SESSION_MEMORY_FIX,
    CROSS_SESSION_MEMORY_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_140,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
    build_cross_session_operational_memory,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-xsess-cert-140"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlCrossSessionMemoryCertification:
    def test_fix_140_contract(self) -> None:
        assert CROSS_SESSION_MEMORY_FIX == "FIX 140"
        assert CROSS_SESSION_MEMORY_SCHEMA_VERSION == "mission_control_cross_session_memory_v1"
        assert MUTATION_PERFORMED_FIX_140 is False
        assert AUTONOMOUS_ADAPTATION_ENABLED_FIX_140 is False
        assert AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140 is False

    def test_cross_session_memory_readonly_organizational_layer(self) -> None:
        _full_stack(SESSION)
        result = build_cross_session_operational_memory(session_id=SESSION, ingest_current=True)
        assert result.ok is True
        assert result.memory["read_only"] is True
        assert result.memory["autonomous_adaptation_enabled"] is False
        assert result.memory["organizational_memory"]["operator_history"]

    def test_operator_api_includes_cross_session_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/operational-memory/cross-session" in paths
