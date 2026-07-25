# SPDX-License-Identifier: Apache-2.0
"""FIX 108B — mutation audit, preview, kill switch, receipt status taxonomy."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
    clear_for_tests as clear_plan,
    save_deployment_plan_context,
)
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
from aethos_core.providers.railway.execution_contract.execution_receipt_status import (
    STATUS_MUTATION_SUCCESS,
    STATUS_SIMULATED_SUCCESS,
    normalize_receipt_status,
    phase_mutation_recorded,
)
from aethos_core.providers.railway.execution_contract.execution_receipts import (
    clear_for_tests as clear_receipts,
    find_phase_receipt,
    record_execution_receipt,
)
from aethos_core.providers.railway.execution_contract.execution_router import (
    route_railway_execution_contract,
)
from aethos_core.providers.railway.execution_contract.mutation_audit import (
    build_railway_mutation_audit_report,
)
from aethos_core.providers.railway.execution_contract.mutation_preview import (
    assess_railway_mutation_preview,
)
from aethos_core.providers.railway.greenfield_adapters.create_service_adapter import (
    create_railway_service,
)
from aethos_core.providers.railway.greenfield_adapters.mutation_kill_switch import (
    is_railway_mutation_kill_switch_active,
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


def _plan() -> dict:
    return {
        "repo": "org/repo",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "aethos-api",
    }


def test_kill_switch_blocks_real_mutation_policy(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_MUTATION_KILL_SWITCH", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    get_settings.cache_clear()
    assert is_railway_mutation_kill_switch_active() is True
    policy = assess_railway_execution_enablement_policy(
        plan=_plan(),
        user_text=NON_PRODUCTION_FINAL_PHRASE,
    )
    assert policy.allows_real_mutation() is False
    assert "mutation_kill_switch_active" in policy.blocking_reasons


def test_kill_switch_blocks_adapter_even_with_authorization(monkeypatch):
    from aethos_core.providers.railway.greenfield_adapters.mutation_live_gate import (
        live_create_service_authorization,
    )

    monkeypatch.setenv("RAILWAY_GREENFIELD_MUTATION_KILL_SWITCH", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    get_settings.cache_clear()
    with live_create_service_authorization():
        result = create_railway_service(
            project_name="pilotos",
            environment_name="staging",
            service_name="aethos-api",
            idempotency_key="k",
        )
    assert result.ok is False
    assert any("kill switch" in err.lower() for err in result.errors)


def test_receipt_statuses_distinguish_simulated_and_mutation():
    sim = normalize_receipt_status(
        {"status": "simulated_success", "mutation_performed": False}
    )
    live = normalize_receipt_status(
        {"status": "mutation_success", "mutation_performed": True}
    )
    assert sim["status"] == STATUS_SIMULATED_SUCCESS
    assert live["status"] == STATUS_MUTATION_SUCCESS
    legacy = normalize_receipt_status({"status": "completed", "mutation_performed": True})
    assert legacy["status"] == STATUS_MUTATION_SUCCESS


def test_phase_mutation_recorded_treats_skipped_as_no_duplicate():
    skipped = normalize_receipt_status(
        {"status": "mutation_skipped", "mutation_performed": False, "replayed": True}
    )
    assert phase_mutation_recorded(skipped) is True


def test_mutation_preview_command(monkeypatch):
    save_deployment_plan_context(session_id="s1", plan=_plan())
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "disabled")
    get_settings.cache_clear()
    routed = route_railway_execution_contract(
        "what would railway mutate",
        session_id="s1",
    )
    assert routed is not None
    body, route_id, meta = routed
    assert route_id == "railway_mutation_preview"
    assert "Mutation Preview" in body
    assert meta["mutation_performed"] == "false"
    assert "would_mutate" in body.lower()


def test_mutation_audit_reports_isolation(monkeypatch):
    save_deployment_plan_context(session_id="s1", plan=_plan())
    report = build_railway_mutation_audit_report(plan=_plan())
    assert report.dry_run_cannot_reach_live_adapter is True
    assert report.live_adapter_requires_authorization_token is True
    assert any(c.name == "dry_run_executor_does_not_import_live_adapter" for c in report.isolation_checks)


def test_dry_run_receipt_is_simulated_success_not_mutation():
    journal = {"execution_id": "exec-sim", "state": "execution_locked"}
    with patch(
        "aethos_core.providers.railway.greenfield_adapters.create_service_adapter.create_railway_service",
    ) as mock_create:
        run_dry_run_phase_execution(journal=journal, plan=_plan())
    mock_create.assert_not_called()
    receipt = find_phase_receipt(execution_id="exec-sim", phase="create_service")
    assert receipt is not None
    assert receipt["status"] == STATUS_SIMULATED_SUCCESS
    assert receipt["mutation_performed"] is False


def test_show_mutation_audit_route(monkeypatch):
    save_deployment_plan_context(session_id="s1", plan=_plan())
    routed = route_railway_execution_contract("show railway mutation audit", session_id="s1")
    assert routed is not None
    body, route_id, _meta = routed
    assert route_id == "railway_mutation_audit"
    assert "Live Mutation Audit" in body
    assert "dry_run isolated" in body.lower() or "dry_run_executor" in body.lower()


def test_idempotent_replay_preview_blocks_would_mutate():
    plan = _plan()
    preview = assess_railway_mutation_preview(
        plan=plan,
        execution_id="exec-1",
        journal={
            "railway_service_id": "svc-1",
            "github_source_bound": {"repository": "org/repo", "branch": "main"},
        },
    )
    assert preview.idempotent_replay is True
    assert preview.would_mutate is False
