# SPDX-License-Identifier: Apache-2.0
"""FIX 111 — live disconnect_repo_source rollback for connect_source."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
from aethos_core.providers.railway.execution_contract.connect_source_rollback_contract import (
    build_connect_source_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_dry_run_rollback_executor import (
    run_dry_run_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
    save_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor import (
    run_real_disconnect_connect_source_rollback,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_MUTATION_SUCCESS,
    STATUS_ROLLBACK_SIMULATED_SUCCESS,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter import (
    disconnect_github_source,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_plan()
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_plan()
    clear_journal()
    clear_receipts()
    get_settings.cache_clear()


def _journal_with_live_forward() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-live-rb",
            "state": "execution_phase_connect_source",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
        }
    )
    record_execution_receipt(
        execution_id="exec-live-rb",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="bound skipDeploys=true",
    )
    return journal


def test_live_rollback_contract_requires_forward_mutation_receipt():
    journal = _journal_with_live_forward()
    contract = build_connect_source_rollback_contract(journal=journal, execution_id="exec-live-rb")
    assert contract.forward_live_mutation_recorded is True
    assert contract.eligible_for_live_rollback is False  # flag off by default


def test_live_rollback_policy_blocked_when_disconnect_disabled():
    journal = _journal_with_live_forward()
    plan = {"repo": "org/repo", "environment": "staging", "branch": "main"}
    result = run_real_disconnect_connect_source_rollback(journal=journal, plan=plan)
    assert result.policy_blocked is True
    assert result.mutation_performed is False


def test_live_rollback_executor_does_not_import_dry_run():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_rollback_disconnect_executor"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "execution_dry_run_rollback_executor" not in source
    assert "run_dry_run_connect_source_rollback" not in source


def test_disconnect_adapter_requires_authorization():
    result = disconnect_github_source(
        environment_name="staging",
        environment_id="env-1",
        service_id="svc-1",
        repository="org/repo",
        branch="main",
        idempotency_key="k",
    )
    assert result.ok is False
    assert result.errors


def test_live_rollback_records_mutation_receipt():
    from aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter import (
        DisconnectGithubSourceResult,
    )

    journal = _journal_with_live_forward()
    plan = {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter.disconnect_github_source",
            return_value=DisconnectGithubSourceResult(
                ok=True,
                mutation_performed=True,
                service_id="svc-1",
                environment_id="env-staging",
                repository="org/repo",
                branch="main",
                detail="disconnected",
            ),
        ):
            result = run_real_disconnect_connect_source_rollback(
                journal=journal,
                plan=plan,
                policy=policy,
                user_text=NON_PRODUCTION_FINAL_PHRASE,
            )
    assert result.rollback_receipt_recorded is True
    assert result.mutation_performed is True
    receipt = find_phase_receipt(execution_id="exec-live-rb", phase="rollback_connect_source")
    assert receipt is not None
    assert receipt["status"] == STATUS_ROLLBACK_MUTATION_SUCCESS
    assert receipt["mutation_performed"] is True
    assert "github_source_bound" not in result.journal


def test_live_rollback_idempotent_replay():
    journal = _journal_with_live_forward()
    record_execution_receipt(
        execution_id="exec-live-rb",
        phase="rollback_connect_source",
        status=STATUS_ROLLBACK_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="already done",
    )
    plan = {"repo": "org/repo", "environment": "staging", "branch": "main"}
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        result = run_real_disconnect_connect_source_rollback(journal=journal, plan=plan)
    assert result.idempotent_replay is True


def test_dry_run_simulate_does_not_call_live_disconnect():
    journal = _journal_with_live_forward()
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.disconnect_github_source_adapter.disconnect_github_source",
    ) as mock_disconnect:
        run_dry_run_connect_source_rollback(journal=journal)
    mock_disconnect.assert_not_called()


def test_simulated_forward_does_not_enable_live_rollback():
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-sim",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
        }
    )
    record_execution_receipt(
        execution_id="exec-sim",
        phase="connect_source",
        status="simulated_success",
        mutation_performed=False,
        detail="simulated",
    )
    contract = build_connect_source_rollback_contract(journal=journal, execution_id="exec-sim")
    assert contract.forward_live_mutation_recorded is False
    assert contract.eligible_for_dry_run_rollback is True


def test_execute_rollback_route_policy_blocked_by_default():
    plan = {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }
    save_deployment_plan_context(session_id="s2", plan=plan)
    journal = _journal_with_live_forward()
    save_execution_journal(journal)
    from aethos_core.providers.railway.execution_contract.execution_context import (
        bind_session_execution,
    )

    bind_session_execution(session_id="s2", execution_id="exec-live-rb")

    route = route_railway_execution_contract(
        "execute railway source binding rollback",
        session_id="s2",
    )
    assert route is not None
    assert route[2]["policy_blocked"] == "true" or route[2]["mutation_performed"] == "false"


def test_dry_run_then_live_blocked_by_rollback_receipt():
    journal = _journal_with_live_forward()
    dry = run_dry_run_connect_source_rollback(journal=journal)
    receipt = find_phase_receipt(execution_id="exec-live-rb", phase="rollback_connect_source")
    assert receipt["status"] == STATUS_ROLLBACK_SIMULATED_SUCCESS

    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_DISCONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        live = run_real_disconnect_connect_source_rollback(
            journal=dry.journal,
            plan={"repo": "org/repo", "environment": "staging", "branch": "main"},
        )
    assert live.idempotent_replay is True
    assert live.mutation_performed is False
