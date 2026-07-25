# SPDX-License-Identifier: Apache-2.0
"""FIX 147 — mission readiness review board."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_contract import (
    GO_NO_GO_HOLD_VALUES,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_intent import (
    is_mission_readiness_review_intent,
)
from aethos_core.mission_control.mission_readiness_review.mission_readiness_review_service import (
    build_mission_readiness_review,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()


def test_mission_readiness_review_intent():
    assert is_mission_readiness_review_intent("show mission readiness review")
    assert is_mission_readiness_review_intent("go no-go review")
    assert not is_mission_readiness_review_intent("autonomous go decision execute")


def test_mission_readiness_review_api_readonly():
    session = "mc-readiness-147"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/mission-readiness-review",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["human_review_required"] is True
    assert body["execution_authority_delegated"] is False
    assert body["autonomous_go_no_go_execution_enabled"] is False
    review = body["review"]
    assert review["schema_version"] == "mission_control_mission_readiness_review_v1"
    sections = review["sections"]
    assert "readiness_score_summary" in sections
    assert "go_no_go_hold_recommendation" in sections
    assert "pending_approvals" in sections
    assert review["go_no_go_hold"] in GO_NO_GO_HOLD_VALUES
    assert review["all_recommendations_executable"] is False
    assert "Mission Readiness Review Board" in body["markdown"]


def test_mission_readiness_review_chat_route():
    session = "mc-readiness-chat-147"
    _full_stack(session)
    result = resolve_chat_turn("show mission readiness review", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_mission_readiness_review"
    assert result.meta.get("mutation_performed") == "false"
    assert result.meta.get("human_review_required") == "true"
    assert "Mission Readiness Review Board" in result.reply


def test_mission_readiness_review_builds_from_orchestration():
    session = "mc-readiness-src-147"
    _full_stack(session)
    result = build_mission_readiness_review(session_id=session)
    assert result.ok is True
    assert result.review["sources"]["mission_orchestration"] is True
    go_rec = result.review["sections"]["go_no_go_hold_recommendation"]
    assert go_rec["human_review_required"] is True
    assert go_rec["executable"] is False
