# SPDX-License-Identifier: Apache-2.0
"""FIX 131 — Mission Control lane drilldown (read-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.cross_lane.lane_drilldown_contract import MUTATION_PERFORMED_FIX_131
from aethos_core.mission_control.cross_lane.lane_drilldown_service import build_lane_drilldown
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    get_settings.cache_clear()
    yield
    cp()
    get_settings.cache_clear()


def test_drilldown_readonly_contract():
    assert MUTATION_PERFORMED_FIX_131 is False


def test_software_delivery_drilldown_sections():
    session = "mc-drill-131"
    _full_stack(session)
    result = build_lane_drilldown(session_id=session, lane="software_delivery")
    assert result.ok
    ids = {s["section_id"] for s in result.sections}
    assert "governance_gates" in ids
    assert "timeline" in ids
    assert "execution_contract" in ids
    assert "audit_trail" in ids


def test_unknown_lane_blocked():
    result = build_lane_drilldown(session_id="x", lane="not_a_lane")
    assert not result.ok


def test_lane_drilldown_api():
    session = "mc-api-drill-131"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        f"/api/v1/mission-control/cross-lane/lane/software_delivery/drilldown",
        params={"session_id": session},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert len(body["sections"]) >= 5
