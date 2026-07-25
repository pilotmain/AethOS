# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_diagnostics import (
    classify_playwright_error,
    normalize_browser_diagnostics,
)


def test_asyncio_misuse_precedence_over_chromium_missing():
    raw = {
        "playwright_package": "installed",
        "chromium_browser": "missing",
        "launch_probe_ok": False,
        "launch_probe_error": (
            "It looks like you are using Playwright Sync API inside the asyncio loop."
        ),
        "runtime_error_kind": "asyncio_sync_api_misuse",
        "execution_ready": False,
        "python_executable": "/usr/bin/python3",
    }
    norm = normalize_browser_diagnostics(raw)
    assert norm["failure_kind"] == "sync_api_inside_asyncio_loop"
    assert norm["chromium_browser"] == "unknown"
    assert norm["install_command"] is None
    assert norm["runtime_bug"] is True
    assert classify_playwright_error(norm["launch_probe_error"]) == "asyncio_sync_api_misuse"
