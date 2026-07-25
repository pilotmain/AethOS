# SPDX-License-Identifier: Apache-2.0
"""FIX 114 — readonly runtime verification after deploy."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_readonly_runtime_verification_executor import (
    run_readonly_runtime_verification,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_dispatch import (
    run_single_real_mutation_phase,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.runtime_verification_readiness import (
    assess_runtime_verification_readiness,
)
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
)
from aethos_core.providers.railway.greenfield_adapters.verify_runtime_readonly_adapter import (
    VerifyRuntimeReadonlyResult,
    verify_runtime_readonly,
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


def _journal_ready_for_verify() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-114",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "railway_deployment_id": "dep-114",
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
            "deploy_trigger_metadata": {
                "deployment_id": "dep-114",
                "graphql_operation": "serviceInstanceRedeploy",
            },
            "runtime_verification_performed": False,
        }
    )
    for phase in ("create_service", "connect_source", "trigger_deploy"):
        record_execution_receipt(
            execution_id="exec-114",
            phase=phase,
            status="mutation_success",
            mutation_performed=True,
            detail="ok",
        )
    record_execution_receipt(
        execution_id="exec-114",
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
def test_runtime_verification_executor_records_readonly_success(_mock_bind):
    journal = _journal_ready_for_verify()
    plan = _plan()

    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED": "true",
            "RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED": "true",
            "RAILWAY_GREENFIELD_VERIFY_RUNTIME_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.verify_runtime_readonly_adapter.verify_runtime_readonly",
            return_value=VerifyRuntimeReadonlyResult(
                ok=True,
                verified=True,
                deployment_id="dep-114",
                deployment_state="success",
                service_id="svc-1",
                detail="healthy",
            ),
        ):
            result = run_readonly_runtime_verification(
                journal=journal,
                plan=plan,
                policy=policy,
                user_text=NON_PRODUCTION_FINAL_PHRASE,
            )

    assert result.mutation_performed is False
    assert result.journal.get("runtime_verification_performed") is True
    assert result.journal.get("runtime_verification", {}).get("verified") is True
    receipt = find_phase_receipt(execution_id="exec-114", phase="verify_runtime")
    assert receipt is not None
    assert receipt["mutation_performed"] is False
    assert receipt["status"] == "verification_readonly_success"


def test_runtime_verification_policy_blocked_when_disabled():
    journal = _journal_ready_for_verify()
    result = run_readonly_runtime_verification(
        journal=journal,
        plan=_plan(),
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert result.policy_blocked is True


def test_verify_runtime_adapter_requires_authorization():
    result = verify_runtime_readonly(
        environment_name="staging",
        service_id="svc-1",
        deployment_id="dep-114",
    )
    assert result.ok is False


def test_runtime_verification_idempotent_replay():
    journal = _journal_ready_for_verify()
    journal["runtime_verification_performed"] = True
    journal["runtime_verification"] = {
        "verified": True,
        "deployment_id": "dep-114",
        "deployment_state": "success",
    }
    record_execution_receipt(
        execution_id="exec-114",
        phase="verify_runtime",
        status="verification_readonly_success",
        mutation_performed=False,
        detail="prior",
    )
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_VERIFY_RUNTIME_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        result = run_readonly_runtime_verification(
            journal=journal,
            plan=_plan(),
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
    assert result.idempotent_replay is True
    assert result.mutation_performed is False


def test_readonly_executor_does_not_import_dry_run_or_trigger_deploy():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_readonly_runtime_verification_executor"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "run_dry_run_phase_execution" not in source
    assert "trigger_railway_deploy" not in source
    assert "trigger_deploy_adapter" not in source


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(ok=True, verified=True, detail="ok"),
)
def test_dispatch_runs_verify_after_trigger_deploy_complete(_mock_bind):
    journal = _journal_ready_for_verify()
    plan = _plan()

    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
            "RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED": "true",
            "RAILWAY_GREENFIELD_TRIGGER_DEPLOY_ENABLED": "true",
            "RAILWAY_GREENFIELD_VERIFY_RUNTIME_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.verify_runtime_readonly_adapter.verify_runtime_readonly",
            return_value=VerifyRuntimeReadonlyResult(
                ok=True,
                verified=True,
                deployment_id="dep-114",
                deployment_state="success",
                service_id="svc-1",
                detail="healthy",
            ),
        ):
            result = run_single_real_mutation_phase(
                journal=journal,
                plan=plan,
                user_text=NON_PRODUCTION_FINAL_PHRASE,
            )

    assert result.mutation_performed is False
    assert "verify_runtime" in (result.executed_phases or [])
    readiness = assess_runtime_verification_readiness(
        plan=plan,
        journal=result.journal,
        execution_id="exec-114",
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert readiness.ready_for_runtime_verification is True
