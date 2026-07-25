# SPDX-License-Identifier: Apache-2.0
"""FIX 112 — secure configure_env adapter and executor."""

from __future__ import annotations

import re
import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.env_value_readiness.env_secure_resolution import (
    resolve_env_var_from_secure_store,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
    set_deployment_env_presence_for_tests,
)
from aethos_core.providers.railway.execution_contract.env_configure_rollback_contract import (
    build_env_configure_rollback_contract,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_configure_env import (
    run_real_mutation_configure_env,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    list_execution_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.source_binding_verification import (
    SourceBindingVerification,
)
from aethos_core.providers.railway.greenfield_adapters.configure_env_adapter import (
    configure_env_group,
)
from aethos_core.providers.railway.greenfield_adapters.env_configure_graphql import (
    validate_stage_input_env_only,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_journal()
    clear_receipts()
    clear_deployment_env_presence_for_tests()
    get_settings.cache_clear()
    yield
    clear_journal()
    clear_receipts()
    clear_deployment_env_presence_for_tests()
    get_settings.cache_clear()


def _plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }


def _journal_ready() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-112",
            "state": "execution_phase_connect_source",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
        }
    )
    record_execution_receipt(
        execution_id="exec-112",
        phase="create_service",
        status="mutation_success",
        mutation_performed=True,
        detail="created",
    )
    record_execution_receipt(
        execution_id="exec-112",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="bound skipDeploys=true",
    )
    return journal


def test_validate_stage_input_rejects_source_keys():
    errors = validate_stage_input_env_only(
        {
            "services": {
                "svc": {
                    "source": {"repo": "org/repo"},
                    "variables": {"ANTHROPIC_API_KEY": "x"},
                }
            }
        }
    )
    assert errors


def test_secure_resolution_blocks_local_env_only(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "local-only-secret")
    plan = _plan()
    result = resolve_env_var_from_secure_store("ANTHROPIC_API_KEY", plan=plan)
    assert result.ok is False
    assert result.value == ""
    assert result.blocked_reason in {
        "not_present_in_secure_store",
        "forbidden_source",
        "secure_store_missing",
    }


def test_rollback_contract_requires_live_forward():
    journal = _journal_ready()
    contract = build_env_configure_rollback_contract(journal=journal, plan=_plan(), execution_id="exec-112")
    assert contract.forward_connect_source_live_recorded is True


@patch(
    "aethos_core.providers.railway.execution_contract.source_binding_status.verify_source_binding_readonly",
    return_value=SourceBindingVerification(
        ok=True,
        verified=True,
        repository_observed="org/repo",
        branch_observed="main",
        detail="ok",
    ),
)
def test_configure_env_executor_records_group_receipts(_mock_verify):
    from aethos_core.providers.railway.greenfield_adapters.configure_env_adapter import (
        ConfigureEnvGroupResult,
    )

    journal = _journal_ready()
    plan = _plan()
    target_key = "org/repo|pilotos|staging|api"
    set_deployment_env_presence_for_tests(
        target_key=target_key,
        present_names=["ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"],
    )

    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONFIGURE_ENV_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.configure_env_adapter.configure_env_group",
            return_value=ConfigureEnvGroupResult(
                ok=True,
                group_id="minimum_secrets",
                mutation_performed=True,
                env_names_written=("ANTHROPIC_API_KEY", "WEB_SEARCH_API_KEY"),
                version_fingerprint="abc",
                detail="configured",
            ),
        ):
            result = run_real_mutation_configure_env(
                journal=journal,
                plan=plan,
                policy=policy,
                user_text=NON_PRODUCTION_FINAL_PHRASE,
            )

    assert result.mutation_performed is True
    receipts = [
        r
        for r in list_execution_receipts(execution_id="exec-112")
        if r.get("phase") == "configure_env"
    ]
    assert len(receipts) == 1
    assert receipts[0].get("receipt_group") == "minimum_secrets"
    assert "ANTHROPIC_API_KEY" in (receipts[0].get("env_var_names") or [])
    detail = str(receipts[0].get("detail") or "")
    assert "sk-" not in detail.lower()
    assert "secret" not in detail.lower() or "no secret" in detail.lower()


def test_configure_env_blocks_chat_secrets_in_user_text():
    journal = _journal_ready()
    result = run_real_mutation_configure_env(
        journal=journal,
        plan=_plan(),
        user_text="set env variable ANTHROPIC_API_KEY=sk-chat-leak",
    )
    assert result.policy_blocked is True
    assert "chat_secrets_forbidden" in result.errors


def test_configure_env_adapter_requires_authorization():
    result = configure_env_group(
        environment_name="staging",
        environment_id="env-1",
        service_id="svc-1",
        group_id="minimum_secrets",
        env_names=("ANTHROPIC_API_KEY",),
        plan=_plan(),
    )
    assert result.ok is False


def test_configure_env_executor_does_not_import_dry_run():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_configure_env"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "run_dry_run_phase_execution" not in source


def test_receipts_never_store_secret_values():
    journal = _journal_ready()
    record_execution_receipt(
        execution_id="exec-112",
        phase="configure_env",
        status="mutation_success",
        mutation_performed=True,
        detail="group configured (no values)",
        receipt_group="minimum_secrets",
        env_var_names=["ANTHROPIC_API_KEY"],
    )
    for receipt in list_execution_receipts(execution_id="exec-112"):
        blob = str(receipt)
        assert not re.search(r"sk-[a-zA-Z0-9]{10,}", blob)
