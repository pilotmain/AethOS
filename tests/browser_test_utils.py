# SPDX-License-Identifier: Apache-2.0
"""Mocks for supervised browser session tests — no real Chromium in CI."""

from __future__ import annotations

import os
from typing import Any

import sys

from aethos_core.runtime.browser_diagnostics import (
    install_hint_text,
    recommended_install_commands,
    set_playwright_runtime_override,
)
from aethos_core.runtime.browser_driver import DriverHandle, set_browser_driver
from aethos_core.runtime.browser_session import browser_session_store


class _MockLink:
    def __init__(self, href: str, text: str = "") -> None:
        self._href = href
        self._text = text

    def get_attribute(self, name: str) -> str | None:
        if name == "href":
            return self._href
        return None

    def inner_text(self, timeout: float | None = None) -> str:
        return self._text


class _MockLocator:
    def __init__(self, page: "_MockPage", *, links: list[_MockLink] | None = None) -> None:
        self._page = page
        self._links = links or []

    def count(self) -> int:
        return len(self._links)

    def nth(self, index: int) -> _MockLink:
        return self._links[index]

    def inner_text(self, timeout: float | None = None) -> str:
        return self._page._body_text


class _MockPage:
    def __init__(
        self,
        url: str = "https://vercel.com/dashboard",
        *,
        body_text: str = "Projects\n",
        title: str = "Vercel",
        project_hrefs: list[tuple[str, str]] | None = None,
    ) -> None:
        self.url = url
        self._body_text = body_text
        self._title = title
        if project_hrefs is None:
            hrefs = [
                ("https://vercel.com/raya-team/my-app", "my-app"),
                ("https://vercel.com/raya-team/api-service", "api-service"),
                ("https://vercel.com/raya-team/invoicepilot", "invoicepilot"),
            ]
        else:
            hrefs = project_hrefs
        self._links = [_MockLink(h, t) for h, t in hrefs]
        if body_text == "Projects\n" and hrefs:
            self._body_text = body_text + "\n".join(t for _, t in hrefs)

    def title(self) -> str:
        return self._title

    def locator(self, selector: str) -> _MockLocator:
        if "body" in selector:
            return _MockLocator(self)
        return _MockLocator(self, links=self._links)

    def get_by_text(self, text: str, exact: bool = False) -> "_MockTextLocator":
        return _MockTextLocator(self, text)

    def wait_for_selector(self, selector: str, timeout: float | None = None) -> None:
        return None

    def inner_text(self, selector: str) -> str:
        return self._body_text


class _MockTextLocator:
    def __init__(self, page: _MockPage, text: str) -> None:
        self._page = page
        self._text = text

    @property
    def first(self) -> "_MockTextLocator":
        return self

    def wait_for(self, state: str = "visible", timeout: float | None = None) -> None:
        if self._text.lower() in self._page._body_text.lower():
            return None
        raise TimeoutError(self._text)


class MockBrowserDriver:
    def __init__(self, *, installed: bool = True, should_fail: bool = False) -> None:
        self.installed = installed
        self.should_fail = should_fail
        self.opened_urls: list[str] = []
        self.closed_count = 0

    def is_execution_ready(self) -> bool:
        return self.installed

    def is_playwright_installed(self) -> bool:
        return self.installed

    def get_runtime_diagnostics(self) -> dict:
        from aethos_core.runtime.browser_diagnostics import probe_playwright_runtime

        if self.installed:
            d = probe_playwright_runtime()
            return {
                **d,
                "playwright_package": "installed",
                "chromium_browser": "installed",
                "execution_ready": True,
                "playwright_import_ok": True,
            }
        return {
            **probe_playwright_runtime(),
            "playwright_package": "missing",
            "chromium_browser": "missing",
            "execution_ready": False,
            "playwright_import_ok": False,
        }

    def open_url(
        self,
        url: str,
        *,
        headless: bool,
        storage_state_path: str | None = None,
    ) -> DriverHandle:
        if not self.installed:
            raise RuntimeError(
                "Playwright package is not installed in the AethOS runtime environment."
            )
        if self.should_fail:
            raise RuntimeError("Mock browser launch failed.")
        self.opened_urls.append(url)
        if storage_state_path:
            self.opened_urls.append(f"storage:{storage_state_path}")
        page = _MockPage(url=url)
        return DriverHandle(playwright=object(), browser=object(), context=object(), page=page)

    def export_storage_state(self, handle: DriverHandle) -> dict:
        return {"cookies": [], "origins": [], "mock": True}

    def close_handle(self, handle: DriverHandle) -> None:
        self.closed_count += 1


def _refresh_settings_from_env() -> None:
    from aethos_core.config import get_settings

    get_settings.cache_clear()
    get_settings()


def _diag_for_mock(*, installed: bool) -> dict:
    base = {
        "python_executable": sys.executable,
        "install_hint": install_hint_text(),
        "recommended_install_commands": recommended_install_commands(),
        "import_error": None,
        "chromium_error": None,
    }
    if installed:
        return {
            **base,
            "python_version": "3.11.0",
            "playwright_import_ok": True,
            "playwright_package": "installed",
            "playwright_version": "1.49.0",
            "chromium_browser": "installed",
            "launch_probe_ok": True,
            "launch_probe_error": None,
            "browser_cache_path": "/tmp/mock-browsers",
            "chromium_executable_path": "/tmp/mock-browsers/chromium",
            "recommended_install_command": f"{base['python_executable']} -m playwright install chromium",
            "execution_ready": True,
        }
    return {
        **base,
        "python_version": "3.11.0",
        "playwright_import_ok": False,
        "playwright_package": "missing",
        "chromium_browser": "missing",
        "launch_probe_ok": False,
        "import_error": "mock: package missing",
        "execution_ready": False,
        "recommended_install_command": f"{base['python_executable']} -m playwright install chromium",
    }


def use_mock_browser_driver(**kwargs: Any) -> MockBrowserDriver:
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    mock = MockBrowserDriver(**kwargs)
    set_browser_driver(mock)
    set_playwright_runtime_override(_diag_for_mock(installed=mock.installed))
    browser_session_store.close_all()
    browser_session_store._sessions.clear()
    from aethos_core.runtime.browser_profile_store import browser_profile_store

    browser_profile_store.clear_all_for_tests()
    _refresh_settings_from_env()
    return mock


def drain_browser_executor() -> None:
    from aethos_core.runtime.browser_executor import browser_executor

    while browser_executor.drain_sync_for_tests():
        pass
    while browser_executor.drain_once_for_tests():
        pass


def reset_browser_test_state() -> None:
    os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
    set_browser_driver(None)
    set_playwright_runtime_override(None)
    from aethos_core.runtime.browser_diagnostics import clear_browser_diagnostics_cache_for_tests

    clear_browser_diagnostics_cache_for_tests()
    from aethos_core.runtime.browser_executor import browser_executor

    browser_executor.drain_queue_for_tests()
    browser_session_store.close_all()
    browser_session_store._sessions.clear()
    with browser_session_store._lock:
        browser_session_store._events.clear()
    from aethos_core.runtime.browser_profile_store import browser_profile_store

    browser_profile_store.clear_all_for_tests()
    from aethos_core.security.credential_vault import get_credential_vault, reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    get_credential_vault().clear_all_for_tests()
    reset_credential_vault_for_tests()
    _refresh_settings_from_env()
