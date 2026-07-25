# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — mission knowledge spaces certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
    AUTONOMOUS_ACTION_ENABLED_FIX_141,
    KNOWLEDGE_SPACES_FIX,
    KNOWLEDGE_SPACES_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_141,
)
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_service import search_mission_knowledge_spaces
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-knowledge-cert-141"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_operational_memory_records_for_tests()
    yield
    clear_for_tests()
    clear_operational_memory_records_for_tests()


class TestMissionControlKnowledgeSpacesCertification:
    def test_fix_141_contract(self) -> None:
        assert KNOWLEDGE_SPACES_FIX == "FIX 141"
        assert KNOWLEDGE_SPACES_SCHEMA_VERSION == "mission_control_knowledge_spaces_v1"
        assert MUTATION_PERFORMED_FIX_141 is False
        assert AUTONOMOUS_ACTION_ENABLED_FIX_141 is False
        assert AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141 is False

    def test_knowledge_spaces_readonly_search(self) -> None:
        _full_stack(SESSION)
        result = search_mission_knowledge_spaces(session_id=SESSION, query="incident blocker", ingest_current=True)
        assert result.ok is True
        assert result.payload["read_only"] is True
        assert result.payload["recommendations"]

    def test_operator_api_includes_knowledge_spaces_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/knowledge-spaces/search" in paths
