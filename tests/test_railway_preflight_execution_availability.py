# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.railway.api_client.find_service_by_name")
def test_railway_deployments_preflight_reports_readonly_execution_available(
    mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-rw"}
    mock_find.return_value = {
        "service_id": "svc-1",
        "service_name": "speakglobal-ai",
        "project_id": "proj-1",
        "project_name": "adequate-luck",
    }

    outcome = run_operation_preflight(
        job_type="railway_deployments_preflight",
        params={
            "user_request": "show railway deployments for speakglobal-ai",
            "provider": "railway",
            "operation_type": "list_deployments",
            "target_hints": ["speakglobal-ai"],
        },
    )
    pf = outcome.preflight
    assert pf.read_only_execution_enabled is True
    assert pf.mutation_execution_enabled is False
    assert "**Read-only execution:** available after approval" in outcome.full_result
    assert "**Read-only execution:** not available" not in outcome.full_result


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.railway.api_client.find_service_by_name")
def test_approve_railway_deployments_preflight_creates_railway_execution_job(
    mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-rw"}
    mock_find.return_value = {
        "service_id": "svc-1",
        "service_name": "speakglobal-ai",
        "project_id": "proj-1",
        "project_name": "adequate-luck",
    }

    job_executor.drain_queue_for_tests()
    job_store.clear_for_tests()
    try:
        outcome = run_operation_preflight(
            job_type="railway_deployments_preflight",
            params={
                "user_request": "show railway deployments for speakglobal-ai",
                "provider": "railway",
                "operation_type": "list_deployments",
                "target_hints": ["speakglobal-ai"],
            },
        )
        preflight = job_store.create(
            title="Railway deployments preflight",
            job_type="railway_deployments_preflight",
            params={
                "user_request": "show railway deployments for speakglobal-ai",
                "provider": "railway",
                "operation_type": "list_deployments",
                "target_hints": ["speakglobal-ai"],
                "operation_preflight": outcome.preflight.to_dict(),
                "preflight_status": outcome.preflight.preflight_status,
                "is_current": True,
            },
            auto_run=False,
        )
        preflight.status = JobStatus.COMPLETED

        _, execution = approve_preflight_readonly_execution(preflight.id)
        assert execution.job_type == "readonly_execution"
        assert execution.params.get("provider") == "railway"
        assert execution.params.get("operation_type") == "list_deployments"
        assert execution.params.get("target_name") == "speakglobal-ai"
        assert execution.params.get("source_preflight_job_id") == preflight.id
        assert execution.params.get("auth_method_label") == "Railway API token"
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()
