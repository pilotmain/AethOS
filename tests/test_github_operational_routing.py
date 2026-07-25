# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_execution import approve_preflight_readonly_execution
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import JobStatus, job_store


def test_github_workflow_runs_intent_detector():
    out = infer_operation_preflight_intent("show workflow runs for AethOS")
    assert out is not None
    _, job_type, params = out
    assert job_type == "operation_preflight"
    assert params["provider"] == "github"
    assert params["operation_type"] == "workflow_runs"
    assert "AethOS" in params["target_hints"]


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_workflow_runs_preflight_reports_readonly_execution_available(
    mock_list, mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}
    mock_list.return_value = {
        "ok": True,
        "repositories": [
            {
                "repo_id": 1,
                "name": "AethOS",
                "full_name": "pilotmain/AethOS",
                "owner": "pilotmain",
            }
        ],
        "error": None,
    }
    mock_find.return_value = {
        "repo_id": 1,
        "name": "AethOS",
        "full_name": "pilotmain/AethOS",
        "owner": "pilotmain",
    }

    outcome = run_operation_preflight(
        job_type="github_workflow_runs_preflight",
        params={
            "user_request": "show workflow runs for AethOS",
            "provider": "github",
            "operation_type": "workflow_runs",
            "target_hints": ["AethOS"],
        },
    )
    pf = outcome.preflight
    assert pf.read_only_execution_enabled is True
    assert pf.mutation_execution_enabled is False
    assert pf.target_name == "pilotmain/AethOS"
    assert "**Read-only execution:** available after approval" in outcome.full_result


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_approve_github_workflow_runs_preflight_creates_github_execution_job(
    mock_list, mock_find, mock_auth, _mock_token
):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-gh"}
    mock_list.return_value = {
        "ok": True,
        "repositories": [
            {
                "repo_id": 1,
                "name": "AethOS",
                "full_name": "pilotmain/AethOS",
                "owner": "pilotmain",
            }
        ],
        "error": None,
    }
    mock_find.return_value = {
        "repo_id": 1,
        "name": "AethOS",
        "full_name": "pilotmain/AethOS",
        "owner": "pilotmain",
    }

    job_executor.drain_queue_for_tests()
    job_store.clear_for_tests()
    try:
        outcome = run_operation_preflight(
            job_type="github_workflow_runs_preflight",
            params={
                "user_request": "show workflow runs for AethOS",
                "provider": "github",
                "operation_type": "workflow_runs",
                "target_hints": ["AethOS"],
            },
        )
        preflight = job_store.create(
            title="GitHub workflow runs preflight",
            job_type="github_workflow_runs_preflight",
            params={
                "user_request": "show workflow runs for AethOS",
                "provider": "github",
                "operation_type": "workflow_runs",
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
        assert execution.params.get("provider") == "github"
        assert execution.params.get("operation_type") == "workflow_runs"
        assert execution.params.get("target_name") == "pilotmain/AethOS"
        assert execution.params.get("source_preflight_job_id") == preflight.id
        assert execution.params.get("auth_method_label") == "GitHub API token"
    finally:
        job_store.clear_for_tests()
        job_executor.drain_queue_for_tests()


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
def test_chat_creates_github_workflow_runs_preflight(mock_auth):
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
            json={"message": "show workflow runs for AethOS", "session_id": "gh-wf"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert body["meta"]["proposed_job_type"] == "operation_preflight"
        assert body["meta"]["provider"] == "github"
    finally:
        reset_credential_vault_for_tests()
        get_settings.cache_clear()
        job_executor.drain_queue_for_tests()
