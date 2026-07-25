# SPDX-License-Identifier: Apache-2.0
"""Browser observation runtime diagnostic reply tests."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.browser_observation.browser_observation_diagnostics import (
    format_browser_observation_blocked_reply,
    inspect_browser_observation_runtime,
)
from aethos_core.browser_observation.browser_observation_router import (
    compose_browser_blocked_reply,
    route_browser_observation,
)
from aethos_core.config import get_settings


def _blocked_diag() -> dict:
    return {
        "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
        "ignored_env_vars": ["PLAYWRIGHT_ENABLED", "BROWSER_ENABLED"],
        "env_flag_loaded": True,
        "env_raw_process_value": "true",
        "settings_value": True,
        "playwright_python_package_installed": True,
        "chromium_binary_installed": False,
        "browser_launch_test": "fail (Chromium executable not found)",
        "worker_enabled": True,
        "execution_ready": False,
        "python_executable": "/usr/bin/python3",
        "playwright_version": "1.49.0",
        "recommended_install_commands": ["/usr/bin/python3 -m playwright install chromium"],
        "remediation_notes": ["Restart the AethOS API after changing `.env`."],
    }


def test_blocked_reply_lists_subchecks() -> None:
    body = format_browser_observation_blocked_reply(_blocked_diag())
    assert "Runtime checks (this API process):" in body
    assert "env flag loaded (`BROWSER_AUTOMATION_ENABLED`): yes" in body
    assert "playwright python package installed: yes" in body
    assert "chromium binary installed: no" in body
    assert "browser launch test: fail" in body
    assert "worker enabled: yes" in body
    assert "PLAYWRIGHT_ENABLED" in body
    assert "Playwright runtime unavailable" not in body
    assert "How I can help" not in body


@patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
@patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=False)
def test_route_uses_detailed_blocker(_ready, mock_inspect) -> None:
    mock_inspect.return_value = _blocked_diag()
    result = route_browser_observation("take a screenshot of pilotmain.com", session_id="diag-route")
    assert result is not None
    body, intent, _meta = result
    assert intent == "browser_observation_blocked"
    assert "chromium binary installed: no" in body


def test_inspect_reports_canonical_env_var(monkeypatch) -> None:
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    get_settings.cache_clear()
    diag = inspect_browser_observation_runtime(probe_launch=False)
    assert diag["canonical_env_var"] == "BROWSER_AUTOMATION_ENABLED"
    assert "env_flag_loaded" in diag
    assert "playwright_python_package_installed" in diag
    get_settings.cache_clear()
