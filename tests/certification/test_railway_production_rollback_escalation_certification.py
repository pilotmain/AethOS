# SPDX-License-Identifier: Apache-2.0
"""FIX 120 — production rollback escalation certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_contract import (
    INCIDENT_COMMANDER_ACK_PHRASE,
    PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_rollback_escalation_store import (
    clear_for_tests as clear_escalation,
    load_escalation,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_railway_production_verification_certification import (
    SESSION,
    TestProductionVerificationCertification,
    _bootstrap_production_plan,
)

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_escalation()
    get_settings.cache_clear()
    yield
    clear_escalation()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestProductionRollbackEscalationCertification:
    def test_escalation_and_shadow_rollback_rehearsal(self, monkeypatch) -> None:
        _bootstrap_production_plan(monkeypatch, SESSION)
        TestProductionVerificationCertification().test_verification_evidence_after_shadow_forward(
            monkeypatch
        )

        from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
            get_deployment_plan_context,
        )
        from aethos_core.providers.railway.execution_contract.execution_context import (
            resolve_execution_id_for_plan,
        )

        plan_ctx = get_deployment_plan_context(session_id=SESSION) or {}
        execution_id = resolve_execution_id_for_plan(session_id=SESSION, plan=plan_ctx) or ""

        ack = resolve_chat_turn(
            f"acknowledge production rollback escalation\n{INCIDENT_COMMANDER_ACK_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(ack, route_id="railway_production_rollback_escalation")

        quorum = resolve_chat_turn(
            f"show railway production rollback rehearsal quorum\n{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(quorum, route_id="railway_production_rollback_escalation")

        record_human = resolve_chat_turn(
            "record production rollback decision shadow_rehearsal_authorized",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(record_human, route_id="railway_production_rollback_escalation")

        rollback = resolve_chat_turn(
            f"simulate production railway rollback\n{PRODUCTION_ROLLBACK_REHEARSAL_QUORUM_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(rollback, route_id="railway_production_shadow")
        assert rollback.intent == "railway_production_shadow_rollback"

        ticket = load_escalation(execution_id=execution_id)
        assert ticket is not None
        assert ticket.get("decision_state") == "shadow_rehearsal_completed"
        assert ticket.get("autonomous_rollback_permitted") is False

        audit = resolve_chat_turn(
            "show railway production rollback audit trail",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(audit, route_id="railway_production_rollback_escalation")
        assert "shadow_rehearsal_completed" in audit.reply
