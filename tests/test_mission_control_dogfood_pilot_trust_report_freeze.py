# SPDX-License-Identifier: Apache-2.0
"""FIX 186 — dogfood pilot trust report freeze tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_contract import (
    DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID,
    TRUST_RECOMMENDATION_FIX_186,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_181,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_183,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_intent import (
    is_dogfood_pilot_trust_report_freeze_intent,
    parse_dogfood_pilot_trust_report_freeze_record_intent,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    clear_dogfood_pilot_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from tests.test_mission_control_pilot_validation_trust_board import _validation_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def _seed_dogfood_pilot_audits() -> None:
    persist_pilot_run_audit(
        {
            "session_id": "dogfood-pilot-1",
            "repo_issue": "pilotmain/AethOS#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "pilot_report": {
                "stages_satisfied": ["issue_intake", "implementation_plan", "patch_proposal", "pr_open"],
                "stages_pending": [],
                "failure_class": "wrong_file_targeting_drift",
            },
            "blockers": [],
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": "dogfood-pilot-2",
            "repo_issue": "pilotmain/AethOS#1",
            "outcome": "partial",
            "stages_completed": ["intent_alignment"],
            "pilot_report": {
                "stages_satisfied": ["issue_intake", "implementation_plan", "implementation_branch"],
                "stages_pending": ["intent_alignment"],
            },
            "blockers": ["stage_blocked:intent_alignment"],
        }
    )
    persist_pilot_run_audit(
        {
            "session_id": "dogfood-pilot-3",
            "repo_issue": "pilotmain/AethOS#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "chat_steps": [
                {
                    "step_index": 1,
                    "stage": "implementation_plan",
                    "chat_message": "approve implementation planning\nI approve this governed software delivery implementation plan for human review.",
                    "chat_governance_routed": True,
                }
            ],
            "pilot_report": {
                "stages_satisfied": [
                    "issue_intake",
                    "implementation_plan",
                    "implementation_branch",
                    "patch_proposal",
                    "workspace_apply",
                    "workspace_verify",
                    "pr_draft",
                    "github_pr_preflight",
                    "branch_push",
                    "pr_open",
                ],
                "stages_pending": [],
                "evidence_bundle_ok": True,
            },
            "blockers": [],
            "railway_coupling_detected": False,
        }
    )


def _dogfood_trust_stack(session: str = "fix-186-test") -> None:
    _validation_stack("dogfood-pilot-3")
    _seed_dogfood_pilot_audits()


def test_dogfood_trust_report_freeze_intent():
    assert is_dogfood_pilot_trust_report_freeze_intent("show dogfood trust report freeze")
    assert is_dogfood_pilot_trust_report_freeze_intent("dogfood pilot trust baseline")
    assert not is_dogfood_pilot_trust_report_freeze_intent("run pilot harness")


def test_dogfood_trust_report_freeze_record_intent():
    parsed = parse_dogfood_pilot_trust_report_freeze_record_intent(
        "trust report freeze: AethOS dogfood Phase 1 baseline recorded"
    )
    assert parsed == ("trust_report_freeze_artifact", "AethOS dogfood Phase 1 baseline recorded")


def test_build_dogfood_trust_report_freeze_composes_pilots():
    _dogfood_trust_stack()
    result = build_dogfood_pilot_trust_report_freeze(session_id="fix-186-test")
    assert result.ok is True
    report = result.dogfood_pilot_trust_report_freeze
    assert report["trust_status"] == TRUST_RECOMMENDATION_FIX_186
    assert report["pilot_reexecution_performed"] is False
    assert report["multi_repo_expansion_blocked"] is True

    sections = report["sections"]
    timeline = sections["frozen_evidence_timeline"]
    assert len(timeline) == 3
    assert timeline[0]["pilot_id"] == "dogfood-pilot-1"
    assert timeline[2]["pilot_id"] == "dogfood-pilot-3"
    assert sections["trust_boundary_matrix"]
    assert sections["expansion_recommendation"][0]["proceed"] is False
    assert sections["evidence_index"]

    section_keys = set(sections)
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_181)
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_183)


def test_chat_route_show_dogfood_trust_report_freeze():
    _dogfood_trust_stack()
    turn = resolve_chat_turn("show dogfood trust report freeze", session_id="fix-186-chat")
    assert turn.intent == "mission_control_dogfood_pilot_trust_report_freeze"
    assert (turn.meta or {}).get("route_id") == DOGFOOD_PILOT_TRUST_REPORT_FREEZE_ROUTE_ID
    assert "dogfood-pilot-1" in turn.reply


def test_dogfood_trust_report_freeze_api():
    _dogfood_trust_stack()
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/dogfood-pilot-trust-report-freeze",
        params={"session_id": "fix-186-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["pilot_reexecution_performed"] is False
    assert payload["dogfood_pilot_trust_report_freeze"]["trust_status"] == TRUST_RECOMMENDATION_FIX_186
    assert payload.get("markdown")
