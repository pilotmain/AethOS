# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.github.inventory.inventory_adapter import GitHubInventoryAdapter


@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_inventory_normalizes_repositories(mock_list):
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
    rows = GitHubInventoryAdapter().build_projects_inventory(auth_context={"token": "tok"})
    assert len(rows) == 1
    row = rows[0]
    assert row["provider"] == "github"
    assert row["full_name"] == "acme/quotepilot"
    assert row["owner"] == "acme"
    assert "source:github_api" in row["evidence"]


@patch("aethos_core.providers.github.api_client.list_repositories")
def test_github_inventory_api_failure_returns_empty(mock_list):
    mock_list.return_value = {"ok": False, "repositories": [], "error": "Unauthorized"}
    fetched = GitHubInventoryAdapter().fetch_projects_inventory(auth_context={"token": "tok"})
    assert fetched["ok"] is False
    assert fetched["error"] == "Unauthorized"
    assert GitHubInventoryAdapter().build_projects_inventory(auth_context={"token": "tok"}) == []


def test_github_inventory_requires_token():
    fetched = GitHubInventoryAdapter().fetch_projects_inventory(auth_context={})
    assert fetched["ok"] is False
    assert GitHubInventoryAdapter().build_projects_inventory(auth_context={}) == []
