# SPDX-License-Identifier: Apache-2.0
"""FIX 129 — Mission Control cross-lane HTTP API (read-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    get_settings.cache_clear()
    yield
    cp()
    get_settings.cache_clear()


def test_cross_lane_snapshot_api_readonly():
    session = "mc-api-129"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/cross-lane/snapshot", params={"session_id": session})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["route_id"] == "mission_control_cross_lane"
    snap = body["snapshot"]
    assert snap["session_id"] == session
    assert "software_delivery" in snap["lanes"]
    assert snap["execution_health"]["mutation_performed_in_snapshot"] is False


def test_unified_timeline_populated_from_lanes():
    session = "mc-timeline-129"
    _full_stack(session)
    from aethos_core.mission_control.cross_lane.snapshot_service import build_mission_control_snapshot

    result = build_mission_control_snapshot(session_id=session)
    assert result.ok
    timeline = result.snapshot.get("unified_timeline") or []
    assert len(timeline) >= 1
    assert timeline[0].get("lane") == "software_delivery"
