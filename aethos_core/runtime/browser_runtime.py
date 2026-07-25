# SPDX-License-Identifier: Apache-2.0
"""Central browser runtime boundary — all sync Playwright work on the browser thread."""

from __future__ import annotations

import asyncio
import logging
import threading
import traceback
from collections.abc import Callable
from typing import Any, TypeVar

T = TypeVar("T")

_log = logging.getLogger(__name__)


class BrowserRuntimeBoundaryError(RuntimeError):
    """Sync Playwright was invoked outside the browser executor thread."""

    layer = "aethos_runtime"

    def __init__(
        self,
        message: str,
        *,
        caller: str = "",
        current_thread: str = "",
        expected_thread_id: int | None = None,
        current_thread_id: int | None = None,
    ) -> None:
        super().__init__(message)
        self.caller = caller
        self.current_thread = current_thread
        self.expected_thread_id = expected_thread_id
        self.current_thread_id = current_thread_id


def _boundary_violation_message(*, caller: str, reason: str) -> str:
    from aethos_core.runtime.browser_executor import browser_executor

    current = threading.current_thread()
    expected_tid = browser_executor.thread_id()
    current_tid = threading.get_ident()
    stack = "".join(traceback.format_stack(limit=8))
    _log.error(
        "browser_runtime_boundary_violation caller=%s reason=%s thread=%s expected_tid=%s current_tid=%s\n%s",
        caller,
        reason,
        current.name,
        expected_tid,
        current_tid,
        stack,
    )
    return (
        f"{reason} "
        f"(caller={caller or 'unknown'}, thread={current.name}, "
        f"expected_browser_thread_id={expected_tid}, current_thread_id={current_tid}). "
        "Route through run_browser_sync() / run_playwright_on_browser_thread()."
    )


def assert_not_in_asyncio_loop_for_sync_playwright(*, caller: str = "playwright") -> None:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return
    raise BrowserRuntimeBoundaryError(
        _boundary_violation_message(
            caller=caller,
            reason="Playwright Sync API must not run inside the asyncio event loop.",
        ),
        caller=caller,
        current_thread=threading.current_thread().name,
        current_thread_id=threading.get_ident(),
    )


def assert_on_browser_executor_thread(*, caller: str = "playwright") -> None:
    """Ensure sync Playwright runs only on the dedicated browser executor thread."""
    assert_not_in_asyncio_loop_for_sync_playwright(caller=caller)
    from aethos_core.runtime.browser_executor import browser_executor

    expected_tid = browser_executor.thread_id()
    current_tid = threading.get_ident()
    if expected_tid is not None and current_tid != expected_tid:
        raise BrowserRuntimeBoundaryError(
            _boundary_violation_message(
                caller=caller,
                reason="Playwright Sync API must run on the browser executor thread.",
            ),
            caller=caller,
            current_thread=threading.current_thread().name,
            expected_thread_id=expected_tid,
            current_thread_id=current_tid,
        )


def run_browser_sync(
    fn: Callable[[], T],
    *,
    timeout: float = 90.0,
    operation: str = "browser_sync",
) -> T:
    """Run callable on the dedicated browser executor thread."""
    from aethos_core.runtime.browser_diagnostics import is_browser_runtime_error
    from aethos_core.runtime.browser_executor import browser_executor, reset_browser_executor

    browser_executor.set_active_operation(operation)
    try:
        result = browser_executor.run_sync(fn, timeout=timeout)
        browser_executor.record_success()
        return result
    except BrowserRuntimeBoundaryError as exc:
        browser_executor.record_error(str(exc), operation=operation)
        reset_browser_executor()
        raise
    except Exception as exc:
        browser_executor.record_error(str(exc), operation=operation)
        if is_browser_runtime_error(exc):
            reset_browser_executor()
        raise


def run_playwright_on_browser_thread(fn: Callable[[], T], *, timeout: float = 90.0) -> T:
    """Run sync Playwright work on the browser executor thread (inline if already there)."""
    from aethos_core.runtime.browser_executor import browser_executor

    if browser_executor.is_browser_thread():
        return fn()
    return run_browser_sync(fn, timeout=timeout)


def browser_inventory_refresh_blocked_reason(*, probe_launch: bool = False) -> tuple[bool, str]:
    """Check runtime health without Playwright — preflight must pass probe_launch=False."""
    from aethos_core.config import get_settings

    if not get_settings().browser_automation_enabled:
        return False, ""
    from aethos_core.runtime.browser_capability import get_browser_capability_status

    cap = get_browser_capability_status(probe_launch=probe_launch)
    if cap.get("runtime_bug"):
        return True, (
            "Browser execution is blocked by an AethOS runtime issue "
            "(Playwright sync/async boundary). Restart the API after updating; "
            "do not run `playwright install` for this error."
        )
    if not cap.get("execution_ready"):
        msg = str(cap.get("user_message") or cap.get("execution_label") or "").strip()
        if msg:
            return True, msg
        return True, "Browser execution is not ready in the AethOS runtime."
    return False, ""


def browser_runtime_snapshot(*, probe_launch: bool = True) -> dict[str, Any]:
    from aethos_core.runtime.browser_capability import get_browser_capability_status

    return get_browser_capability_status(probe_launch=probe_launch)


def get_browser_executor_thread_id() -> int | None:
    from aethos_core.runtime.browser_executor import browser_executor

    return browser_executor.thread_id()
