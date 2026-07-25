# SPDX-License-Identifier: Apache-2.0
"""Semantic response composition runtime tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_planner.adapters.railway_wide_health import compose_railway_provider_wide_health_reply
from aethos_core.operational_planner.planner_router import compose_planned_operational_reply
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.operational_result_store import get_latest_operational_result
from aethos_core.response_composition.response_composer import try_compose_rerender_reply
from aethos_core.response_composition.response_memory import get_response_context


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    yield
    clear_provider_wide_health_for_tests()


def _rows() -> list[dict]:
    return [
        {"service": "pilotos-api", "project": "pilotos", "environment": "production", "status": "running", "health": "healthy"},
        {"service": "pilotcore-finance-engine", "project": "pilotcore-finance-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "MongoDB", "project": "pilotcore-sales-engine", "environment": "production", "status": "failed", "health": "failed"},
        {"service": "SpeakGlobal AI", "project": "confident-wholeness", "environment": "production", "status": "unknown", "health": "unknown"},
    ]


def _seed_report(session_id: str) -> None:
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(_rows(), None),
    ):
        compose_railway_provider_wide_health_reply(session_id=session_id)


def test_follow_up_table_rendering_without_rerun():
    _seed_report("rerender-table")
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    ) as collect:
        body, intent, meta = compose_planned_operational_reply("table format please", session_id="rerender-table")
        collect.assert_not_called()
    assert meta["from_cache"] == "true"
    assert meta["output_format"] == "table"
    assert intent == "operational_response_table"
    assert "| Service | Project |" in body
    assert "no refresh" in body.lower()


def test_summary_rendering():
    _seed_report("rerender-summary")
    body, intent, meta = try_compose_rerender_reply("summary only", session_id="rerender-summary")
    assert body is not None
    assert meta["from_cache"] == "true"
    assert intent == "operational_response_executive_summary"
    assert "Summary:" in body
    assert "| Service |" not in body


def test_grouped_failed_rendering():
    _seed_report("rerender-failed")
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    ) as collect:
        body, intent, meta = compose_planned_operational_reply("show only failed", session_id="rerender-failed")
        collect.assert_not_called()
    assert meta["from_cache"] == "true"
    assert "MongoDB" in body
    assert "pilotcore-finance-engine" in body
    assert "Failed services:" in body
    assert "pilotos-api" not in body.split("Failed services:")[-1]


def test_json_rendering():
    _seed_report("rerender-json")
    body, intent, meta = try_compose_rerender_reply("json", session_id="rerender-json")
    assert body is not None
    assert meta["from_cache"] == "true"
    assert meta.get("validation_status") == "passed"
    assert intent == "operational_response_json"
    from aethos_core.response_composition.final_response_validator import validate_json_final_response

    validation = validate_json_final_response(body)
    assert validation.ok is True
    assert "services" in validation.parsed_json
    assert "metadata" in validation.parsed_json
    assert "failures" not in validation.parsed_json


def test_no_rerun_on_re_render():
    _seed_report("no-rerun")
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
    ) as collect:
        compose_planned_operational_reply("group by project", session_id="no-rerun")
        compose_planned_operational_reply("json", session_id="no-rerun")
        compose_planned_operational_reply("summary only", session_id="no-rerun")
        collect.assert_not_called()


def test_output_format_preserved_across_turns():
    _seed_report("format-memory")
    compose_planned_operational_reply("table format please", session_id="format-memory")
    context = get_response_context(session_id="format-memory")
    assert context["has_result"] is True
    assert context["last_output_format"] == "table"
    result = get_latest_operational_result(session_id="format-memory")
    assert result is not None
    assert len(result.render_history) >= 2


def test_provider_wide_check_after_named_health_refreshes_inventory():
    from aethos_core.response_composition.response_composer import store_provider_wide_health_result
    from aethos_core.response_composition.response_intent_classifier import classify_response_intent

    store_provider_wide_health_result(
        session_id="wide-after-named",
        provider="railway",
        payload={
            "services": [
                {"service": "aethos-api", "project": "pilotos", "environment": "staging", "status": "running", "health": "healthy"},
                {"service": "aethos-ui", "project": "pilotos", "environment": "staging", "status": "running", "health": "healthy"},
            ]
        },
        summary={"total": 2, "healthy": 2, "failed": 0, "unknown": 0},
        scope="named_service_health",
        meta={"route_id": "multi_provider_health"},
    )
    intent = classify_response_intent(
        "check all services in railway and report healthy vs failed",
        session_id="wide-after-named",
    )
    assert intent.kind == "new_operation"

    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(_rows(), None),
    ) as collect:
        body, intent, meta = compose_planned_operational_reply(
            "check all services in railway and report healthy vs failed",
            session_id="wide-after-named",
        )
        collect.assert_called_once()

    assert meta.get("from_cache") != "true"
    assert meta.get("scope") == "provider_wide"
    assert "no refresh" not in body.lower()
    assert "MongoDB" in body
    assert "pilotos-api" in body
