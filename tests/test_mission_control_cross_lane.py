# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control cross-lane observability."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.cross_lane.cross_lane_contract import (
    MUTATION_PERFORMED_FIX_128,
    OBSERVED_LANES,
)
from aethos_core.mission_control.cross_lane.snapshot_service import (
    build_mission_control_snapshot,
    is_mission_control_observability_intent,
)
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests as cp

    cp()
    get_settings.cache_clear()
    yield
    cp()
    get_settings.cache_clear()


def test_mission_control_intents():
    assert is_mission_control_observability_intent("show mission control snapshot")
    assert is_mission_control_observability_intent("show mission control dashboard")


def test_no_mutation():
    assert MUTATION_PERFORMED_FIX_128 is False
    assert len(OBSERVED_LANES) >= 6


def test_snapshot_with_plan():
    session = "mc-snap-128"
    _full_stack(session)
    result = build_mission_control_snapshot(session_id=session)
    assert result.ok
    assert result.snapshot.get("correlation_id")
    assert "software_delivery" in result.snapshot.get("lanes", {})
    assert result.snapshot.get("execution_health", {}).get("mutation_performed_in_snapshot") is False


def test_chat_route():
    session = "mc-route-128"
    _full_stack(session)
    turn = resolve_chat_turn(
        "show mission control snapshot",
        session_id=session,
        apply_relational_layer=False,
    )
    assert turn.intent == "mission_control_snapshot"
    assert turn.meta.get("mutation_performed") == "false"
    assert turn.meta.get("route_id") == "mission_control_cross_lane"
