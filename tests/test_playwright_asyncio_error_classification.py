# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.browser_diagnostics import (
    classify_playwright_error,
    runtime_not_ready_message,
    should_mark_profile_expired_from_error,
)


def test_classify_asyncio_sync_api_misuse():
    msg = "It looks like you are using Playwright Sync API inside the asyncio loop. Please use the Async API instead."
    assert classify_playwright_error(msg) == "asyncio_sync_api_misuse"


def test_runtime_message_does_not_suggest_install_for_asyncio_misuse():
    diag = {
        "playwright_package": "installed",
        "chromium_browser": "installed",
        "runtime_error_kind": "asyncio_sync_api_misuse",
        "launch_probe_error": "Sync API inside the asyncio loop",
        "recommended_install_command": "python -m playwright install chromium",
    }
    text = runtime_not_ready_message(diag)
    assert "runtime bug" in text.lower() or "runtime issue" in text.lower()
    assert "do not run" in text.lower() or "not a chromium install" in text.lower()


def test_runtime_error_does_not_expire_profile():
    exc = RuntimeError(
        "It looks like you are using Playwright Sync API inside the asyncio loop."
    )
    assert should_mark_profile_expired_from_error(exc) is False
