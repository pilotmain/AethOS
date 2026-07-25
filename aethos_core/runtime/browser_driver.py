# SPDX-License-Identifier: Apache-2.0
"""Playwright browser driver — headed supervised sessions only."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Protocol

from aethos_core.runtime.browser_diagnostics import (
    probe_playwright_runtime,
    validate_browser_runtime_for_execution,
)
from aethos_core.runtime.browser_runtime import (
    assert_on_browser_executor_thread,
    run_playwright_on_browser_thread,
)


@dataclass
class DriverHandle:
    """Opaque Playwright resources for one supervised session."""

    playwright: Any
    browser: Any
    context: Any
    page: Any


class BrowserDriver(Protocol):
    def is_execution_ready(self) -> bool: ...

    def get_runtime_diagnostics(self) -> dict[str, Any]: ...

    def open_url(
        self,
        url: str,
        *,
        headless: bool,
        storage_state_path: str | None = None,
    ) -> DriverHandle: ...

    def export_storage_state(self, handle: DriverHandle) -> dict[str, Any]: ...

    def close_handle(self, handle: DriverHandle) -> None: ...


class PlaywrightBrowserDriver:
    """Default driver — launches visible Chromium when headless=False."""

    def is_execution_ready(self) -> bool:
        try:
            validate_browser_runtime_for_execution()
            return True
        except Exception:
            return False

    def is_playwright_installed(self) -> bool:
        """Backward-compatible alias — means full runtime ready (package + Chromium)."""
        return self.is_execution_ready()

    def get_runtime_diagnostics(self) -> dict[str, Any]:
        return probe_playwright_runtime()

    def open_url(
        self,
        url: str,
        *,
        headless: bool,
        storage_state_path: str | None = None,
    ) -> DriverHandle:
        return run_playwright_on_browser_thread(
            lambda: self._open_url_on_browser_thread(
                url,
                headless=headless,
                storage_state_path=storage_state_path,
            ),
            timeout=120.0,
        )

    def _open_url_on_browser_thread(
        self,
        url: str,
        *,
        headless: bool,
        storage_state_path: str | None,
    ) -> DriverHandle:
        assert_on_browser_executor_thread(caller="browser_driver.open_url")
        validate_browser_runtime_for_execution()
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        try:
            browser = pw.chromium.launch(headless=headless)
            if storage_state_path:
                context = browser.new_context(storage_state=storage_state_path)
            else:
                context = browser.new_context()
            page = context.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            return DriverHandle(playwright=pw, browser=browser, context=context, page=page)
        except Exception:
            try:
                pw.stop()
            except Exception:
                pass
            raise

    def export_storage_state(self, handle: DriverHandle) -> dict[str, Any]:
        return run_playwright_on_browser_thread(
            lambda: self._export_storage_state_on_browser_thread(handle),
            timeout=60.0,
        )

    def _export_storage_state_on_browser_thread(self, handle: DriverHandle) -> dict[str, Any]:
        if handle.context is None:
            raise RuntimeError("Browser context is not available for storage export.")
        state = handle.context.storage_state()
        if not isinstance(state, dict):
            raise RuntimeError("Unexpected storage state shape from Playwright.")
        return state

    def close_handle(self, handle: DriverHandle) -> None:
        run_playwright_on_browser_thread(
            lambda: self._close_handle_on_browser_thread(handle),
            timeout=30.0,
        )

    def _close_handle_on_browser_thread(self, handle: DriverHandle) -> None:
        for obj, method in (
            (handle.page, "close"),
            (handle.context, "close"),
            (handle.browser, "close"),
            (handle.playwright, "stop"),
        ):
            if obj is None:
                continue
            try:
                getattr(obj, method)()
            except Exception:
                pass


_driver: BrowserDriver | None = None


def get_browser_driver() -> PlaywrightBrowserDriver:
    global _driver
    if _driver is None:
        _driver = PlaywrightBrowserDriver()
    return _driver


def set_browser_driver(driver: BrowserDriver | None) -> None:
    """Test hook — inject a mock driver."""
    global _driver
    _driver = driver  # type: ignore[assignment]
