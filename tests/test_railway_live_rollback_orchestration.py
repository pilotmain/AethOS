# SPDX-License-Identifier: Apache-2.0
"""FIX 115 — governed live rollback orchestration."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    ROLLBACK_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch import (
    run_live_rollback_orchestration,
    run_single_live_rollback_phase,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
    run_real_disconnect_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure import (
    run_real_revert_env_configure_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_MUTATION_SUCCESS,
    STATUS_ROLLBACK_SIMULATED_SKIPPED,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    list_rollback_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.execution_rollback_contract_models import (
    CONNECT_SOURCE_ROLLBACK_PHASE,
    DISABLE_DEPLOYS_ROLLBACK_PHASE,
    REMOVE_SERVICE_ROLLBACK_PHASE,
    REVERT_ENV_ROLLBACK_PHASE,
)
from aethos_core.providers.railway.execution_contract.execution_rollback_readiness import (
    assess_railway_rollback_readiness,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.execution_contract.rollback_audit_renderer import (
    build_rollback_isolation_audit,
)
from aethos_core.providers.railway.execution_contract.execution_renderer import (
    render_rollback_timeline,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
)

_SECRET = "super_secret_railway_token_abcdefghijklmnop"


@pytest.fixture(autouse=True)
def _clean():
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()


def _plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }


def _journal_forward_live() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-rb-115",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
            "env_configure_groups": {
                "minimum_secrets": {
                    "recorded": True,
                    "env_names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
                }
            },
        }
    )
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="bound",
    )
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase="configure_env",
        status="mutation_success",
        mutation_performed=True,
        detail="configured",
        receipt_group="minimum_secrets",
        env_var_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    return journal


def _enable_rollback_env(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_REVERT_ENV_ENABLED", "true")
    get_settings.cache_clear()


def test_rollback_readiness_gating():
    readiness = assess_railway_rollback_readiness(
        plan=_plan(),
        journal=_journal_forward_live(),
        execution_id="exec-rb-115",
        user_text="check railway rollback readiness",
    )
    assert readiness.ready_for_live_rollback is False
    assert "rollback_phrase_required" in readiness.blockers


def test_rollback_readiness_passes_with_phrase(monkeypatch):
    _enable_rollback_env(monkeypatch)
    readiness = assess_railway_rollback_readiness(
        plan=_plan(),
        journal=_journal_forward_live(),
        execution_id="exec-rb-115",
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert readiness.staging_only is True
    assert readiness.live_forward_execution_exists is True
    assert readiness.rollback_contract_present is True
    assert readiness.production_target is False
    assert "disconnect_repo_source" in readiness.phases_available
    assert "revert_env_writes" in readiness.phases_available


def test_production_rollback_hard_block():
    journal = _journal_forward_live()
    plan = {**_plan(), "environment": "production"}
    result = run_real_disconnect_connect_source_rollback(
        journal=journal,
        plan=plan,
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.policy_blocked is True
    readiness = assess_railway_rollback_readiness(
        plan=plan,
        journal=journal,
        execution_id="exec-rb-115",
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert readiness.production_target is True
    assert readiness.ready_for_live_rollback is False


@patch(
    "aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter.disconnect_github_source"
)
def test_disconnect_source_rollback_success(mock_disconnect, monkeypatch):
    from aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter import (
        DisconnectGithubSourceResult,
    )

    mock_disconnect.return_value = DisconnectGithubSourceResult(
        ok=True,
        mutation_performed=True,
        detail="disconnected",
    )
    _enable_rollback_env(monkeypatch)
    policy = assess_railway_execution_enablement_policy(plan=_plan(), user_text=ROLLBACK_FINAL_PHRASE)
    result = run_real_disconnect_connect_source_rollback(
        journal=_journal_forward_live(),
        plan=_plan(),
        policy=policy,
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.mutation_performed is True
    receipt = find_phase_receipt(execution_id="exec-rb-115", phase=CONNECT_SOURCE_ROLLBACK_PHASE)
    assert receipt is not None
    assert receipt["status"] == STATUS_ROLLBACK_MUTATION_SUCCESS
    assert _SECRET not in str(receipt)


@patch(
    "aethos_core.providers.railway.greenfield_adapters.revert_env_configure_adapter.revert_env_writes"
)
def test_env_rollback_success(mock_revert, monkeypatch):
    from aethos_core.providers.railway.greenfield_adapters.revert_env_configure_adapter import (
        RevertEnvConfigureResult,
    )

    mock_revert.return_value = RevertEnvConfigureResult(
        ok=True,
        mutation_performed=True,
        env_names_reverted=("ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"),
        detail="reverted names only",
    )
    _enable_rollback_env(monkeypatch)
    journal = _journal_forward_live()
    journal["connect_source_rollback_performed"] = True
    journal["github_source_disconnected"] = True
    policy = assess_railway_execution_enablement_policy(plan=_plan(), user_text=ROLLBACK_FINAL_PHRASE)
    result = run_real_revert_env_configure_rollback(
        journal=journal,
        plan=_plan(),
        policy=policy,
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.mutation_performed is True
    receipt = find_phase_receipt(execution_id="exec-rb-115", phase=REVERT_ENV_ROLLBACK_PHASE)
    assert receipt is not None
    assert receipt.get("env_var_names") == ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"]
    assert _SECRET not in str(receipt)


def test_rollback_idempotent_replay(monkeypatch):
    _enable_rollback_env(monkeypatch)
    journal = _journal_forward_live()
    journal["connect_source_rollback_performed"] = True
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase=CONNECT_SOURCE_ROLLBACK_PHASE,
        status=STATUS_ROLLBACK_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="prior",
    )
    policy = assess_railway_execution_enablement_policy(plan=_plan(), user_text=ROLLBACK_FINAL_PHRASE)
    result = run_real_disconnect_connect_source_rollback(
        journal=journal,
        plan=_plan(),
        policy=policy,
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.idempotent_replay is True
    assert result.mutation_performed is False


@patch(
    "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch.run_real_disconnect_connect_source_rollback"
)
def test_rollback_partial_failure_on_disconnect(mock_disconnect, monkeypatch):
    from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
        RealConnectSourceRollbackResult,
    )

    mock_disconnect.return_value = RealConnectSourceRollbackResult(
        journal=_journal_forward_live(),
        detail="failed",
        errors=["disconnect_failed"],
    )
    _enable_rollback_env(monkeypatch)
    result = run_single_live_rollback_phase(
        journal=_journal_forward_live(),
        plan=_plan(),
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.partial_failure is True


def test_rollback_timeline_rendering():
    journal = _journal_forward_live()
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase=CONNECT_SOURCE_ROLLBACK_PHASE,
        status=STATUS_ROLLBACK_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="ok",
    )
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase=REVERT_ENV_ROLLBACK_PHASE,
        status=STATUS_ROLLBACK_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="ok",
    )
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase=DISABLE_DEPLOYS_ROLLBACK_PHASE,
        status=STATUS_ROLLBACK_SIMULATED_SKIPPED,
        mutation_performed=False,
        detail="simulated",
    )
    record_execution_receipt(
        execution_id="exec-rb-115",
        phase=REMOVE_SERVICE_ROLLBACK_PHASE,
        status=STATUS_ROLLBACK_SIMULATED_SKIPPED,
        mutation_performed=False,
        detail="simulated",
    )
    body = render_rollback_timeline(journal, receipts=list_rollback_receipts(execution_id="exec-rb-115"))
    assert "rollback_mutation_success" in body
    assert "rollback_simulated_skipped" in body
    assert _SECRET not in body


def test_rollback_audit_isolation():
    audit = build_rollback_isolation_audit(execution_id="exec-rb-115")
    assert audit.rollback_executor_does_not_import_forward_executor is True
    assert audit.rollback_env_adapter_has_no_deploy_trigger is True
    assert audit.rollback_idempotency_enforced is True
    assert audit.rollback_respects_kill_switch is True
    assert audit.rollback_staging_only_enforced is True


def test_kill_switch_blocks_rollback(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_MUTATION_KILL_SWITCH", "true")
    get_settings.cache_clear()
    assert is_railway_mutation_kill_switch_active() is True
    policy = assess_railway_execution_enablement_policy(plan=_plan(), user_text=ROLLBACK_FINAL_PHRASE)
    assert policy.allows_disconnect_source_rollback() is False
    assert policy.allows_revert_env_rollback() is False


def test_dispatch_does_not_import_forward_executor():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "execution_real_mutation_dispatch" not in source
    assert "run_single_real_mutation_phase" not in source


def test_env_executor_does_not_import_forward_executor():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "trigger_railway_deploy" not in source
    assert "execution_real_mutation_dispatch" not in source


@patch(
    "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch.run_real_disconnect_connect_source_rollback"
)
@patch(
    "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch.run_real_revert_env_configure_rollback"
)
@patch(
    "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch.verify_rollback_env_readonly"
)
@patch(
    "aethos_core.providers.railway.execution_contract.execution_live_rollback_dispatch.verify_source_binding_readonly"
)
def test_orchestration_records_simulated_phases(
    mock_binding,
    mock_env_verify,
    mock_revert,
    mock_disconnect,
    monkeypatch,
):
    from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
        RealConnectSourceRollbackResult,
    )
    from aethos_core.providers.railway.execution_contract.execution_real_rollback_env_configure import (
        RealEnvRollbackResult,
    )
    from aethos_core.providers.railway.execution_contract.rollback_env_verification import (
        RollbackEnvVerification,
    )
    from aethos_core.providers.railway.execution_contract.source_binding_verification import (
        SourceBindingVerification,
    )

    journal = _journal_forward_live()

    def _disconnect_side(*, journal, **kwargs):
        updated = dict(journal)
        updated["github_source_disconnected"] = True
        updated["connect_source_rollback_performed"] = True
        record_execution_receipt(
            execution_id="exec-rb-115",
            phase=CONNECT_SOURCE_ROLLBACK_PHASE,
            status=STATUS_ROLLBACK_MUTATION_SUCCESS,
            mutation_performed=True,
            detail="disconnected",
        )
        return RealConnectSourceRollbackResult(journal=updated, mutation_performed=True)

    def _revert_side(*, journal, **kwargs):
        updated = dict(journal)
        updated["env_configure_rollback_performed"] = True
        record_execution_receipt(
            execution_id="exec-rb-115",
            phase=REVERT_ENV_ROLLBACK_PHASE,
            status=STATUS_ROLLBACK_MUTATION_SUCCESS,
            mutation_performed=True,
            detail="reverted",
        )
        return RealEnvRollbackResult(journal=updated, mutation_performed=True)

    mock_disconnect.side_effect = _disconnect_side
    mock_revert.side_effect = _revert_side
    mock_binding.return_value = SourceBindingVerification(ok=True, verified=True, detail="ok")
    mock_env_verify.return_value = RollbackEnvVerification(ok=True, verified=True, detail="ok")
    _enable_rollback_env(monkeypatch)
    result = run_live_rollback_orchestration(
        journal=journal,
        plan=_plan(),
        user_text=ROLLBACK_FINAL_PHRASE,
    )
    assert result.rollback_completed is True
    assert find_phase_receipt(execution_id="exec-rb-115", phase=DISABLE_DEPLOYS_ROLLBACK_PHASE) is not None
    assert find_phase_receipt(execution_id="exec-rb-115", phase=REMOVE_SERVICE_ROLLBACK_PHASE) is not None


def test_router_rollback_readiness_route():
    routed = route_railway_execution_contract(
        f"check railway rollback readiness\n{ROLLBACK_FINAL_PHRASE}",
        session_id="rb-115",
    )
    assert routed is not None
    assert routed[1] == "railway_rollback_readiness"
