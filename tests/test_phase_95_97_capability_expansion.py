# SPDX-License-Identifier: Apache-2.0
"""Phase 9.5 / 9.7 capability and self-improvement tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.onboarding.companion_onboarding import build_companion_onboarding_state
from aethos_core.self_improvement.intent import is_self_improvement_intent, parse_self_improvement_repository
from aethos_core.self_improvement.service import build_self_improvement_plan
from aethos_core.social.orchestration import clear_social_drafts_for_tests, list_social_drafts, schedule_social_draft


@pytest.fixture(autouse=True)
def _clean_social():
    clear_social_drafts_for_tests()
    yield
    clear_social_drafts_for_tests()


def test_companion_onboarding_state():
    state = build_companion_onboarding_state()
    assert state.ok
    assert len(state.steps) >= 4
    assert 0.0 <= state.progress <= 1.0


def test_social_draft_orchestration_no_publish():
    result = schedule_social_draft(platform="linkedin", topic="AethOS launch")
    assert result.ok
    assert result.published is False
    assert result.status == "pending_approval"
    drafts = list_social_drafts()
    assert len(drafts) == 1
    assert drafts[0]["published"] is False


def test_self_improvement_intent_parsing():
    assert is_self_improvement_intent("read open GitHub issues for pilotmain/AethOS")
    assert parse_self_improvement_repository("prepare a pr plan for pilotmain/AethOS") == "pilotmain/AethOS"


@patch("aethos_core.self_improvement.issues.intake.fetch_github_issues")
def test_self_improvement_plan_dry_run(mock_fetch):
    mock_fetch.return_value = {
        "ok": True,
        "issues": [{"number": 1, "title": "Doc fix", "html_url": "https://github.com/pilotmain/AethOS/issues/1"}],
    }
    result = build_self_improvement_plan(repository="pilotmain/AethOS")
    assert result.ok
    assert result.execution_enabled is False
    assert result.branch.get("merge_allowed") is False


def test_runtime_onboarding_and_social_api():
    client = TestClient(app)
    onboarding = client.get("/api/v1/runtime/onboarding/companion")
    assert onboarding.status_code == 200
    assert onboarding.json()["ok"] is True

    draft = client.post(
        "/api/v1/runtime/social/drafts",
        json={"platform": "linkedin", "topic": "governed ops"},
    )
    assert draft.status_code == 200
    assert draft.json()["published"] is False

    listed = client.get("/api/v1/runtime/social/drafts")
    assert listed.json()["count"] >= 1


@patch("aethos_core.self_improvement.issues.intake.fetch_github_issues")
def test_runtime_self_improvement_plan_api(mock_fetch):
    mock_fetch.return_value = {"ok": True, "issues": []}
    client = TestClient(app)
    r = client.get("/api/v1/runtime/self-improvement/plan", params={"repository": "pilotmain/AethOS"})
    assert r.status_code == 200
    body = r.json()
    assert body["merge_allowed"] is False
