# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from aethos_core.operations.target_resolution import resolve_vercel_target
from aethos_core.runtime.operational_memory import operational_memory


def test_missing_target_reports_runtime_block_when_browser_unready(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    operational_memory.clear_for_tests()
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    fake_cap = {
        "enabled": True,
        "execution_ready": False,
        "runtime_bug": True,
        "user_message": "AethOS runtime bug: Playwright Sync API was called inside the asyncio event loop.",
        "execution_label": "AethOS runtime bug (Playwright sync/async boundary)",
        "playwright_package": "installed",
        "chromium_browser": "unknown",
        "failure_kind": "sync_api_inside_asyncio_loop",
        "diagnostics": {"execution_ready": False, "runtime_bug": True},
    }
    with patch(
        "aethos_core.operations.target_resolution._api_token_available",
        return_value=False,
    ), patch(
        "aethos_core.runtime.browser_capability.get_browser_capability_status",
        return_value=fake_cap,
    ):
        res = resolve_vercel_target(
            user_request="check logs for talking-avatar-agent",
            operation_type="check_logs",
        )
    assert res.status == "blocked_by_browser_runtime"
    assert "browser execution is currently blocked" in res.message.lower()
    assert "show my vercel apps" not in res.message.lower()
