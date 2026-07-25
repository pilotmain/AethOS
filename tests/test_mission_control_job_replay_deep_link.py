# SPDX-License-Identifier: Apache-2.0
"""FIX 137B — Mission Control replay deep links."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    audit_link_ref,
    build_link_index,
    evidence_link_ref,
    resolve_step_index,
    timeline_link_ref,
)
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()


def test_link_ref_helpers_stable():
    t = timeline_link_ref(lane="software_delivery", action="planning_approved", timestamp="2026-05-26T12:00:00Z")
    assert t.startswith("timeline:")
    a = audit_link_ref(approval_id="mc-ui-apr-abc123")
    assert a == "audit:mc-ui-apr-abc123"
    e = evidence_link_ref(recorded_at="2026-05-26T12:00:00Z", phase="applied", source_file="x.json")
    assert e.startswith("evidence:")


def test_replay_includes_link_index():
    session = "mc-replay-dl-137b"
    _full_stack(session)
    result = build_job_replay(session_id=session)
    assert result.ok is True
    index = result.replay.get("link_index") or {}
    assert len(index) >= 1
    steps = result.replay.get("steps") or []
    assert steps[0].get("link_key")


def test_resolve_api_finds_timeline_link():
    session = "mc-replay-resolve-137b"
    _full_stack(session)
    replay = build_job_replay(session_id=session).replay
    timeline_ref = next(
        (alias for alias in (replay.get("link_index") or {}) if str(alias).startswith("timeline:")),
        None,
    )
    assert timeline_ref is not None
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/job-replay/resolve",
        params={"session_id": session, "link": timeline_ref},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["mutation_performed"] is False
    assert body["step_index"] is not None


def test_resolve_step_index_by_numeric_string():
    steps = [{"step_index": 0, "link_key": "rpl-a"}, {"step_index": 1, "link_key": "rpl-b"}]
    index = build_link_index(steps)
    assert resolve_step_index(steps=steps, link_index=index, link="1") == 1
