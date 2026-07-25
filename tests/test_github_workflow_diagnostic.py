# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


def test_github_workflow_diagnostic_intent_detector():
    out = infer_operation_preflight_intent("why did the AethOS workflow fail")
    assert out is not None
    _, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["provider"] == "github"
    assert params["operation_type"] == "workflow_diagnostic"
    assert "AethOS" in params["target_hints"]


def test_github_workflow_diagnostic_intent_variants():
    for prompt in (
        "why did github workflow fail for AethOS",
        "why did the AethOS build fail",
        "why did the latest AethOS workflow fail",
    ):
        out = infer_operation_preflight_intent(prompt)
        assert out is not None, prompt
        assert out[1] == "operation_preflight"


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_workflow_diagnostic_preflight_available(
    mock_list, mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}
    mock_list.return_value = {
        "ok": True,
        "repositories": [{"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}],
        "error": None,
    }
    mock_find.return_value = {"name": "AethOS", "full_name": "pilotmain/AethOS", "owner": "pilotmain"}

    outcome = run_operation_preflight(
        job_type="github_workflow_diagnostic_preflight",
        params={
            "user_request": "why did the AethOS workflow fail",
            "provider": "github",
            "operation_type": "workflow_diagnostic",
            "target_hints": ["AethOS"],
        },
    )
    pf = outcome.preflight
    assert pf.target_name == "pilotmain/AethOS"
    assert pf.read_only_execution_enabled is True
    assert "Find recent failed workflow runs" in outcome.full_result
    assert "GitHub API token" in outcome.full_result


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_approve_github_workflow_diagnostic_creates_execution_job(
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
            job_type="github_workflow_diagnostic_preflight",
            params={
                "user_request": "why did the AethOS workflow fail",
                "provider": "github",
                "operation_type": "workflow_diagnostic",
                "target_hints": ["AethOS"],
            },
        )
        preflight = job_store.create(
            title="GitHub workflow diagnostic preflight",
            job_type="github_workflow_diagnostic_preflight",
            params={
                "user_request": "why did the AethOS workflow fail",
                "provider": "github",
                "operation_type": "workflow_diagnostic",
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
        assert execution.params.get("operation_type") == "workflow_diagnostic"
        assert execution.params.get("approved_actions") == ["github_api_workflow_diagnostic"]
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.operations.workflow_diagnostics_api.fetch_run_jobs")
@patch("aethos_core.providers.github.operations.workflow_diagnostics_api.fetch_workflow_runs")
def test_workflow_diagnostic_execution_with_failed_run(mock_runs, mock_jobs, _mock_token):
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
                "run_number": 7,
                "html_url": "https://github.com/pilotmain/AethOS/actions/runs/99",
            }
        ],
    }
    mock_jobs.return_value = {
        "ok": True,
        "jobs": [
            {
                "id": 1,
                "name": "test",
                "status": "completed",
                "conclusion": "failure",
                "steps": [
                    {"name": "Run tests", "status": "completed", "conclusion": "failure", "number": 3}
                ],
            }
        ],
    }

    from aethos_core.operations.execution.github_execution_runner import run_github_readonly_execution

    outcome = run_github_readonly_execution(
        params={
            "provider": "github",
            "operation_type": "workflow_diagnostic",
            "target_name": "pilotmain/AethOS",
            "approved_actions": ["github_api_workflow_diagnostic"],
            "auth_method": "api_token",
            "auth_method_label": "GitHub API token",
            "credential_id": "cred-gh",
        },
        job_id=None,
    )
    assert outcome.artifact.confidence == "confirmed"
    assert "Latest failed run" in outcome.full_result
    assert "Run tests" in outcome.full_result
    assert "Step-level log download is not implemented" in outcome.full_result
    assert "Bearer tok" not in outcome.full_result


@patch("aethos_core.providers.github.operations.workflow_diagnostics_api.fetch_workflow_runs")
def test_workflow_diagnostic_no_failed_runs(mock_runs):
    mock_runs.return_value = {
        "ok": True,
        "repository": "pilotmain/AethOS",
        "runs": [{"id": 1, "name": "CI", "status": "completed", "conclusion": "success", "run_number": 1}],
    }

    from aethos_core.providers.github.operations.workflow_diagnostics_api import fetch_workflow_diagnostic

    payload = fetch_workflow_diagnostic("tok", repository="pilotmain/AethOS")
    assert payload["ok"] is True
    assert payload["no_failed_runs"] is True
    assert payload["confidence"] == "confirmed"


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
def test_chat_creates_github_workflow_diagnostic_preflight(mock_auth):
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
            json={"message": "why did the AethOS workflow fail", "session_id": "gh-diag"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert body["meta"]["proposed_job_type"] == "operation_preflight"
        assert body["meta"]["provider"] == "github"
    finally:
        reset_credential_vault_for_tests()
        get_settings.cache_clear()
        job_executor.drain_queue_for_tests()
