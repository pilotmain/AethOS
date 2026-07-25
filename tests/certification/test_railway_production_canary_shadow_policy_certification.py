# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_store import (
    clear_for_tests as clear_policy,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    clear_for_tests as clear_rollout_journal,
)
from aethos_core.providers.railway.execution_contract.production_rollout_receipts import (
    clear_for_tests as clear_rollout_receipts,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_railway_production_rollout_orchestration_certification import (
    SESSION,
    TestProductionRolloutOrchestrationCertification,
)

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_policy()
    clear_rollout_journal()
    clear_rollout_receipts()
    get_settings.cache_clear()
    yield
    clear_policy()
    clear_rollout_journal()
    clear_rollout_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestProductionCanaryShadowPolicyCertification:
    def test_policy_governed_rollout_with_synthetic_traffic(self, monkeypatch) -> None:
        TestProductionRolloutOrchestrationCertification().test_governed_rollout_sequence_after_verification(
            monkeypatch
        )

        policy = resolve_chat_turn(
            "show railway production canary shadow policy",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(policy, route_id="railway_production_canary_shadow_policy")
        assert "shadow_only" in policy.reply or "canary_governed" in policy.reply

        shadow_traffic = resolve_chat_turn(
            "show railway production shadow traffic policy",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(shadow_traffic, route_id="railway_production_canary_shadow_policy")
        assert "0" in shadow_traffic.reply

        synthetic = resolve_chat_turn(
            f"record railway production synthetic verification traffic\n{SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE}",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(synthetic, route_id="railway_production_canary_shadow_policy")

        percent = resolve_chat_turn(
            "show railway production rollout percentage governance",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(percent, route_id="railway_production_canary_shadow_policy")

        segmentation = resolve_chat_turn(
            "show railway production traffic segmentation",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(segmentation, route_id="railway_production_canary_shadow_policy")
        assert "synthetic_verification" in segmentation.reply

        health = resolve_chat_turn(
            "show railway production canary health evidence",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(health, route_id="railway_production_canary_shadow_policy")

        rollback_rec = resolve_chat_turn(
            "show railway production canary rollback recommendation",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(rollback_rec, route_id="railway_production_canary_shadow_policy")
