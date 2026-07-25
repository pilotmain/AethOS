# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.vercel.api_client import parse_deployment_record, parse_domain_record
from aethos_core.providers.vercel.operations.deployments_api import fetch_deployments, format_deployments_output


def test_parse_deployment_record_fields():
    rec = parse_deployment_record(
        {
            "uid": "dpl_abc123",
            "readyState": "ERROR",
            "target": "production",
            "meta": {"githubCommitRef": "main", "githubCommitSha": "abc123def456"},
            "createdAt": 1,
            "errorMessage": "Build failed",
        }
    )
    assert rec["id"] == "dpl_abc123"
    assert rec["state"] == "error"
    assert rec["target"] == "production"
    assert rec["branch"] == "main"
    assert rec["error_message"] == "Build failed"


def test_fetch_deployments_via_api():
    project = {"id": "prj_1", "name": "quotepilot", "teamId": "team_1"}
    deployments = [{"uid": "dpl_1", "readyState": "READY", "target": "production", "meta": {}}]
    with patch(
        "aethos_core.providers.vercel.operations.deployments_api.find_project_by_name",
        return_value=project,
    ), patch(
        "aethos_core.providers.vercel.operations.deployments_api.list_deployments",
        return_value=deployments,
    ):
        payload = fetch_deployments("token", project_name="quotepilot")
    assert payload["ok"] is True
    assert payload["source"] == "provider_api"
    assert payload["deployment_count"] == 1
    out = format_deployments_output(payload)
    assert "quotepilot" in out
    assert "ready" in out.lower()


def test_parse_domain_record():
    rec = parse_domain_record({"name": "app.example.com", "verified": True, "production": True})
    assert rec["domain"] == "app.example.com"
    assert rec["verified"] is True
