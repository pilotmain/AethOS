# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.vercel.operations.domains_api import fetch_domains, format_domains_output


def test_fetch_domains_includes_api_and_alias():
    project = {
        "id": "prj_1",
        "name": "invoicepilot",
        "teamId": "team_1",
        "targets": {"production": {"alias": ["invoicepilot.com"]}},
    }
    with patch(
        "aethos_core.providers.vercel.operations.domains_api.find_project_by_name",
        return_value=project,
    ), patch(
        "aethos_core.providers.vercel.operations.domains_api.list_project_domains",
        return_value=[{"name": "invoicepilot.com", "verified": True, "production": True}],
    ):
        payload = fetch_domains("token", project_name="invoicepilot")
    assert payload["ok"] is True
    domains = [d["domain"] for d in payload["domains"]]
    assert "invoicepilot.com" in domains
    assert "invoicepilot.vercel.app" in domains
    out = format_domains_output(payload)
    assert "verified" in out
