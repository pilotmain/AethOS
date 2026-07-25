# SPDX-License-Identifier: Apache-2.0
"""FIX 200 — governed merge lifecycle tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    append_bounded_multi_agent_delivery_execution_record,
    clear_bounded_multi_agent_delivery_execution_records_for_tests,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_contract import (
    AUTONOMOUS_MERGE_ENABLED_FIX_200,
    GOVERNED_MERGE_LIFECYCLE_ROUTE_ID,
    MERGE_AUTHORITY_FIX_200,
    MERGE_RECOMMENDATIONS,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_intent import (
    is_governed_merge_lifecycle_intent,
    parse_governed_merge_lifecycle_record_intent,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
    build_governed_merge_lifecycle,
    prepare_governed_merge_handoff,
)
from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_store import (
    append_governed_merge_lifecycle_record,
    clear_governed_merge_lifecycle_records_for_tests,
)
from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
    append_issue_intent_alignment_record,
    clear_issue_intent_alignment_records_for_tests,
)
from aethos_core.software_delivery.github_pr_open_store import (
    clear_for_tests as clear_pr_open_store,
    save_github_pr_open,
)
from aethos_core.software_delivery.github_pr_preflight_store import (
    clear_for_tests as clear_preflight_store,
    save_github_pr_preflight,
)
from aethos_core.software_delivery.issue_plan_store import (
    clear_for_tests as clear_plan_store,
    save_issue_plan,
)
from aethos_core.software_delivery.workspace_verification_store import (
    clear_for_tests as clear_verification_store,
    save_workspace_verification,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan_store()
    clear_verification_store()
    clear_preflight_store()
    clear_pr_open_store()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_governed_merge_lifecycle_records_for_tests()
    clear_plan_store()
    clear_verification_store()
    clear_preflight_store()
    clear_pr_open_store()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    clear_issue_intent_alignment_records_for_tests()
    get_settings.cache_clear()


def _seed_merge_lifecycle_stack(session: str) -> str:
    plan_id = f"plan-{session}"
    save_issue_plan(
        {
            "plan_id": plan_id,
            "session_id": session,
            "issue_reference": "pilotmain/AethOS#7",
            "title": "Governed merge lifecycle test",
            "affected_files": ["README.md"],
            "risk_assessment": {"risk_tier": "low", "blast_radius": "single_file"},
        }
    )
    save_workspace_verification(
        {
            "verification_id": f"verify-{session}",
            "plan_id": plan_id,
            "session_id": session,
            "status": "passed",
            "pr_drafting_unblocked": True,
        }
    )
    save_github_pr_preflight(
        {
            "preflight_id": f"preflight-{session}",
            "plan_id": plan_id,
            "session_id": session,
            "status": "preflight_passed",
            "preflight_approved": True,
            "github_creation_unblocked": True,
        }
    )
    save_github_pr_open(
        {
            "pr_open_id": f"pr-open-{session}",
            "plan_id": plan_id,
            "session_id": session,
            "status": "opened",
            "pr_number": 42,
            "pr_url": "https://github.com/pilotmain/AethOS/pull/42",
            "repository": "pilotmain/AethOS",
        }
    )
    append_issue_intent_alignment_record(
        session_id=session,
        kind="alignment_record",
        content="Intent aligned for merge lifecycle test",
        metadata={"alignment_score": 88},
    )
    for role_id in ("verification_agent", "diff_audit_agent", "risk_agent"):
        append_bounded_multi_agent_delivery_execution_record(
            session_id=session,
            plan_id=plan_id,
            kind="agent_execution_receipt",
            content=f"{role_id}:completed",
            metadata={
                "agent_role_id": role_id,
                "status": "completed",
                "work_performed": True,
                "risk_score": 72 if role_id == "risk_agent" else None,
            },
        )
    return plan_id


def test_governed_merge_lifecycle_intent():
    assert is_governed_merge_lifecycle_intent("show governed merge lifecycle")
    assert is_governed_merge_lifecycle_intent("merge review packet")
    assert is_governed_merge_lifecycle_intent("prepare merge handoff")
    assert not is_governed_merge_lifecycle_intent("autonomous merge now")


def test_merge_decision_record_intent():
    parsed = parse_governed_merge_lifecycle_record_intent(
        "merge decision approve: verification and risk reviewed — ready for handoff"
    )
    assert parsed == (
        "merge_decision_approve",
        "verification and risk reviewed — ready for handoff",
    )


def test_build_merge_lifecycle_without_plan():
    result = build_governed_merge_lifecycle(session_id="fix-200-empty")
    report = result.governed_merge_lifecycle
    assert report["merge_authority"] is MERGE_AUTHORITY_FIX_200
    assert report["autonomous_merge_enabled"] is AUTONOMOUS_MERGE_ENABLED_FIX_200
    assert "no_issue_plan_for_session" in result.blockers


def test_build_merge_lifecycle_with_evidence():
    _seed_merge_lifecycle_stack("fix-200-stack")
    result = build_governed_merge_lifecycle(session_id="fix-200-stack")
    report = result.governed_merge_lifecycle
    sections = report["sections"]
    readiness = sections["merge_readiness_assessment"][0]
    recommendation = sections["merge_recommendation"][0]

    assert readiness["pr_open_complete"] is True
    assert readiness["verification_passed"] is True
    assert recommendation["recommendation"] in MERGE_RECOMMENDATIONS
    assert recommendation["recommendation_only"] is True
    assert sections["merge_execution_adapter"][0]["provider"] == "github"
    assert sections["merge_handoff_artifact"] == []


def test_merge_handoff_after_human_approval():
    _seed_merge_lifecycle_stack("fix-200-handoff")
    append_governed_merge_lifecycle_record(
        session_id="fix-200-handoff",
        kind="merge_decision_approve",
        content="Operator approves merge after review",
        plan_id="plan-fix-200-handoff",
    )
    handoff = prepare_governed_merge_handoff(session_id="fix-200-handoff")
    assert handoff.ok is True
    assert handoff.merge_handoff["handoff_executable"] is False
    assert "gh pr merge" in str(
        handoff.merge_handoff.get("merge_execution_adapter", {}).get("command_template")
    )

    lifecycle = build_governed_merge_lifecycle(session_id="fix-200-handoff")
    assert lifecycle.governed_merge_lifecycle["sections"]["merge_handoff_artifact"]


def test_chat_route_show_merge_lifecycle():
    _seed_merge_lifecycle_stack("fix-200-chat")
    turn = resolve_chat_turn("show governed merge lifecycle", session_id="fix-200-chat")
    assert turn.intent == "mission_control_governed_merge_lifecycle"
    assert (turn.meta or {}).get("route_id") == GOVERNED_MERGE_LIFECYCLE_ROUTE_ID


def test_governed_merge_lifecycle_api():
    _seed_merge_lifecycle_stack("fix-200-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/governed-merge-lifecycle",
        params={"session_id": "fix-200-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["merge_authority"] is False
    assert payload["autonomous_merge_enabled"] is False
    assert payload["governed_merge_lifecycle"]["current_stage"] == "merge_review"
    assert payload["markdown"]
