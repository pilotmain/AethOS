# SPDX-License-Identifier: Apache-2.0
"""FIX 119 — production verification certification (fixtures only)."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    get_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    bind_session_execution,
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    get_or_create_execution_journal,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    load_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    clear_for_tests as clear_verification_receipts,
    load_verification_receipt,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_railway_production_shadow_certification import (
    _production_plan_mocks,
)

pytestmark = pytest.mark.certification

SESSION = "prod-verification-cert-v1"


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_verification_receipts()
    get_settings.cache_clear()
    yield
    clear_verification_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


def _bootstrap_production_plan(monkeypatch, session: str) -> None:
    with _production_plan_mocks(monkeypatch):
        for cmd in (
            "run railway deployment readiness for pilotmain/aethos",
            "create railway deployment plan for pilotmain/aethos in pilotos / production",
            "complete the railway deployment plan",
            "confirm railway deployment plan",
            "create railway service creation preflight",
            "approve railway service creation preflight",
            "simulate railway service creation",
        ):
            resolve_chat_turn(cmd, session_id=session, apply_relational_layer=False)

        from aethos_core.providers.railway.service_creation_simulator.simulator_context import (
            get_simulation,
            save_simulation,
        )

        snap = get_simulation(session_id=session)
        assert snap is not None
        snap["ready_to_execute"] = True
        snap["blocking_reasons"] = []
        snap["blocking_reason_messages"] = []
        save_simulation(session_id=session, simulation=snap)
        get_settings.cache_clear()

        plan_ctx = get_deployment_plan_context(session_id=session) or {}
        journal, _ = get_or_create_execution_journal(
            plan=plan_ctx,
            session_id=session,
            initial_state="simulation_complete",
            approval={},
        )
        bind_session_execution(session_id=session, execution_id=str(journal["execution_id"]))


class TestProductionVerificationCertification:
    def test_verification_evidence_after_shadow_forward(self, monkeypatch) -> None:
        _bootstrap_production_plan(monkeypatch, SESSION)
        phrase = f"{PRODUCTION_FINAL_PHRASE}\n{PRODUCTION_QUORUM_CONFIRMATION_PHRASE}"

        forward = resolve_chat_turn(
            f"simulate production railway deployment\n{phrase}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(forward, route_id="railway_production_shadow")
        assert forward.intent == "railway_production_shadow_forward"

        plan_ctx = get_deployment_plan_context(session_id=SESSION) or {}
        execution_id = resolve_execution_id_for_plan(session_id=SESSION, plan=plan_ctx) or ""
        assert execution_id
        assert load_shadow_journal(execution_id=execution_id) is not None

        evidence = resolve_chat_turn(
            "show railway production verification evidence",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(evidence, route_id="railway_production_verification")
        assert evidence.meta.get("verification_passed") == "true"
        assert "strong_signals" in evidence.reply.lower()

        receipt = load_verification_receipt(execution_id=execution_id)
        assert receipt is not None
        assert receipt.get("schema_version") == "production_verification_v1"
        assert receipt.get("mutation_performed") is False

        rollback_rec = resolve_chat_turn(
            "show railway production rollback recommendation",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(rollback_rec, route_id="railway_production_verification")
        assert "rollback_recommendation" in rollback_rec.reply.lower()
