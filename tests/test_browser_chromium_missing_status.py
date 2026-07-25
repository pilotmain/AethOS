# SPDX-License-Identifier: Apache-2.0

import sys
from unittest.mock import patch

from aethos_core.runtime.browser_capability import get_browser_capability_status


def test_chromium_missing_distinct_label(monkeypatch):
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    from aethos_core.config import get_settings

    get_settings.cache_clear()

    fake_diag = {
        "python_executable": sys.executable,
        "playwright_import_ok": True,
        "playwright_package": "installed",
        "chromium_browser": "missing",
        "import_error": None,
        "chromium_error": "browser not found",
        "execution_ready": False,
        "install_hint": f"{sys.executable} -m pip install playwright",
        "recommended_install_commands": [
            f"{sys.executable} -m pip install playwright",
            f"{sys.executable} -m playwright install chromium",
        ],
    }

    with patch(
        "aethos_core.runtime.browser_capability.probe_playwright_on_browser_thread",
        return_value=fake_diag,
    ):
        status = get_browser_capability_status()

    assert status["playwright_package"] == "installed"
    assert status["chromium_browser"] == "missing"
    assert status["execution_ready"] is False
    assert "Chromium" in status["execution_label"]
    assert status["available"] is False

    get_settings.cache_clear()
    get_settings()
