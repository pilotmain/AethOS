# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.preflight import run_operation_preflight


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.github.api_client.find_repository_by_name")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_workflow_runs_preflight_execution_availability(mock_list, mock_find, mock_auth, _mock_token):
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
    assert "**Read-only execution:** available after approval" in outcome.full_result
    assert "**Read-only execution:** not available" not in outcome.full_result
