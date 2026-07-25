# SPDX-License-Identifier: Apache-2.0
"""FIX 110 — connect_source rollback contract and dry-run executor."""

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
)
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_ROLLBACK_SIMULATED_SUCCESS,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    list_rollback_receipts,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_rollback import attach_rollback_journal
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter import (
    connect_github_source,
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


def _journal_with_binding() -> dict:
    journal = attach_rollback_journal(
        {
            "execution_id": "exec-rb",
            "state": "execution_phase_connect_source",
            "railway_service_id": "svc-1",
            "railway_environment_id": "env-staging",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
        }
    )
    record_execution_receipt(
        execution_id="exec-rb",
        phase="connect_source",
        status="mutation_success",
        mutation_performed=True,
        detail="bound skipDeploys=true",
    )
    return journal


def test_dry_run_rollback_executor_does_not_import_live_disconnect():
    import re

    mod = sys.modules[
        "aethos_core.providers.railway.execution_contract.execution_dry_run_rollback_executor"
    ]
    source = open(mod.__file__, encoding="utf-8").read()
    assert not re.search(
        r"^\s*(?:from|import)\s+.*disconnect_github_source",
        source,
        re.MULTILINE,
    )
    assert connect_github_source.__module__ != mod.__name__


def test_rollback_contract_eligible_when_forward_recorded():
    journal = _journal_with_binding()
    contract = build_connect_source_rollback_contract(journal=journal, execution_id="exec-rb")
    assert contract.eligible_for_dry_run_rollback is True
    assert contract.dry_run_only is True
    assert contract.live_rollback_enabled is False


def test_dry_run_rollback_records_receipt():
    journal = _journal_with_binding()
    result = run_dry_run_connect_source_rollback(journal=journal)
    assert result.rollback_receipt_recorded is True
    assert result.mutation_performed is False
    receipt = find_phase_receipt(execution_id="exec-rb", phase="rollback_connect_source")
    assert receipt is not None
    assert receipt["status"] == STATUS_ROLLBACK_SIMULATED_SUCCESS
    assert receipt["mutation_performed"] is False


def test_dry_run_rollback_idempotent_replay():
    journal = _journal_with_binding()
    first = run_dry_run_connect_source_rollback(journal=journal)
    second = run_dry_run_connect_source_rollback(journal=first.journal)
    assert second.idempotent_replay is True
    rollback_receipts = [
        r
        for r in list_rollback_receipts(execution_id="exec-rb")
        if r.get("phase") == "rollback_connect_source"
    ]
    assert len(rollback_receipts) == 1


def test_simulate_rollback_route_and_timeline():
    plan = {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "api",
        "branch": "main",
    }
    save_deployment_plan_context(session_id="s1", plan=plan)
    journal = _journal_with_binding()
    from aethos_core.providers.railway.execution_contract.execution_context import (
        bind_session_execution,
    )
    from aethos_core.providers.railway.execution_contract.execution_journal import (
        save_execution_journal,
    )

    save_execution_journal(journal)
    bind_session_execution(session_id="s1", execution_id="exec-rb")

    contract_route = route_railway_execution_contract(
        "show railway source binding rollback contract",
        session_id="s1",
    )
    assert contract_route is not None
    assert "rollback_connect_source" in contract_route[0]

    sim = route_railway_execution_contract(
        "simulate railway source binding rollback",
        session_id="s1",
    )
    assert sim is not None
    assert sim[2]["mutation_performed"] == "false"

    timeline = route_railway_execution_contract("show railway rollback timeline", session_id="s1")
    assert timeline is not None
    assert "rollback_connect_source" in timeline[0]
    assert "rollback_simulated_success" in timeline[0] or "connect_source rollback" in timeline[0]


def test_connect_github_source_adapter_not_called_during_dry_run_rollback():
    journal = _journal_with_binding()
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.connect_github_source_adapter.connect_github_source",
    ) as mock_connect:
        run_dry_run_connect_source_rollback(journal=journal)
    mock_connect.assert_not_called()
