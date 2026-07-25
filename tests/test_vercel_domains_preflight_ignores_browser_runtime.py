# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_status import derive_preflight_status
from aethos_core.runtime.operational_memory import operational_memory


def test_domains_preflight_ready_when_browser_blocked_but_api_token_present():
    operational_memory.clear_for_tests()
    project = {"id": "prj_1", "name": "invoicepilot", "teamId": "team_1"}
    with patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method",
        return_value={"method": "api_token", "credential_id": "cred-1"},
    ), patch(
        "aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token",
        return_value="token",
    ), patch(
        "aethos_core.providers.vercel.api_client.find_project_by_name",
        return_value=project,
    ), patch(
        "aethos_core.runtime.browser_capability.get_browser_capability_status",
        return_value={
            "enabled": True,
            "execution_ready": False,
            "runtime_bug": True,
            "user_message": "Playwright blocked",
            "execution_label": "runtime bug",
            "playwright_package": "installed",
            "chromium_browser": "unknown",
            "failure_kind": "sync_api_inside_asyncio_loop",
            "diagnostics": {},
        },
    ):
        outcome = run_operation_preflight(
            job_type="vercel_domains_preflight",
            params={
                "user_request": "show domains for invoicepilot",
                "provider": "vercel",
                "operation_type": "list_domains",
                "target_hints": ["invoicepilot"],
            },
        )
    pf = outcome.preflight
    status = derive_preflight_status(pf)
    assert status in ("ready_for_approval", "ready_for_readonly_diagnostic")
    assert status != "blocked"
    assert pf.current_state.get("api_capable") is True
    assert pf.current_state.get("browser_runtime_required") is False
    assert "browser runtime is fixed" not in outcome.summary.lower()
