# SPDX-License-Identifier: Apache-2.0

import sys
from unittest.mock import patch

from aethos_core.runtime.browser_diagnostics import (
    probe_playwright_runtime,
    recommended_install_command,
    recommended_install_commands,
    set_playwright_runtime_override,
)


def test_recommended_install_uses_sys_executable():
    py = sys.executable
    cmds = recommended_install_commands()
    assert cmds[0] == f"{py} -m pip install playwright"
    assert cmds[1] == f"{py} -m playwright install chromium"
    assert recommended_install_command() == cmds[1]


def test_launch_probe_fields_present():
    fake = {
        "python_executable": sys.executable,
        "python_version": "3.11.0",
        "playwright_package": "installed",
        "chromium_browser": "installed",
        "launch_probe_ok": True,
        "launch_probe_error": None,
        "execution_ready": True,
        "recommended_install_command": f"{sys.executable} -m playwright install chromium",
        "recommended_install_commands": recommended_install_commands(),
    }
    set_playwright_runtime_override(fake)
    try:
        diag = probe_playwright_runtime()
    finally:
        set_playwright_runtime_override(None)
    assert diag["launch_probe_ok"] is True
    assert diag["execution_ready"] is True


def test_execution_ready_false_when_launch_probe_fails():
    fake = {
        "python_executable": sys.executable,
        "playwright_package": "installed",
        "chromium_browser": "installed",
        "launch_probe_ok": False,
        "launch_probe_error": "mock launch failed",
        "execution_ready": False,
        "recommended_install_command": f"{sys.executable} -m playwright install chromium",
    }
    set_playwright_runtime_override(fake)
    try:
        diag = probe_playwright_runtime()
    finally:
        set_playwright_runtime_override(None)
    assert diag["execution_ready"] is False
    assert "launch" in (diag.get("launch_probe_error") or "").lower()
