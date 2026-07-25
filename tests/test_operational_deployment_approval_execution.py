# SPDX-License-Identifier: Apache-2.0
"""Operational deployment approval inbox → governed chat approve route."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox
from aethos_core.mission_control.approval_inbox.operational_deployment_approval_execution_service import (
    execute_operational_deployment_approval_from_inbox,
    reject_operational_deployment_approval_from_inbox,
)
from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
    create_railway_greenfield_preflight_job,
)
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    job_store.clear_for_tests()
    get_settings.cache_clear()
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_MODE", "enabled")
    monkeypatch.setenv("RAILWAY_GREENFIELD_REQUIRE_FINAL_PHRASE", "false")
    get_settings.cache_clear()
    yield
    job_store.clear_for_tests()
    get_settings.cache_clear()


def _seed_greenfield_preflight(*, session_id: str = "sess-deploy-approve") -> str:
    plan = {
        "repo": "pilotmain/killit",
        "branch": "main",
        "project": "pilotos",
        "environment": "staging",
        "service_name": "killit",
        "risk_tier": "standard",
    }
    preflight = create_railway_greenfield_preflight_job(
        user_text="deploy killit to railway",
        session_id=session_id,
        plan=plan,
        env_report={"required_env_var_names": [], "count": 0},
        local_source={"ok": True, "workspace_name": "killit"},
        git_remote={"ok": True, "repository": "pilotmain/killit", "branch": "main"},
    )
    return str(preflight.get("job_id") or "")


def test_execute_operational_deployment_from_inbox_uses_governed_route(monkeypatch):
    job_id = _seed_greenfield_preflight()
    inbox = build_approval_inbox(session_id="operator")
    item = next(i for i in inbox.items if str(i.get("context", {}).get("job_id") or "") == job_id)
    assert item.get("deployment_execution_enabled") is True

    orchestration_id = "job-orch-test"

    def _mock_approve(preflight_job_id, **kwargs):
        job = job_store.get(preflight_job_id)
        job.params["greenfield_preflight_approved"] = True
        return job, {"preflight_id": "rgf-test", "orchestration_job_id": orchestration_id}

    monkeypatch.setattr(
        "aethos_core.providers.railway.greenfield_deployment.greenfield_approval_flow.approve_railway_greenfield_preflight",
        _mock_approve,
    )

    result = execute_operational_deployment_approval_from_inbox(
        session_id="operator",
        inbox_id=item["inbox_id"],
    )

    assert result.ok
    assert result.job_id == job_id
    assert result.route_id == "pending_job_approval_resolved"
    assert result.audit_id
    approved = job_store.get(job_id)
    assert approved.params.get("greenfield_preflight_approved") is True


def test_execute_operational_deployment_blocked_when_planning_only(monkeypatch):
    monkeypatch.setenv("RAILWAY_GREENFIELD_EXECUTION_ENABLED", "false")
    get_settings.cache_clear()
    job_id = _seed_greenfield_preflight()
    inbox = build_approval_inbox(session_id="operator")
    item = next(i for i in inbox.items if str(i.get("context", {}).get("job_id") or "") == job_id)
    assert item.get("deployment_execution_enabled") is False

    result = execute_operational_deployment_approval_from_inbox(
        session_id="operator",
        inbox_id=item["inbox_id"],
    )
    assert not result.ok
    assert result.blockers == ["deployment_execution_disabled"]


def test_reject_operational_deployment_clears_pending():
    job_id = _seed_greenfield_preflight()
    inbox = build_approval_inbox(session_id="operator")
    item = next(i for i in inbox.items if str(i.get("context", {}).get("job_id") or "") == job_id)

    result = reject_operational_deployment_approval_from_inbox(
        session_id="operator",
        inbox_id=item["inbox_id"],
    )
    assert result.ok
    job = job_store.get(job_id)
    assert job.params.get("approval_rejected") is True
    assert job.params.get("approval_required") is False

    inbox_after = build_approval_inbox(session_id="operator")
    assert not any(str(i.get("context", {}).get("job_id") or "") == job_id for i in inbox_after.items)
