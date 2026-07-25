# SPDX-License-Identifier: Apache-2.0
"""FIX 108 — real mutation executor is isolated from dry-run."""

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
    save_execution_journal,
)
from aethos_core.providers.railway.execution_contract.execution_real_mutation_executor import (
    run_real_mutation_create_service,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    list_execution_receipts,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.greenfield_adapters.create_service_adapter import (
    CreateRailwayServiceResult,
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


def test_real_executor_does_not_import_dry_run_internals():
    real_mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_executor"
    ]
    source = open(real_mod.__file__, encoding="utf-8").read()
    assert "run_dry_run_phase_execution" not in source
    assert "execution_dry_run_executor" not in source


def test_real_executor_stops_after_create_service_phase():
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-108",
            "state": "execution_locked",
            "idempotency_key": "idem-108",
        }
    )
    plan = {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
    }
    policy = assess_railway_execution_enablement_policy(
        plan=plan,
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    with patch.dict(
        "os.environ",
        {
            "RAILWAY_GREENFIELD_EXECUTION_ENABLED": "true",
            "RAILWAY_GREENFIELD_EXECUTION_MODE": "enabled",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        policy = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=NON_PRODUCTION_FINAL_PHRASE,
        )
        with patch(
            "aethos_core.providers.railway.execution_contract.execution_real_mutation_executor.create_railway_service",
            return_value=CreateRailwayServiceResult(
                ok=True,
                mutation_performed=True,
                service_id="svc-live",
                service_name="aethos-api",
                project_id="proj-1",
                environment_id="env-staging",
                detail="serviceCreate succeeded",
            ),
        ):
            result = run_real_mutation_create_service(
                journal=journal,
                plan=plan,
                policy=policy,
            )

    assert result.mutation_performed is True
    assert result.journal["state"] == "execution_phase_create_service"
    assert result.journal.get("railway_service_id") == "svc-live"
    receipts = list_execution_receipts(execution_id="exec-108")
    forward = [r for r in receipts if r.get("phase") == "create_service"]
    assert len(forward) == 1
    assert forward[0]["mutation_performed"] is True
    assert not any(r.get("phase") == "connect_source" for r in receipts)


def test_real_executor_idempotent_replay_skips_second_mutation():
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-replay",
            "state": "execution_phase_create_service",
            "idempotency_key": "idem-replay",
            "railway_service_id": "svc-live",
            "execution_mode": "enabled",
        }
    )
    save_execution_journal(journal)
    from aethos_core.providers.railway.execution_contract.execution_receipts import (
        record_execution_receipt,
    )

    record_execution_receipt(
        execution_id="exec-replay",
        phase="create_service",
        status="mutation_success",
        mutation_performed=True,
        detail="prior mutation",
    )
    plan = {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
    }
    with patch(
        "aethos_core.providers.railway.execution_contract.execution_real_mutation_executor.create_railway_service",
    ) as mock_create:
        result = run_real_mutation_create_service(journal=journal, plan=plan)
    mock_create.assert_not_called()
    assert result.idempotent_replay is True


def test_dry_run_never_calls_create_service_adapter():
    journal = {
        "execution_id": "exec-dry",
        "state": "execution_locked",
    }
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.create_railway_service",
    ) as mock_create:
        run_dry_run_phase_execution(journal=journal, plan={})
    mock_create.assert_not_called()
    receipt = find_phase_receipt(execution_id="exec-dry", phase="create_service")
    assert receipt is not None
    assert receipt["mutation_performed"] is False
