# SPDX-License-Identifier: Apache-2.0
"""FIX 116 — Phase 1 Railway staging lifecycle certification freeze."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    get_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.execution_context import (
    clear_for_tests as clear_execution_context,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    ROLLBACK_FINAL_PHRASE,
    is_rollback_blocked_environment,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.execution_rollback_readiness import (
    assess_railway_rollback_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.railway_phase_1_contract import (
    PHASE_1_FORWARD_APPROVAL_PHRASE,
    PHASE_1_FORWARD_LIVE_ORDER,
    PHASE_1_ROLLBACK_APPROVAL_PHRASE,
    PHASE_1_ROLLBACK_LIVE_ACTIONS,
    PHASE_1_ROLLBACK_SIMULATED_ACTIONS,
)
from aethos_core.providers.railway.execution_contract.rollback_audit_renderer import (
    build_rollback_isolation_audit,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_aethos_stability_contract_v1 import _railway_dry_run_lifecycle_mocks

pytestmark = pytest.mark.certification


@pytest.fixture(autouse=True)
def _phase1_clean():
    reset_certification_runtime()
    clear_journal()
    clear_receipts()
    clear_execution_context()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_receipts()
    clear_execution_context()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestRailwayPhase1FrozenContract:
    def test_forward_and_rollback_order_frozen(self) -> None:
        assert PHASE_1_FORWARD_LIVE_ORDER == (
            "create_service",
            "connect_source",
            "configure_env",
            "trigger_deploy",
            "verify_runtime",
        )
        assert PHASE_1_ROLLBACK_LIVE_ACTIONS == (
            "disconnect_repo_source",
            "revert_env_writes",
        )
        assert PHASE_1_ROLLBACK_SIMULATED_ACTIONS == (
            "disable_deploys",
            "remove_created_service",
        )

    def test_approval_phrases_exact(self) -> None:
        assert PHASE_1_FORWARD_APPROVAL_PHRASE == "Execute governed Railway deployment."
        assert (
            PHASE_1_ROLLBACK_APPROVAL_PHRASE
            == "I understand this will rollback staging Railway mutations. Execute governed rollback."
        )

    def test_production_environments_blocked_for_rollback(self) -> None:
        for env in ("production", "prod", "live"):
            assert is_rollback_blocked_environment(env) is True
        assert is_rollback_blocked_environment("staging") is False

    def test_rollback_isolation_audit_passes(self) -> None:
        audit = build_rollback_isolation_audit(execution_id="phase1-cert-audit")
        assert audit.ok is True


class TestRailwayPhase1StagingLifecycleCertification:
    """Full forward dry-run + rollback diagnostics — fixtures only."""

    def test_phase1_forward_and_rollback_prompt_chain(self, monkeypatch) -> None:
        session = "phase1-railway-cert"
        with _railway_dry_run_lifecycle_mocks(monkeypatch):
            resolve_chat_turn(
                "run railway deployment readiness for pilotmain/aethos",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "create railway deployment plan for pilotmain/aethos in pilotos / staging",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "complete the railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "confirm railway deployment plan",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "create railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            resolve_chat_turn(
                "approve railway service creation preflight",
                session_id=session,
                apply_relational_layer=False,
            )
            sim = resolve_chat_turn(
                "simulate railway service creation",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(sim, route_id="railway_service_creation_simulator")
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

            gate = resolve_chat_turn(
                "check railway execution readiness",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(gate, route_id="railway_execution_contract")
            assert gate.intent == "railway_execution_readiness_gate"

            execute = resolve_chat_turn(
                "execute railway service creation",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(execute, route_id="railway_execution_contract")
            assert execute.meta.get("mutation_performed") == "false"

            plan_ctx = get_deployment_plan_context(session_id=session) or {}
            execution_id = resolve_execution_id_for_plan(session_id=session, plan=plan_ctx)
            assert execution_id
            forward_receipts = list_execution_receipts(execution_id=execution_id)
            assert forward_receipts
            assert all(r.get("mutation_performed") is False for r in forward_receipts)

            rollback_readiness = resolve_chat_turn(
                "check railway rollback readiness",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(rollback_readiness, route_id="railway_execution_contract")
            assert rollback_readiness.meta.get("execution_contract_stage") == "rollback_readiness"

            contract = resolve_chat_turn(
                "show railway rollback contract",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(contract, route_id="railway_execution_contract")

            timeline = resolve_chat_turn(
                "show railway rollback timeline",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(timeline, route_id="railway_execution_contract")
            assert timeline.intent == "railway_execution_rollback_timeline"

            receipts = resolve_chat_turn(
                "show railway rollback receipts",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(receipts, route_id="railway_execution_contract")
            assert receipts.intent == "railway_execution_rollback_receipts"

            audit = resolve_chat_turn(
                "show railway rollback audit",
                session_id=session,
                apply_relational_layer=False,
            )
            assert_route_owns(audit, route_id="railway_execution_contract")
            assert audit.meta.get("execution_contract_stage") == "rollback_audit"
            assert "audit_ok:" in audit.reply.lower()


class TestRailwayPhase1ProductionPolicyLayer:
    def test_production_policy_blocks_live_forward_by_default(self, monkeypatch) -> None:
        monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
        monkeypatch.setenv("RAILWAY_PRODUCTION_FORWARD_LIVE_UNLOCKED", "false")
        get_settings.cache_clear()
        from aethos_core.providers.railway.execution_contract.production_policy import (
            assess_railway_production_policy,
        )

        assessment = assess_railway_production_policy(
            plan={
                "repo": "pilotmain/aethos",
                "project": "pilotos",
                "environment": "production",
            },
        )
        assert assessment.forward_live_permitted is False
        assert "production_forward_live_locked" in assessment.blockers


class TestRailwayPhase1ProductionRollbackBlocked:
    def test_production_plan_blocks_live_rollback_even_with_phrase(self, monkeypatch) -> None:
        _enable_rollback_env(monkeypatch)
        plan = {
            "repo": "org/repo",
            "project": "pilotos",
            "environment": "production",
            "service_name": "api",
            "branch": "main",
        }
        journal = attach_rollback_journal(
            {
                "execution_id": "exec-phase1-prod-block",
                "railway_service_id": "svc-1",
                "github_source_bound": {"repository": "org/repo", "branch": "main"},
            }
        )
        readiness = assess_railway_rollback_readiness(
            plan=plan,
            journal=journal,
            execution_id="exec-phase1-prod-block",
            user_text=ROLLBACK_FINAL_PHRASE,
        )
        assert readiness.production_target is True
        assert readiness.ready_for_live_rollback is False
        assert "production_rollback_blocked" in readiness.blockers


def _enable_rollback_env(monkeypatch) -> None:
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_REVERT_ENV_ENABLED", "true")
    get_settings.cache_clear()
