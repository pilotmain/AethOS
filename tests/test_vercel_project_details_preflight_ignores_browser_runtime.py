# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_status import derive_preflight_status
from aethos_core.runtime.operational_memory import operational_memory


def test_project_details_preflight_api_first():
    operational_memory.clear_for_tests()
    project = {"id": "prj_1", "name": "lifeos", "teamId": "team_1", "framework": "nextjs"}
    with patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method",
        return_value={"method": "api_token", "credential_id": "cred-1"},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.api_client.find_project_by_name",
        return_value=project,
    ):
        outcome = run_operation_preflight(
            job_type="vercel_project_details_preflight",
            params={
                "user_request": "show project details for lifeos",
                "provider": "vercel",
                "operation_type": "project_details",
                "target_hints": ["lifeos"],
            },
        )
    pf = outcome.preflight
    assert pf.target_name == "lifeos"
    assert derive_preflight_status(pf) != "blocked"
    assert pf.current_state.get("api_capable") is True
