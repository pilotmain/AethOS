# SPDX-License-Identifier: Apache-2.0
"""FIX 240 — repository knowledge graph tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_1_REPOSITORY,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_contract import (
    CODE_MODIFICATION_AUTHORITY_FIX_240,
    KNOWLEDGE_GRAPH_EXECUTION_FIX_240,
    REPOSITORY_AUTHORITY_FIX_240,
    REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_intent import (
    is_repository_knowledge_graph_intent,
    parse_repository_knowledge_graph_record_intent,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_service import (
    build_repository_knowledge_graph,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
    append_repository_knowledge_graph_record,
    clear_repository_knowledge_graph_records_for_tests,
)
from tests.test_mission_control_governed_merge_lifecycle import _seed_merge_lifecycle_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_repository_knowledge_graph_records_for_tests()
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
        clear_governed_merge_lifecycle_records_for_tests,
    )
    from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
        clear_bounded_multi_agent_delivery_execution_records_for_tests,
    )
    from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
        clear_issue_intent_alignment_records_for_tests,
    )
    from aethos_core.software_delivery.github_pr_open_store import clear_for_tests as clear_pr_open
    from aethos_core.software_delivery.github_pr_preflight_store import clear_for_tests as clear_preflight
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as clear_plan
    from aethos_core.software_delivery.workspace_verification_store import clear_for_tests as clear_verify

    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_repository_knowledge_graph_records_for_tests()
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan()
    clear_verify()
    clear_preflight()
    clear_pr_open()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def _seed_knowledge_graph_stack(session: str) -> str:
    plan_id = _seed_merge_lifecycle_stack(session)
    append_repository_knowledge_graph_record(
        session_id=session,
        kind="ownership_record_note",
        content="Mission control subsystem owned by platform-engineering",
        repository_id=PHASE_1_REPOSITORY,
        metadata={"subsystem": "mission-control", "team": "platform-engineering"},
    )
    append_repository_knowledge_graph_record(
        session_id=session,
        kind="dependency_mapping_note",
        content="Web app depends on aethos-core API surface",
        repository_id=PHASE_1_REPOSITORY,
        metadata={"source": "web-app", "target": "aethos-core", "dependency_type": "internal"},
    )
    return plan_id


def test_repository_knowledge_graph_intent():
    assert is_repository_knowledge_graph_intent("show repository knowledge graph")
    assert is_repository_knowledge_graph_intent("engineering intelligence dashboard")
    assert not is_repository_knowledge_graph_intent("generate patch now")


def test_ownership_record_intent():
    parsed = parse_repository_knowledge_graph_record_intent(
        "ownership record: subsystem=mission-control team=platform-engineering"
    )
    assert parsed is not None
    assert parsed[0] == "ownership_record_note"
    assert parsed[2].get("subsystem") == "mission-control"
    assert parsed[2].get("team") == "platform-engineering"


def test_dependency_mapping_record_intent():
    parsed = parse_repository_knowledge_graph_record_intent(
        "dependency mapping: source=web-app target=fastapi type=external"
    )
    assert parsed is not None
    assert parsed[0] == "dependency_mapping_note"
    assert parsed[2].get("dependency_type") == "external"


def test_build_repository_knowledge_graph():
    _seed_knowledge_graph_stack("fix-240-graph")
    result = build_repository_knowledge_graph(session_id="fix-240-graph")
    graph = result.repository_knowledge_graph
    assert graph["repository_authority"] is REPOSITORY_AUTHORITY_FIX_240
    assert graph["code_modification_authority"] is CODE_MODIFICATION_AUTHORITY_FIX_240
    assert graph["knowledge_graph_execution"] is KNOWLEDGE_GRAPH_EXECUTION_FIX_240
    assert graph["repository_id"] == PHASE_1_REPOSITORY
    sections = graph["sections"]
    assert sections["architecture_graph"]
    assert sections["dependency_registry"]
    assert sections["ownership_registry"]
    assert sections["change_impact_assessment"]
    assert sections["engineering_intelligence_dashboard"]
    assert sections["cross_repository_knowledge"]


def test_change_impact_for_affected_files():
    _seed_knowledge_graph_stack("fix-240-impact")
    result = build_repository_knowledge_graph(session_id="fix-240-impact")
    impact = result.repository_knowledge_graph["sections"]["change_impact_assessment"][0]
    assert impact.get("blast_radius") == "single_file"
    assert impact.get("affected_systems")


def test_chat_route_show_knowledge_graph():
    _seed_knowledge_graph_stack("fix-240-chat")
    turn = resolve_chat_turn("show repository knowledge graph", session_id="fix-240-chat")
    assert turn.intent == "mission_control_repository_knowledge_graph"
    assert (turn.meta or {}).get("route_id") == REPOSITORY_KNOWLEDGE_GRAPH_ROUTE_ID


def test_repository_knowledge_graph_api():
    _seed_knowledge_graph_stack("fix-240-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/repository-knowledge-graph",
        params={"session_id": "fix-240-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["repository_authority"] is False
    assert payload["code_modification_authority"] is False
    assert payload["markdown"]
