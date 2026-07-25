# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — production rollout orchestration certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    get_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    clear_for_tests as clear_rollout_journal,
    load_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    ROLLOUT_ADVANCE_APPROVAL_PHRASE,
    ROLLOUT_STAGES,
)
from aethos_core.providers.railway.execution_contract.production_rollout_receipts import (
    clear_for_tests as clear_rollout_receipts,
    list_rollout_receipts,
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
    clear_rollout_journal()
    clear_rollout_receipts()
    get_settings.cache_clear()
    yield
    clear_rollout_journal()
    clear_rollout_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestProductionRolloutOrchestrationCertification:
    def test_governed_rollout_sequence_after_verification(self, monkeypatch) -> None:
        _bootstrap_production_plan(monkeypatch, SESSION)
        TestProductionVerificationCertification().test_verification_evidence_after_shadow_forward(
            monkeypatch
        )

        plan_ctx = get_deployment_plan_context(session_id=SESSION) or {}
        execution_id = resolve_execution_id_for_plan(session_id=SESSION, plan=plan_ctx) or ""

        resolve_chat_turn(
            "record production rollback decision escalation_closed",
            session_id=SESSION,
            apply_relational_layer=False,
        )

        status = resolve_chat_turn(
            "show railway production rollout status",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(status, route_id="railway_production_rollout")
        assert status.intent == "railway_production_rollout_status"

        resolve_chat_turn(
            f"record railway production synthetic verification traffic\n{SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )

        advance_phrase = (
            f"advance railway production rollout\n{ROLLOUT_ADVANCE_APPROVAL_PHRASE}"
        )
        for _ in ROLLOUT_STAGES:
            advance = resolve_chat_turn(
                advance_phrase,
                session_id=SESSION,
                apply_relational_layer=False,
            )
            assert_route_owns(advance, route_id="railway_production_rollout")
            assert advance.intent == "railway_production_rollout_advance"

        journal = load_rollout_journal(execution_id=execution_id)
        assert journal is not None
        assert journal.get("orchestration_state") == "completed"
        assert journal.get("autonomous_promotion_permitted") is False

        receipts = list_rollout_receipts(execution_id=execution_id)
        assert len(receipts) >= len(ROLLOUT_STAGES)
        assert all(r.get("mutation_performed") is False for r in receipts)

        timeline = resolve_chat_turn(
            "show railway production rollout timeline",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(timeline, route_id="railway_production_rollout")
        assert timeline.intent == "railway_production_rollout_timeline"

        checkpoint = resolve_chat_turn(
            "show railway production rollout health checkpoint",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(checkpoint, route_id="railway_production_rollout")
        assert "shadow_forward_complete" in checkpoint.reply
