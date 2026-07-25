# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

import pytest

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.target_resolution import resolve_vercel_target
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def vault_env(tmp_path, monkeypatch):
    monkeypatch.setenv("CREDENTIALS_DIR", str(tmp_path / "credentials"))
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    operational_memory.clear_for_tests()
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    reset_credential_vault_for_tests()
    operational_memory.clear_for_tests()
    get_settings.cache_clear()


def _browser_blocked():
    return {
        "enabled": True,
        "execution_ready": False,
        "runtime_bug": True,
        "user_message": "Playwright Sync API was called inside the asyncio event loop.",
        "execution_label": "AethOS runtime bug (Playwright sync/async boundary)",
        "playwright_package": "installed",
        "chromium_browser": "unknown",
        "failure_kind": "sync_api_inside_asyncio_loop",
        "diagnostics": {"execution_ready": False, "runtime_bug": True},
    }


def _seed_api_token(client):
    with patch(
        "aethos_core.connections.credential_validation._validate_vercel_runtime",
        return_value={"ok": True, "validation_status": "validated", "detail": "Vercel token validated."},
    ):
        client.post(
            "/api/v1/connections/vercel/credentials",
            json={"type": "api_token", "label": "Primary", "token": "vercel_test_token_abcdefgh"},
        )


def test_api_first_target_resolution_uses_provider_api(vault_env):
    project = {"id": "prj_1", "name": "invoicepilot", "teamId": "team_1", "framework": "nextjs"}
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
        res = resolve_vercel_target(
            user_request="show domains for invoicepilot",
            target_hints=["invoicepilot"],
            operation_type="list_domains",
        )
    assert res.status == "resolved"
    assert res.target_name == "invoicepilot"
    assert res.source == "provider_api"


def test_api_first_resolution_not_blocked_when_browser_broken(vault_env):
    project = {"id": "prj_1", "name": "quotepilot", "teamId": "team_1"}
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
        return_value=_browser_blocked(),
    ):
        res = resolve_vercel_target(
            user_request="show deployments for quotepilot",
            target_hints=["quotepilot"],
            operation_type="list_deployments",
        )
    assert res.status == "resolved"
    assert res.status != "blocked_by_browser_runtime"
