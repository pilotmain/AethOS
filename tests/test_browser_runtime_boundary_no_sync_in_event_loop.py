# SPDX-License-Identifier: Apache-2.0

import asyncio
import inspect

import pytest

from aethos_core.runtime.browser_diagnostics import clear_browser_diagnostics_cache_for_tests, set_playwright_runtime_override
from aethos_core.runtime.browser_diagnostics import probe_playwright_on_browser_thread
from aethos_core.runtime.browser_executor import browser_executor
from aethos_core.runtime.browser_runtime import (
    BrowserRuntimeBoundaryError,
    assert_not_in_asyncio_loop_for_sync_playwright,
    get_browser_executor_thread_id,
    run_browser_sync,
)


@pytest.fixture(autouse=True)
def _browser_runtime_test_cleanup():
    yield
    browser_executor.drain_queue_for_tests()
    clear_browser_diagnostics_cache_for_tests()
    set_playwright_runtime_override(None)


def test_launch_probe_uses_run_browser_sync():
    src = inspect.getsource(probe_playwright_on_browser_thread)
    assert "run_browser_sync" in src


def test_assert_not_in_asyncio_loop_raises_inside_loop():
    async def _inner():
        with pytest.raises(BrowserRuntimeBoundaryError):
            assert_not_in_asyncio_loop_for_sync_playwright()

    asyncio.run(_inner())


def test_run_browser_sync_from_asyncio_context():
    browser_executor.start()
    try:
        seen: list[str] = []

        async def _inner():
            seen.append(
                run_browser_sync(
                    lambda: __import__("threading").current_thread().name,
                    timeout=5.0,
                )
            )

        asyncio.run(_inner())
        assert seen == ["aethos-browser-executor"]
        assert get_browser_executor_thread_id() is not None
    finally:
        browser_executor.stop()


def test_probe_from_asyncio_event_loop():
    browser_executor.start()
    try:
        from aethos_core.runtime.browser_diagnostics import clear_browser_diagnostics_cache_for_tests

        clear_browser_diagnostics_cache_for_tests()

        async def _inner():
            diag = probe_playwright_on_browser_thread()
            assert diag.get("failure_kind") != "sync_api_inside_asyncio_loop"
            assert "sync api inside the asyncio loop" not in str(
                diag.get("launch_probe_error") or ""
            ).lower()

        asyncio.run(_inner())
    finally:
        browser_executor.stop()
