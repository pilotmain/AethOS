# SPDX-License-Identifier: Apache-2.0
"""Tests for governed Railway greenfield orchestration after MC approval."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
from aethos_core.provider_e2e_orchestration.executor import run_provider_e2e_orchestration
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store


@pytest.fixture(autouse=True)
def _clear_jobs():
    job_store._jobs.clear()
    yield
    job_store._jobs.clear()


def _greenfield_params() -> dict:
    return {
        "provider": "railway",
        "flow": "railway_greenfield_deployment",
        "greenfield": True,
        "provider_e2e_approved": True,
        "session_id": "gf-test",
        "user_request": "deploy killit-api to railway staging",
        "preflight_id": "rgf-test",
        "parent_greenfield_job_id": "job-preflight",
        "target_plan": {
            "repo": "pilotmain/killit",
            "branch": "main",
            "project": "pilotos",
            "environment": "staging",
            "service_name": "killit-api",
            "health_check_path": "/",
        },
        "service_name": "killit-api",
        "project_name": "pilotos",
        "environment": "staging",
        "deploy_action": "none",
    }


def test_greenfield_orchestration_delegates_to_governed_executor():
    job = authority.create_job(
        title="Railway greenfield execution: killit-api",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=_greenfield_params(),
        source="test",
        session_id="gf-test",
        auto_run=False,
    )
    with patch(
        "aethos_core.provider_e2e_orchestration.executor._run_governed_railway_greenfield_orchestration"
    ) as mocked:
        from aethos_core.provider_e2e_orchestration.executor import ProviderE2EExecutionOutcome

        mocked.return_value = ProviderE2EExecutionOutcome(
            summary="ok",
            full_result="ok",
            executed=True,
            blocked=False,
            artifact={"execution_status": "completed"},
        )
        outcome = run_provider_e2e_orchestration(job_id=job.id, params=dict(job.params or {}))
    mocked.assert_called_once()
    assert outcome.executed is True


def test_greenfield_orchestration_reports_credential_blocker():
    job = authority.create_job(
        title="Railway greenfield execution: killit-api",
        job_type=PROVIDER_E2E_ORCHESTRATION_JOB_TYPE,
        params=_greenfield_params(),
        source="test",
        session_id="gf-test",
        auto_run=False,
    )
    with patch(
        "aethos_core.providers.railway.greenfield_deployment.governed_greenfield_executor.resolve_railway_credential"
    ) as cred:
        from aethos_core.providers.railway.credential_truth import RailwayCredentialResolution

        cred.return_value = RailwayCredentialResolution(
            token=None,
            source="none",
            credential_id="",
            masked_identifier="",
            resolver="test",
            detail="No validated vault credential or environment Railway token available.",
        )
        outcome = run_provider_e2e_orchestration(job_id=job.id, params=dict(job.params or {}))
    assert outcome.executed is False
    assert outcome.blocked is True
    assert "Railway token" in outcome.summary or "credential" in outcome.summary.lower()
