# SPDX-License-Identifier: Apache-2.0
"""Filtered view state tests."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from aethos_core.operational_planner.adapters.railway_wide_health import compose_railway_provider_wide_health_reply
from aethos_core.operational_planner.planner_router import compose_planned_operational_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.filtered_view_state import get_active_filter_mode, get_source_payload
from aethos_core.response_composition.final_response_validator import validate_json_final_response
from aethos_core.response_composition.operational_result_store import get_latest_operational_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _rows() -> list[dict]:
    healthy = {"service": "api", "project": "demo", "environment": "production", "status": "running", "health": "healthy"}
    failed = [
        {"service": "pilotcore-finance-engine", "project": "pilotcore-finance-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "worker", "project": "talking-avatar-worker", "environment": "production", "status": "failed", "health": "failed"},
    ]
    return [healthy, *failed]


def _seed(session_id: str) -> None:
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(_rows(), None),
    ):
        compose_railway_provider_wide_health_reply(session_id=session_id)


def test_show_only_failed_stores_filtered_view():
    _seed("view-failed")
    compose_planned_operational_reply("show only failed", session_id="view-failed")
    assert get_active_filter_mode(session_id="view-failed") == "failed"


def test_json_after_failed_returns_failed_json():
    _seed("view-json")
    compose_planned_operational_reply("show only failed", session_id="view-json")
    body, intent, meta = compose_planned_operational_reply("json", session_id="view-json")
    assert intent == "operational_response_json"
    assert meta["filter_mode"] == "failed"
    validation = validate_json_final_response(body)
    assert validation.ok is True
    assert validation.parsed_json["metadata"]["filter"] == "failed"
    assert len(validation.parsed_json["services"]) == 3
    assert "failures" not in validation.parsed_json


def test_show_all_restores_full_result():
    _seed("view-all")
    compose_planned_operational_reply("show only failed", session_id="view-all")
    compose_planned_operational_reply("show all", session_id="view-all")
    assert get_active_filter_mode(session_id="view-all") == "all"
    body, _, meta = compose_planned_operational_reply("table format please", session_id="view-all")
    assert meta["filter_mode"] == "all"
    assert "api" in body


def test_source_payload_not_mutated():
    _seed("view-source")
    before = get_source_payload(session_id="view-source")
    assert before is not None
    before_snapshot = json.dumps(before, sort_keys=True)
    compose_planned_operational_reply("show only failed", session_id="view-source")
    after = get_source_payload(session_id="view-source")
    assert after is not None
    assert json.dumps(after, sort_keys=True) == before_snapshot
    result = get_latest_operational_result(session_id="view-source")
    assert result is not None
    assert len(result.result_payload.get("services") or []) == 4
