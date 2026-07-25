# SPDX-License-Identifier: Apache-2.0
"""FIX 143 — meta-governance insights (read-only)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_insights.governance_insights_intent import is_governance_insights_intent
from aethos_core.mission_control.governance_insights.governance_insights_service import build_governance_insights
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    clear_operational_memory_records_for_tests,
)
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    get_settings.cache_clear()


def test_governance_insights_intent():
    assert is_governance_insights_intent("show governance insights")
    assert is_governance_insights_intent("meta-governance health")
    assert not is_governance_insights_intent("auto-tune policy now")


def test_governance_insights_api_readonly():
    session = "mc-gov-insights-143"
    _full_stack(session)
    client = TestClient(app)
    res = client.get("/api/v1/mission-control/governance-insights", params={"session_id": session, "format": "both"})
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["policy_auto_tuning_enabled"] is False
    assert body["governance_self_modification_enabled"] is False
    insights = body["insights"]
    assert insights["schema_version"] == "mission_control_governance_insights_v1"
    sections = insights["insights"]
    assert "governance_health_metrics" in sections
    assert "operator_workload_heatmap" in sections
    assert all(r.get("executable") is False for r in insights.get("recommendations") or [])
    assert "Adaptive Governance Insights" in body["markdown"]


def test_governance_insights_chat_route():
    session = "mc-gov-insights-chat-143"
    _full_stack(session)
    result = resolve_chat_turn("show governance insights", session_id=session, apply_relational_layer=False)
    assert result.meta.get("route_id") == "mission_control_governance_insights"
    assert result.meta.get("mutation_performed") == "false"
    assert "Adaptive Governance Insights" in result.reply


def test_governance_insights_meta_sections():
    session = "mc-gov-insights-meta-143"
    _full_stack(session)
    result = build_governance_insights(session_id=session)
    assert result.ok is True
    assert result.insights.get("insight_count", 0) >= 0
    assert result.insights["policy_auto_tuning_enabled"] is False
