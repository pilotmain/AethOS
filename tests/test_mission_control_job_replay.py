# SPDX-License-Identifier: Apache-2.0
"""FIX 137 — Mission Control job replay view."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()


def test_job_replay_api_readonly():
    session = "mc-replay-137"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/job-replay", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    replay = body["replay"]
    assert replay["schema_version"] == "mission_control_job_replay_v1"
    assert replay["step_count"] >= 1
    step = replay["steps"][0]
    assert "state_before" in step
    assert "state_after" in step
    assert "summary_markdown" in body
    assert "Step playback" in body["summary_markdown"]


def test_job_replay_steps_have_gates_and_receipts_fields():
    session = "mc-replay-fields-137"
    _full_stack(session)
    result = build_job_replay(session_id=session)
    assert result.ok is True
    assert result.replay["steps"]
    for step in result.replay["steps"]:
        assert "gates" in step
        assert "receipts" in step
        assert "blockers" in step
        assert "approvals" in step


def test_job_replay_unsupported_format():
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/job-replay",
        params={"session_id": "default", "format": "rerun"},
    )
    assert res.status_code == 400
