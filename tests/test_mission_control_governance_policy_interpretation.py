# SPDX-License-Identifier: Apache-2.0
"""FIX 152 — governance policy interpretation + precedent application."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.governance_collaboration.governance_collaboration_store import (
    clear_governance_collaboration_records_for_tests,
)
from aethos_core.mission_control.governance_deliberation.governance_deliberation_store import (
    clear_governance_deliberation_records_for_tests,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import (
    clear_governance_doctrine_records_for_tests,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_intent import (
    is_governance_policy_interpretation_intent,
    parse_interpretation_record_intent,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_service import (
    build_governance_policy_interpretation,
)
from aethos_core.mission_control.governance_policy_interpretation.governance_policy_interpretation_store import (
    clear_governance_policy_interpretation_records_for_tests,
)
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
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    clear_operational_memory_records_for_tests()
    clear_governance_deliberation_records_for_tests()
    clear_governance_collaboration_records_for_tests()
    clear_governance_doctrine_records_for_tests()
    clear_governance_policy_interpretation_records_for_tests()
    get_settings.cache_clear()


def test_governance_policy_interpretation_intent():
    assert is_governance_policy_interpretation_intent("show governance interpretation")
    assert is_governance_policy_interpretation_intent("precedent application")
    assert not is_governance_policy_interpretation_intent("automatic doctrine enforcement now")


def test_interpretation_record_intent_parse():
    parsed = parse_interpretation_record_intent(
        "interpretation doctrine: review delegation allowed does not imply execution authority delegation"
    )
    assert parsed == (
        "doctrine_interpretation",
        "review delegation allowed does not imply execution authority delegation",
    )


def test_governance_policy_interpretation_api_readonly():
    session = "mc-interpretation-152"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/governance-policy-interpretation",
        params={"session_id": session, "format": "both"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    assert body["automatic_doctrine_enforcement_enabled"] is False
    assert body["autonomous_governance_rulings_enabled"] is False
    interpretation = body["interpretation"]
    assert interpretation["schema_version"] == "mission_control_governance_policy_interpretation_v1"
    sections = interpretation["sections"]
    assert "doctrine_interpretation_records" in sections
    assert "constitutional_consistency_checks" in sections
    assert "precedent_confidence_scoring" in sections
    assert interpretation["all_interpretations_executable"] is False
    assert "Governance Policy Interpretation" in body["markdown"]


def test_governance_policy_interpretation_record_persists():
    session = "mc-interpretation-record-152"
    _full_stack(session)
    client = TestClient(app)
    post = client.post(
        "/api/v1/mission-control/governance-policy-interpretation/record",
        json={
            "session_id": session,
            "kind": "doctrine_interpretation",
            "content": "Hold precedent applies when incident exposure is elevated — advisory only.",
        },
    )
    assert post.status_code == 200
    body = post.json()
    assert body["ok"] is True
    assert body["executable"] is False
    assert body["interpretation_memory_only"] is True

    get_res = client.get(
        "/api/v1/mission-control/governance-policy-interpretation",
        params={"session_id": session},
    )
    records = get_res.json()["interpretation"]["sections"]["doctrine_interpretation_records"]
    assert len(records) == 1
    assert records[0]["executable"] is False


def test_governance_policy_interpretation_chat_view_and_record():
    session = "mc-interpretation-chat-152"
    _full_stack(session)
    record = resolve_chat_turn(
        "interpretation precedent: hold pattern when incident exposure elevated",
        session_id=session,
        apply_relational_layer=False,
    )
    assert record.meta.get("route_id") == "mission_control_governance_policy_interpretation"
    assert record.meta.get("automatic_doctrine_enforcement_enabled") == "false"
    assert "Interpretation assistance only" in record.reply

    view = resolve_chat_turn("governance policy interpretation", session_id=session, apply_relational_layer=False)
    assert view.meta.get("route_id") == "mission_control_governance_policy_interpretation"
    assert "Governance Policy Interpretation" in view.reply


def test_governance_policy_interpretation_builds_from_doctrine():
    session = "mc-interpretation-src-152"
    _full_stack(session)
    result = build_governance_policy_interpretation(session_id=session)
    assert result.ok is True
    assert result.interpretation["sources"]["governance_doctrine"] is True
    assert len(result.interpretation["interpretation_assistance_principles"]) >= 8
