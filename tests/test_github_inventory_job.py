# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.job_types import uses_github_readonly
from aethos_core.runtime.github_readonly_inspector import run_github_repositories_inventory
from aethos_core.runtime.github_readonly_jobs import infer_github_readonly_job, is_github_inventory_request


def test_github_inventory_request_detector():
    assert is_github_inventory_request("show my github repositories")
    assert is_github_inventory_request("list github repos")
    assert is_github_inventory_request("list my repos on github")
    assert not is_github_inventory_request("show github workflow runs for quotepilot")
    assert not is_github_inventory_request("show my repos")


def test_infer_github_repositories_inventory_job():
    out = infer_github_readonly_job("show my github repositories")
    assert out is not None
    _, job_type, params = out
    assert job_type == "github_repositories_inventory"
    assert params["provider"] == "github"


def test_github_inventory_job_type_registered():
    assert uses_github_readonly("github_repositories_inventory")


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_inventory_inspector_builds_report(mock_list, _mock_token):
    mock_list.return_value = {
        "ok": True,
        "repositories": [
            {
                "repo_id": 1,
                "name": "quotepilot",
                "full_name": "acme/quotepilot",
                "owner": "acme",
                "private": False,
                "default_branch": "main",
                "html_url": "https://github.com/acme/quotepilot",
                "updated_at": "2026-01-01T00:00:00Z",
            }
        ],
        "error": None,
    }
    outcome = run_github_repositories_inventory(
        credential_id="cred-1",
        user_request="show my github repositories",
    )
    assert "acme/quotepilot" in outcome.summary
    assert outcome.evidence
    assert outcome.evidence[0]["confidence"] == "confirmed"


@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.resolve_best_auth_method")
def test_chat_creates_github_inventory_job(mock_auth):
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
            json={"message": "show my github repositories", "session_id": "gh-inv"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert body["meta"]["proposed_job_type"] == "github_repositories_inventory"
        assert body["meta"]["provider"] == "github"
    finally:
        reset_credential_vault_for_tests()
        get_settings.cache_clear()
        job_executor.drain_queue_for_tests()


@patch("aethos_core.runtime.operational_memory.operational_memory.record_vercel_extraction")
@patch("aethos_core.providers.github.auth.GitHubAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_inventory_does_not_write_operational_memory(mock_list, _mock_token, mock_record):
    mock_list.return_value = {
        "ok": True,
        "repositories": [
            {
                "repo_id": 1,
                "name": "quotepilot",
                "full_name": "acme/quotepilot",
                "owner": "acme",
                "private": False,
                "default_branch": "main",
                "html_url": "",
                "updated_at": "",
            }
        ],
        "error": None,
    }
    from aethos_core.runtime.jobs import job_store

    job = job_store.create(
        title="GitHub repositories inventory",
        job_type="github_repositories_inventory",
        params={
            "user_request": "show my github repositories",
            "provider": "github",
            "credential_id": "cred-1",
            "auth_method": "api_token",
        },
        auto_run=False,
    )
    job_executor.drain_queue_for_tests()
    job_executor.enqueue(job.id)
    assert job_executor.drain_once_for_tests()
    completed = job_store.get(job.id)
    assert completed is not None
    assert completed.status.value == "completed"
    mock_record.assert_not_called()
    assert completed.params.get("github_inventory") is not None
    assert "acme/quotepilot" in (completed.result_summary or "")
    assert "vercel_inventory" not in (completed.params or {})
