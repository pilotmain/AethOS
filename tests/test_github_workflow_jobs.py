# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


def test_github_workflow_jobs_intent_detector():
    out = infer_operation_preflight_intent("show failed workflow jobs for AethOS")
    assert out is not None
    _, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["provider"] == "github"
    assert params["operation_type"] == "workflow_jobs"
    assert "AethOS" in params["target_hints"]


def test_github_workflow_jobs_intent_variants():
    for prompt in (
        "show github failed jobs for AethOS",
        "show workflow job failures for AethOS",
        "show GitHub workflow logs for AethOS",
    ):
        out = infer_operation_preflight_intent(prompt)
        assert out is not None, prompt
        assert out[1] == "operation_preflight"


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_workflow_jobs_preflight_available(mock_list, mock_find, mock_auth, _mock_token):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}
    mock_list.return_value = {
        "ok": True,
        "repositories": [{"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}],
        "error": None,
    }
    mock_find.return_value = {"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}

    outcome = run_operation_preflight(
        job_type="github_workflow_jobs_preflight",
        params={
            "user_request": "show failed workflow jobs for AethOS",
            "provider": "github",
            "operation_type": "workflow_jobs",
            "target_hints": ["AethOS"],
        },
    )
    pf = outcome.preflight
    assert pf.target_name == "pilotmain/AethOS"
    assert pf.read_only_execution_enabled is True
    assert "Collect failed job and step metadata" in outcome.full_result
    assert "GitHub API token" in outcome.full_result


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_approve_github_workflow_jobs_preflight_creates_execution_job(
    mock_list, mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}
    mock_list.return_value = {
        "ok": True,
        "repositories": [{"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}],
        "error": None,
    }
    mock_find.return_value = {"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}

    job_executor.drain_queue_for_tests()
    job_store.clear_for_tests()
    try:
        outcome = run_operation_preflight(
            job_type="github_workflow_jobs_preflight",
            params={
                "user_request": "show failed workflow jobs for AethOS",
                "provider": "github",
                "operation_type": "workflow_jobs",
                "target_hints": ["AethOS"],
            },
        )
        preflight = job_store.create(
            title="GitHub workflow jobs preflight",
            job_type="github_workflow_jobs_preflight",
            params={
                "user_request": "show failed workflow jobs for AethOS",
                "provider": "github",
                "operation_type": "workflow_jobs",
                "target_hints": ["AethOS"],
                "operation_preflight": outcome.preflight.to_dict(),
                "preflight_status": outcome.preflight.preflight_status,
                "is_current": True,
            },
            auto_run=False,
        )
        preflight.status = JobStatus.COMPLETED

        _, execution = approve_preflight_readonly_execution(preflight.id)
        assert execution.job_type == "readonly_execution"
        assert execution.params.get("operation_type") == "workflow_jobs"
        assert execution.params.get("approved_actions") == ["github_api_workflow_jobs"]
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()


@patch("aethos_core.providers.github.operations.workflow_jobs_api.fetch_run_jobs")
@patch("aethos_core.providers.github.operations.workflow_jobs_api.fetch_workflow_runs")
def test_workflow_jobs_execution_with_failed_jobs(mock_runs, mock_jobs):
    mock_runs.return_value = {
        "ok": True,
        "repository": "pilotmain/AethOS",
        "runs": [
            {
                "id": 99,
                "name": "CI",
                "status": "completed",
                "conclusion": "failure",
                "event": "push",
                "head_branch": "main",
                "head_sha": "abc123def456",
                "run_number": 123,
            }
        ],
    }
    mock_jobs.return_value = {
        "ok": True,
        "jobs": [
            {
                "id": 1,
                "name": "backend-tests",
                "status": "completed",
                "conclusion": "failure",
                "html_url": "https://github.com/pilotmain/AethOS/actions/jobs/1",
                "steps": [{"name": "Run pytest", "status": "completed", "conclusion": "failure", "number": 3}],
            },
            {
                "id": 2,
                "name": "frontend-tests",
                "status": "completed",
                "conclusion": "failure",
                "html_url": "https://github.com/pilotmain/AethOS/actions/jobs/2",
                "steps": [{"name": "npm test", "status": "completed", "conclusion": "failure", "number": 2}],
            },
        ],
    }

    from aethos_core.operations.execution.github_execution_runner import run_github_readonly_execution

    with patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok"):
        outcome = run_github_readonly_execution(
        params={
            "provider": "github",
            "operation_type": "workflow_jobs",
            "target_name": "pilotmain/AethOS",
            "approved_actions": ["github_api_workflow_jobs"],
            "auth_method": "api_token",
            "auth_method_label": "GitHub API token",
            "credential_id": "cred-gh",
        },
        job_id=None,
        )
    assert outcome.artifact.confidence == "confirmed"
    assert "backend-tests" in outcome.full_result
    assert "Run pytest" in outcome.full_result
    assert "Raw workflow log download is not implemented" in outcome.full_result
    assert "Bearer tok" not in outcome.full_result


@patch("aethos_core.providers.github.operations.workflow_jobs_api.fetch_workflow_runs")
def test_workflow_jobs_no_failed_runs(mock_runs):
    mock_runs.return_value = {
        "ok": True,
        "repository": "pilotmain/AethOS",
        "runs": [{"id": 1, "name": "CI", "status": "completed", "conclusion": "success", "run_number": 1}],
    }

    from aethos_core.providers.github.operations.workflow_jobs_api import fetch_workflow_jobs

    payload = fetch_workflow_jobs("tok", repository="pilotmain/AethOS")
    assert payload["ok"] is True
    assert payload["no_failed_jobs"] is True


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
def test_chat_creates_github_workflow_jobs_preflight(mock_auth):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}

    from aethos_core.api.main import app
    from aethos_core.config import get_settings
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    get_settings.cache_clear()
    job_executor.drain_queue_for_tests()
    try:
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show failed workflow jobs for AethOS", "session_id": "gh-jobs"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert body["meta"]["proposed_job_type"] == "operation_preflight"
        assert body["meta"]["provider"] == "github"
    finally:
        reset_credential_vault_for_tests()
        get_settings.cache_clear()
        job_executor.drain_queue_for_tests()
