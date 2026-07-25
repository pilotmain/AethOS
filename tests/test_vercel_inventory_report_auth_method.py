# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.vercel.inventory_api import build_api_inventory_report


def test_inventory_report_shows_api_auth_header_fields():
    sample = {
        "id": "prj_1",
        "name": "demo",
        "latestDeployments": [{"target": "production", "readyState": "READY"}],
    }
    with patch(
        "aethos_core.providers.vercel.inventory_api.list_projects",
        return_value=[sample],
    ):
        _artifact, _summary, full = build_api_inventory_report(
            "vercel_test_token_1234567890",
            title="Vercel projects inventory",
            job_type="vercel_projects_inventory",
            credential_id="cred-test",
        )
    assert "**Auth method:** Vercel API token" in full
    assert "**Credential:** `cred-test (masked)`" in full
    assert "**Browser used:** no" in full
    assert "**Provider used:** none" in full
