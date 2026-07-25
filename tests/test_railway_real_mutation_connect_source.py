# SPDX-License-Identifier: Apache-2.0
"""FIX 109 — real connect_source executor isolation and dispatch."""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.execution_dry_run_executor import (
    run_dry_run_phase_execution,
)
from aethos_core.providers.railway.execution_contract.execution_enablement import (
    NON_PRODUCTION_FINAL_PHRASE,
    assess_railway_execution_enablement_policy,
)
from aethos_core.providers.railway.execution_contract.execution_journal import (
    clear_for_tests as clear_journal,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_connect_source import (
    run_real_mutation_connect_source,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_dispatch import (
    run_single_real_mutation_phase,
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_MUTATION_SUCCESS,
    STATUS_SIMULATED_SUCCESS,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    list_execution_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter import (
    ConnectGithubSourceResult,
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
        "service_name": "aethos-api",
        "branch": "main",
    }


def test_connect_source_executor_does_not_import_dry_run():
    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_connect_source"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert "run_dry_run_phase_execution" not in source


def test_dispatch_runs_connect_source_after_create_service():
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-109",
            "state": "execution_phase_create_service",
            "idempotency_key": "idem-109",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "railway_project_id": "proj-1",
        }
    )
    plan = _plan()
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
            "RAILWAY_GREENFIELD_CONNECT_SOURCE_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.connect_github_source",
            return_value=ConnectGithubSourceResult(
                ok=True,
                mutation_performed=True,
                service_id="svc-1",
                environment_id="env-staging",
                repository="org/repo",
                branch="main",
                detail="bound",
            ),
        ) as mock_bind:
            result = run_single_real_mutation_phase(
                journal=journal,
                plan=plan,
                policy=policy,
            )
    mock_bind.assert_called_once()
    assert result.mutation_performed is True
    assert result.journal["state"] == "execution_phase_connect_source"
    assert result.journal.get("github_source_bound") == {"repository": "org/repo", "branch": "main"}
    receipt = find_phase_receipt(execution_id="exec-109", phase="connect_source")
    assert receipt is not None
    assert receipt["status"] == STATUS_MUTATION_SUCCESS
    assert not any(r.get("phase") == "configure_env" for r in list_execution_receipts(execution_id="exec-109"))


def test_connect_source_idempotent_replay():
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-r2",
            "state": "execution_phase_connect_source",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
        }
    )
    record_execution_receipt(
        execution_id="exec-r2",
        phase="connect_source",
        status=STATUS_MUTATION_SUCCESS,
        mutation_performed=True,
        detail="prior",
    )
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.connect_github_source",
    ) as mock_bind:
        result = run_real_mutation_connect_source(journal=journal, plan=_plan())
    mock_bind.assert_not_called()
    assert result.idempotent_replay is True


def test_dry_run_never_calls_connect_github_source():
    journal = {"execution_id": "exec-dry2", "state": "execution_locked"}
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.connect_github_source",
    ) as mock_bind:
        run_dry_run_phase_execution(journal=journal, plan=_plan())
    mock_bind.assert_not_called()
    receipt = find_phase_receipt(execution_id="exec-dry2", phase="connect_source")
    assert receipt is not None
    assert receipt["status"] == STATUS_SIMULATED_SUCCESS
