# SPDX-License-Identifier: Apache-2.0
"""FIX 113 — governed deploy trigger adapter and executor."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.deploy_trigger_rollback_contract import (
    build_deploy_trigger_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_trigger_deploy import (
    run_real_mutation_trigger_deploy,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
)
from aethos_core.providers.railway.greenfield_adapters.trigger_deploy_adapter import (
    trigger_railway_deploy,
)


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


def _journal_ready_for_deploy() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-113",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
            "env_configure_groups": {
                "minimum_secrets": {
                    "recorded": True,
                    "env_names": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
                }
            },
            "env_configure_verification": {
                "ok": True,
                "verified": True,
                "minimum_secrets_present": True,
                "names_observed": ["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
                "missing_names": [],
            },
        }
    )
    record_execution_receipt(
        execution_id="exec-113",
        phase="create_service",
        status="mutation_success",
        mutation_performed=True,
        detail="created",
    )
    record_execution_receipt(
        execution_id="exec-113",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="skipDeploys=true",
    )
    record_execution_receipt(
        execution_id="exec-113",
        phase="configure_env",
        status="mutation_success",
        mutation_performed=True,
        detail="configured",
        receipt_group="minimum_secrets",
        env_var_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )
    return journal


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(ok=True, verified=True, detail="ok"),
)
def test_trigger_deploy_executor_records_deployment_id(_mock_bind):
    from aethos_core.providers.railway.greenfield_adapters.trigger_deploy_adapter import (
        TriggerDeployResult,
    )

    journal = _journal_ready_for_deploy()
    plan = _plan()

    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED": "true",
            "RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.trigger_deploy_adapter.trigger_railway_deploy",
            return_value=TriggerDeployResult(
                ok=True,
                mutation_performed=True,
                service_id="svc-1",
                environment_id="env-staging",
                deployment_id="dep-113",
                graphql_operation="serviceInstanceRedeploy",
                provider_request_id="dep-113",
                detail="triggered",
            ),
        ):
            result = run_real_mutation_trigger_deploy(
                journal=journal,
                plan=plan,
                policy=policy,
                user_text=NON_PRODUCTION_FINAL_PHRASE,
            )

    assert result.mutation_performed is True
    assert result.journal.get("railway_deployment_id") == "dep-113"
    assert result.journal.get("runtime_verification_performed") is False
    receipt = find_phase_receipt(execution_id="exec-113", phase="trigger_deploy")
    assert receipt is not None
    assert receipt["mutation_performed"] is True
    assert "verify" not in receipt["detail"].lower() or "fix 114" in result.detail.lower()


def test_trigger_deploy_policy_blocked_when_disabled():
    journal = _journal_ready_for_deploy()
    result = run_real_mutation_trigger_deploy(
        journal=journal,
        plan=_plan(),
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert result.policy_blocked is True


def test_trigger_deploy_adapter_requires_authorization():
    result = trigger_railway_deploy(
        environment_name="staging",
        environment_id="env-1",
        service_id="svc-1",
        idempotency_key="k",
    )
    assert result.ok is False


def test_trigger_deploy_idempotent_replay():
    journal = _journal_ready_for_deploy()
    journal["railway_deployment_id"] = "dep-existing"
    record_execution_receipt(
        execution_id="exec-113",
        phase="trigger_deploy",
        status="mutation_success",
        mutation_performed=True,
        detail="prior",
    )
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED": "true",
            "RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=_plan(),
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        result = run_real_mutation_trigger_deploy(
            journal=journal,
            plan=_plan(),
            policy=policy,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
    assert result.idempotent_replay is True
    assert result.mutation_performed is False


def test_trigger_deploy_executor_does_not_import_dry_run():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_trigger_deploy"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "run_dry_run_phase_execution" not in source


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(ok=True, verified=True, detail="ok"),
)
def test_rollback_contract_visible_before_trigger(_mock_bind):
    contract = build_deploy_trigger_rollback_contract(
        journal=_journal_ready_for_deploy(),
        plan=_plan(),
        execution_id="exec-113",
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert contract.rollback_journal_present is True
    assert contract.rollback_plan_ready is True
