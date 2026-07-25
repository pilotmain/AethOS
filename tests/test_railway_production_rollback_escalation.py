# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation framework."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
    INCIDENT_COMMANDER_ACK_PHRASE,
    PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
    acknowledge_incident_commander,
    assess_rollback_escalation_gate,
    create_or_refresh_escalation_from_verification,
    is_production_rollback_escalation_intent,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
    clear_for_tests,
    load_escalation,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    clear_for_tests as clear_verification_receipts,
    save_verification_receipt,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_for_tests()
    clear_verification_receipts()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_verification_receipts()
    get_settings.cache_clear()


def _failed_verification_receipt(execution_id: str) -> None:
    save_verification_receipt(
        {
            "execution_id": execution_id,
            "phase": "production_runtime_verification",
            "status": "verification_failed",
            "evidence": {"signals": [{"signal_id": "slo_availability_budget_met", "passed": False}]},
            "assessment": {
                "verification_passed": False,
                "rollback_recommendation": "advise_manual_review",
                "incident_escalation": "operator_review",
                "strong_signal_count": 0,
                "families_present": [],
            },
        }
    )


def test_escalation_intents():
    assert is_production_rollback_escalation_intent("show railway production rollback escalation")
    assert is_production_rollback_escalation_intent("show railway production rollback audit trail")


def test_escalation_ticket_from_verification():
    execution_id = "exec-esc-120"
    _failed_verification_receipt(execution_id)
    record = create_or_refresh_escalation_from_verification(execution_id=execution_id)
    assert record["autonomous_rollback_permitted"] is False
    assert record["rollback_recommendation"] == "advise_manual_review"
    assert record["evidence_bundle"]
    assert len(record.get("audit_trail") or []) >= 1


def test_shadow_rehearsal_requires_quorum_and_incident_commander():
    execution_id = "exec-esc-gate"
    _failed_verification_receipt(execution_id)
    create_or_refresh_escalation_from_verification(execution_id=execution_id)
    gate = assess_rollback_escalation_gate(execution_id=execution_id)
    assert gate.ready_for_shadow_rehearsal is False
    assert "incident_commander_ack_required" in gate.blockers

    acknowledge_incident_commander(
        execution_id=execution_id,
        user_text=INCIDENT_COMMANDER_ACK_PHRASE,
    )
    gate2 = assess_rollback_escalation_gate(
        execution_id=execution_id,
        user_text=PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
    )
    assert gate2.incident_commander_acknowledged is True
    assert gate2.rollback_rehearsal_quorum_satisfied is True
    assert gate2.ready_for_shadow_rehearsal is True
    assert gate2.autonomous_rollback_permitted is False


def test_human_decision_authorizes_rehearsal_without_recommendation():
    execution_id = "exec-esc-auth"
    save_verification_receipt(
        {
            "execution_id": execution_id,
            "assessment": {
                "verification_passed": True,
                "rollback_recommendation": "none",
                "incident_escalation": "none",
            },
            "evidence": {},
        }
    )
    from aethos_core.providers.railway.execution_contract.production_rollback_escalation import (
        record_human_rollback_decision,
    )

    record_human_rollback_decision(
        execution_id=execution_id,
        decision_state="shadow_rehearsal_authorized",
    )
    gate = assess_rollback_escalation_gate(execution_id=execution_id)
    assert gate.ready_for_shadow_rehearsal is True
    record = load_escalation(execution_id=execution_id)
    assert record is not None
    assert record["decision_state"] == "shadow_rehearsal_authorized"
