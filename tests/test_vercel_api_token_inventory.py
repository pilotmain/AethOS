# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.vercel.inventory_api import build_inventory_from_api


SAMPLE_PROJECT = {
    "id": "prj_abc123",
    "name": "invoicepilot",
    "accountId": "team_1",
    "framework": "nextjs",
    "createdAt": 1700000000000,
    "updatedAt": 1700001000000,
    "link": {"type": "github", "org": "acme", "repo": "invoicepilot"},
    "targets": {"production": {"alias": ["invoicepilot.vercel.app"]}},
    "latestDeployments": [
        {"target": "production", "readyState": "READY", "url": "invoicepilot.vercel.app"},
        {"target": "preview", "readyState": "READY"},
    ],
}


def test_vercel_api_token_inventory_enriched_model():
    with patch(
        "aethos_core.providers.vercel.inventory_api.list_projects",
        return_value=[SAMPLE_PROJECT],
    ):
        artifact = build_inventory_from_api("vercel_test_token_1234567890")
    assert artifact.extraction_method == "vercel_api"
    assert len(artifact.projects) == 1
    project = artifact.projects[0]
    assert project.name == "invoicepilot"
    assert project.production_url == "invoicepilot.vercel.app"
    assert project.git_repo == "acme/invoicepilot"
    api_records = artifact.extraction_debug.get("api_projects") or []
    assert api_records[0]["id"] == "prj_abc123"
    assert api_records[0]["framework"] == "nextjs"
    assert "production" in api_records[0]["targets"]
