# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.providers.vercel.operations.project_details_api import (
    fetch_project_details,
    format_project_details_output,
)


def test_fetch_project_details():
    project = {"id": "prj_1", "name": "lifeos", "framework": "nextjs", "teamId": "team_1"}
    detail = {
        **project,
        "link": {"type": "github", "org": "raya", "repo": "lifeos", "productionBranch": "main"},
        "nodeVersion": "20.x",
    }
    with patch(
        "aethos_core.providers.vercel.operations.project_details_api.find_project_by_name",
        return_value=project,
    ), patch(
        "aethos_core.providers.vercel.operations.project_details_api.get_project",
        return_value=detail,
    ):
        payload = fetch_project_details("token", project_name="lifeos")
    assert payload["ok"] is True
    assert payload["details"]["framework"] == "nextjs"
    assert payload["details"]["repo_link"] == "raya/lifeos"
    out = format_project_details_output(payload)
    assert "Production branch: main" in out
