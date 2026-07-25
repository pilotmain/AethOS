# SPDX-License-Identifier: Apache-2.0
"""FIX 121 — production rollout orchestration."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    clear_for_tests as clear_rollout_journal,
    get_or_create_rollout_journal,
    load_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration import (
    advance_rollout_stage,
    build_rollout_status,
    is_production_rollout_orchestration_intent,
    pause_rollout,
    resume_rollout,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
    record_synthetic_verification_traffic,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    ROLLOUT_ADVANCE_APPROVAL_PHRASE,
    ROLLOUT_PAUSE_PHRASE,
    ROLLOUT_RESUME_PHRASE,
    ROLLOUT_STAGES,
)
from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    record_confirmation,
)
from aethos_core.providers.railway.execution_contract.production_rollout_receipts import (
    clear_for_tests as clear_rollout_receipts,
    list_rollout_receipts,
)
from aethos_core.providers.railway.execution_contract.production_shadow_journal import (
    clear_for_tests as clear_shadow_journal,
    get_or_create_shadow_journal,
    save_shadow_journal,
)
from aethos_core.providers.railway.execution_contract.production_verification_receipts import (
    clear_for_tests as clear_verification,
    save_verification_receipt,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_rollout_journal()
    clear_rollout_receipts()
    clear_shadow_journal()
    clear_verification()
    get_settings.cache_clear()
    yield
    clear_rollout_journal()
    clear_rollout_receipts()
    clear_shadow_journal()
    clear_verification()
    get_settings.cache_clear()


def _seed_prerequisites(execution_id: str) -> None:
    record_confirmation(execution_id=execution_id, kind="production_final_phrase")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    journal, _ = get_or_create_shadow_journal(
        execution_id=execution_id,
        plan={"environment": "production"},
        session_id="test",
    )
    journal["forward_shadow_completed"] = True
    save_shadow_journal(journal)
    save_verification_receipt(
        {
            "execution_id": execution_id,
            "assessment": {"verification_passed": True, "rollback_recommendation": "none"},
            "evidence": {"signals": []},
        }
    )


def test_rollout_intents():
    assert is_production_rollout_orchestration_intent("show railway production rollout status")
    assert is_production_rollout_orchestration_intent("advance railway production rollout")


def test_autonomous_promotion_prohibited():
    assert AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED is False


def test_advance_through_stages():
    execution_id = "exec-rollout-121"
    _seed_prerequisites(execution_id)
    phrase = f"advance railway production rollout\n{ROLLOUT_ADVANCE_APPROVAL_PHRASE}"
    record_synthetic_verification_traffic(
        execution_id=execution_id,
        user_text=f"record\n{SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE}",
    )

    for expected_stage in ROLLOUT_STAGES:
        journal, _ = get_or_create_rollout_journal(
            execution_id=execution_id,
            plan={"environment": "production"},
        )
        assert journal["current_stage"] == expected_stage
        result = advance_rollout_stage(
            execution_id=execution_id,
            user_text=phrase,
            plan={"environment": "production"},
        )
        assert result.success, result.blockers

    journal = load_rollout_journal(execution_id=execution_id)
    assert journal is not None
    assert journal["orchestration_state"] == "completed"
    assert len(journal.get("completed_stages") or []) == len(ROLLOUT_STAGES)
    receipts = list_rollout_receipts(execution_id=execution_id)
    assert len(receipts) >= len(ROLLOUT_STAGES)
    assert all(r.get("mutation_performed") is False for r in receipts)


def test_pause_and_resume():
    execution_id = "exec-rollout-pause"
    _seed_prerequisites(execution_id)
    paused = pause_rollout(
        execution_id=execution_id,
        user_text=f"pause railway production rollout\n{ROLLOUT_PAUSE_PHRASE}",
    )
    assert paused.success
    assert paused.journal["rollout_paused"] is True

    blocked = advance_rollout_stage(
        execution_id=execution_id,
        user_text=f"advance railway production rollout\n{ROLLOUT_ADVANCE_APPROVAL_PHRASE}",
    )
    assert not blocked.success
    assert "rollout_paused" in blocked.blockers

    resumed = resume_rollout(
        execution_id=execution_id,
        user_text=f"resume railway production rollout\n{ROLLOUT_RESUME_PHRASE}",
    )
    assert resumed.success
    status = build_rollout_status(execution_id=execution_id, plan={"environment": "production"})
    assert status["rollout_paused"] is False
