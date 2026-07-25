# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
    assess_canary_shadow_deployment_policy,
    is_production_canary_shadow_policy_intent,
    policy_blockers_for_rollout_advance,
    record_synthetic_verification_traffic,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    AUTOMATIC_PROMOTION_PERMITTED,
    AUTOMATIC_TRAFFIC_MUTATION_PERMITTED,
    AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_store import (
    clear_for_tests,
)
from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    record_confirmation,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    clear_for_tests as clear_rollout_journal,
    get_or_create_rollout_journal,
    save_rollout_journal,
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
    clear_for_tests()
    clear_rollout_journal()
    clear_shadow_journal()
    clear_verification()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_rollout_journal()
    clear_shadow_journal()
    clear_verification()
    get_settings.cache_clear()


def _seed(execution_id: str, *, stage: str = "canary") -> None:
    record_confirmation(execution_id=execution_id, kind="production_final_phrase")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    record_confirmation(execution_id=execution_id, kind="production_quorum_confirmation")
    sj, _ = get_or_create_shadow_journal(
        execution_id=execution_id,
        plan={"environment": "production"},
    )
    sj["forward_shadow_completed"] = True
    save_shadow_journal(sj)
    save_verification_receipt(
        {
            "execution_id": execution_id,
            "assessment": {"verification_passed": True},
            "evidence": {},
        }
    )
    rj, _ = get_or_create_rollout_journal(
        execution_id=execution_id,
        plan={"environment": "production"},
    )
    rj["current_stage"] = stage
    save_rollout_journal(rj)


def test_policy_intents():
    assert is_production_canary_shadow_policy_intent("show railway production canary shadow policy")
    assert is_production_canary_shadow_policy_intent("show railway production shadow traffic policy")


def test_prohibitions():
    assert AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED is False
    assert AUTOMATIC_TRAFFIC_MUTATION_PERMITTED is False
    assert AUTOMATIC_PROMOTION_PERMITTED is False


def test_shadow_vs_canary_strategy():
    _seed("exec-csp-shadow", stage="shadow")
    assessment = assess_canary_shadow_deployment_policy(
        execution_id="exec-csp-shadow",
        plan={"environment": "production"},
    )
    assert assessment.deployment_strategy == "shadow_only"
    assert assessment.governed_canary_percent == 0

    _seed("exec-csp-canary", stage="canary")
    record_synthetic_verification_traffic(
        execution_id="exec-csp-canary",
        user_text=f"record\n{SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE}",
    )
    assessment2 = assess_canary_shadow_deployment_policy(
        execution_id="exec-csp-canary",
        plan={"environment": "production"},
    )
    assert assessment2.deployment_strategy == "shadow_then_canary"
    assert assessment2.governed_canary_percent > 0


def test_policy_blocks_canary_advance_without_synthetic():
    _seed("exec-csp-block", stage="canary")
    blockers = policy_blockers_for_rollout_advance(
        execution_id="exec-csp-block",
        rollout_stage="canary",
    )
    assert "synthetic_verification_traffic_required" in blockers
