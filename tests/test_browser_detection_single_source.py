# SPDX-License-Identifier: Apache-2.0

import sys
from unittest.mock import patch

from aethos_core.runtime.browser_capability import get_browser_capability_status
from aethos_core.runtime.browser_diagnostics import probe_playwright_runtime, runtime_not_ready_message
from aethos_core.runtime.browser_driver import PlaywrightBrowserDriver


def test_capability_status_uses_probe_diagnostics():
    fake = {
        "python_executable": sys.executable,
        "playwright_package": "installed",
        "chromium_browser": "missing",
        "launch_probe_ok": False,
        "launch_probe_error": "no chromium",
        "execution_ready": False,
        "recommended_install_command": f"{sys.executable} -m playwright install chromium",
        "recommended_install_commands": [f"{sys.executable} -m playwright install chromium"],
    }
    with patch("aethos_core.runtime.browser_capability.probe_playwright_on_browser_thread", return_value=fake):
        status = get_browser_capability_status()
    assert status["diagnostics"]["python_executable"] == sys.executable
    assert status["execution_ready"] is False
    assert status["chromium_browser"] == "missing"


def test_runtime_message_uses_sys_executable():
    fake = {
        "playwright_package": "missing",
        "chromium_browser": "missing",
        "recommended_install_command": f"{sys.executable} -m pip install playwright",
        "recommended_install_commands": [f"{sys.executable} -m pip install playwright"],
    }
    msg = runtime_not_ready_message(fake)
    assert sys.executable in msg


def test_driver_open_url_uses_same_validation(monkeypatch):
    called = {"n": 0}

    def fake_validate():
        called["n"] += 1
        return probe_playwright_runtime()

    monkeypatch.setattr(
        "aethos_core.runtime.browser_driver.validate_browser_runtime_for_execution",
        fake_validate,
    )
    driver = PlaywrightBrowserDriver()
    try:
        driver.open_url("https://example.com", headless=True)
    except Exception:
        pass
    assert called["n"] >= 1
