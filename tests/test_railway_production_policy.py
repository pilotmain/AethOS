# SPDX-License-Identifier: Apache-2.0
"""FIX 117 — production policy hardening layer."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.production_confirmation_store import (
    clear_for_tests,
    quorum_counts,
    record_confirmation,
)
from aethos_core.providers.railway.execution_contract.production_policy import (
    PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
    assess_railway_production_policy,
    forward_live_mutation_blocked_reason,
    is_deployment_freeze_active,
    is_railway_production_policy_intent,
    load_railway_production_policy_config,
    record_production_confirmations_from_text,
    resolve_environment_tier,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()


def _prod_plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "production",
        "service_name": "api",
        "branch": "main",
    }


def test_production_policy_intent():
    assert is_railway_production_policy_intent("show railway production policy")


def test_forward_live_locked_by_default(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_PRODUCTION_FORWARD_LIVE_UNLOCKED", "false")
    get_settings.cache_clear()
    assessment = assess_railway_production_policy(
        plan=_prod_plan(),
        user_text=PRODUCTION_FINAL_PHRASE,
    )
    assert assessment.environment_tier == "production"
    assert assessment.blast_radius == "platform"
    assert assessment.forward_live_permitted is False
    assert "production_forward_live_locked" in assessment.blockers
    assert assessment.rollback_permitted is False
    assert assessment.autonomous_rollback_blocked is True


def test_shadow_mode_blocks_enabled_production(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_PRODUCTION_SHADOW_MODE_REQUIRED", "true")
    get_settings.cache_clear()
    assessment = assess_railway_production_policy(plan=_prod_plan())
    assert assessment.rollout_mode == "shadow"
    assert "production_shadow_mode_required" in assessment.blockers


def test_incident_mode_freezes_deployments(monkeypatch):
    monkeypatch.setenv("RAILWAY_PRODUCTION_INCIDENT_MODE", "true")
    get_settings.cache_clear()
    assert is_deployment_freeze_active() is True
    assessment = assess_railway_production_policy(plan=_prod_plan())
    assert "production_incident_mode_active" in assessment.blockers


def test_deployment_freeze_window(monkeypatch):
    now = datetime(2026, 5, 26, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setenv("RAILWAY_PRODUCTION_DEPLOYMENT_FREEZE", "false")
    monkeypatch.setenv("RAILWAY_PRODUCTION_FREEZE_START_UTC", "2026-05-26T11:00:00Z")
    monkeypatch.setenv("RAILWAY_PRODUCTION_FREEZE_END_UTC", "2026-05-26T13:00:00Z")
    get_settings.cache_clear()
    assert is_deployment_freeze_active(now=now) is True


def test_operator_quorum_requires_two_phrases(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv("RAILWAY_PRODUCTION_REQUIRE_SECOND_CONFIRMATION", "true")
    monkeypatch.setenv("RAILWAY_PRODUCTION_OPERATOR_QUORUM", "2")
    get_settings.cache_clear()
    execution_id = "exec-quorum-117"
    assessment = assess_railway_production_policy(
        plan=_prod_plan(),
        user_text=PRODUCTION_FINAL_PHRASE,
        execution_id=execution_id,
    )
    assert assessment.operator_quorum_satisfied is False
    record_production_confirmations_from_text(
        execution_id=execution_id,
        user_text=PRODUCTION_QUORUM_CONFIRMATION_PHRASE,
    )
    assessment2 = assess_railway_production_policy(
        plan=_prod_plan(),
        execution_id=execution_id,
    )
    assert assessment2.operator_quorum_satisfied is True
    assert quorum_counts(execution_id=execution_id)["total_distinct"] == 2


def test_enablement_merges_production_blockers(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    get_settings.cache_clear()
    policy = assess_railway_execution_enablement_policy(plan=_prod_plan(), user_text="")
    assert policy.is_production is True
    assert "production_forward_live_locked" in policy.blocking_reasons
    assert policy.allows_real_mutation() is False


def test_staging_tier_allows_forward_policy():
    assessment = assess_railway_production_policy(
        plan={"repo": "o/r", "environment": "staging", "project": "p"},
    )
    assert resolve_environment_tier("staging") == "staging"
    assert assessment.forward_live_permitted is True
    assert assessment.blockers == []


def test_forward_block_reason_for_production(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_ALLOW_PRODUCTION", "true")
    get_settings.cache_clear()
    reason = forward_live_mutation_blocked_reason(
        environment="production",
        phase="create_service",
        plan=_prod_plan(),
    )
    assert reason == "production_forward_live_locked"


def test_show_production_policy_route():
    routed = route_railway_execution_contract(
        "show railway production policy",
        session_id="prod-policy-route",
    )
    assert routed is not None
    body, route_name, meta = routed
    assert route_name == "railway_production_policy"
    assert meta["execution_contract_stage"] == "production_policy"
    assert "# Railway Production Policy" in body
    assert "forward live permitted" in body.lower()


def test_audit_retention_default():
    cfg = load_railway_production_policy_config()
    assert cfg.audit_retention_days >= 90
