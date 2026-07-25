# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — agent execution quality and throughput metrics tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID,
    AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
    EXECUTION_PERFORMED_FIX_190,
    METRIC_AGENT_ROLE_IDS,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_intent import (
    is_agent_execution_quality_throughput_metrics_intent,
    parse_agent_execution_quality_throughput_metrics_record_intent,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_service import (
    build_agent_execution_quality_throughput_metrics,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_store import (
    clear_agent_execution_quality_throughput_metrics_records_for_tests,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_store import (
    append_bounded_multi_agent_delivery_execution_record,
    clear_bounded_multi_agent_delivery_execution_records_for_tests,
)
from tests.test_mission_control_bounded_execution_participation import _participation_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_agent_execution_quality_throughput_metrics_records_for_tests()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_agent_execution_quality_throughput_metrics_records_for_tests()
    clear_bounded_multi_agent_delivery_execution_records_for_tests()
    get_settings.cache_clear()


def _seed_fix_189_receipts(session: str) -> None:
    for role_id in METRIC_AGENT_ROLE_IDS:
        append_bounded_multi_agent_delivery_execution_record(
            session_id=session,
            kind="agent_execution_receipt",
            content=f"{role_id}:completed:artifact",
            metadata={
                "agent_role_id": role_id,
                "status": "completed",
                "artifact_type": "test_artifact",
                "work_performed": True,
                "blockers": [],
                "risk_score": 75 if role_id == "risk_agent" else None,
            },
        )


def test_agent_execution_metrics_intent():
    assert is_agent_execution_quality_throughput_metrics_intent("show agent execution metrics")
    assert not is_agent_execution_quality_throughput_metrics_intent("metrics grant authority")


def test_metrics_record_intent():
    parsed = parse_agent_execution_quality_throughput_metrics_record_intent(
        "agent metrics observation: throughput improved after planner retry"
    )
    assert parsed == ("metrics_observation", "throughput improved after planner retry")


def test_build_metrics_without_receipts():
    result = build_agent_execution_quality_throughput_metrics(session_id="fix-190-test")
    assert result.ok is True
    report = result.agent_execution_quality_throughput_metrics
    assert report["agent_metrics_grant_authority"] is AGENT_METRICS_GRANT_AUTHORITY_FIX_190
    assert report["execution_performed"] is EXECUTION_PERFORMED_FIX_190
    assert report["throughput_label"] == "unmeasured"
    assert "no_fix_189_execution_receipts" in result.blockers


def test_build_metrics_with_receipts():
    _participation_stack("fix-190-stack")
    _seed_fix_189_receipts("fix-190-stack")
    result = build_agent_execution_quality_throughput_metrics(session_id="fix-190-stack")
    report = result.agent_execution_quality_throughput_metrics
    assert report["execution_receipt_count"] == len(METRIC_AGENT_ROLE_IDS)
    assert report["package_completion_rate_percent"] == 100.0
    assert float(report["throughput_score"] or 0) > 0
    sections = report["sections"]
    assert sections["per_agent_execution_receipts"]
    assert sections["end_to_end_throughput_score"]


def test_chat_route_show_agent_execution_metrics():
    _participation_stack("fix-190-chat")
    _seed_fix_189_receipts("fix-190-chat")
    turn = resolve_chat_turn("show agent execution metrics", session_id="fix-190-chat")
    assert turn.intent == "mission_control_agent_execution_quality_throughput_metrics"
    assert (turn.meta or {}).get("route_id") == AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID


def test_agent_execution_metrics_api():
    _participation_stack("fix-190-api")
    _seed_fix_189_receipts("fix-190-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/agent-execution-quality-throughput-metrics",
        params={"session_id": "fix-190-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["agent_metrics_grant_authority"] is False
    assert payload["metrics_compose_receipts_only"] is True
    assert payload["agent_execution_quality_throughput_metrics"]["package_completion_rate_percent"] == 100.0
