# SPDX-License-Identifier: Apache-2.0
"""Playwright runtime diagnostics — single normalized truth; sync Playwright only on browser thread."""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path
from time import time
from typing import Any, Literal

RuntimeErrorKind = Literal[
    "ready",
    "playwright_package_missing",
    "chromium_missing",
    "launch_failed",
    "asyncio_sync_api_misuse",
    "unknown",
]

FailureKind = Literal[
    "ready",
    "sync_api_inside_asyncio_loop",
    "playwright_package_missing",
    "chromium_browser_missing",
    "launch_failed",
    "unknown",
]


class BrowserRuntimeNotReady(RuntimeError):
    """Playwright package or Chromium is not usable."""

    def __init__(
        self,
        message: str,
        *,
        layer: str = "browser_runtime",
        error_kind: RuntimeErrorKind = "unknown",
    ) -> None:
        super().__init__(message)
        self.layer = layer
        self.error_kind = error_kind


_last_successful_browser_use_at: float | None = None
_cached_success_diag: dict[str, Any] | None = None


def record_browser_operation_success() -> None:
    """Clear stale launch failures after a successful Playwright operation."""
    global _last_successful_browser_use_at, _cached_success_diag
    _last_successful_browser_use_at = time()
    py = sys.executable
    _cached_success_diag = {
        "python_executable": py,
        "python_version": sys.version.split()[0],
        "playwright_import_ok": True,
        "playwright_package": "installed",
        "playwright_version": _playwright_version(),
        "chromium_browser": "installed",
        "launch_probe_ok": True,
        "launch_probe_error": None,
        "runtime_error_kind": "ready",
        "execution_ready": True,
        "last_successful_browser_use_at": _last_successful_browser_use_at,
    }


def last_successful_browser_use_at() -> float | None:
    return _last_successful_browser_use_at


def _safe_error(message: str, *, max_len: int = 240) -> str:
    text = (message or "").strip().replace("\n", " ")
    if len(text) > max_len:
        return text[: max_len - 3] + "..."
    return text


def recommended_install_commands() -> list[str]:
    py = sys.executable
    return [
        f"{py} -m pip install playwright",
        f"{py} -m playwright install chromium",
    ]


def recommended_install_command() -> str:
    return recommended_install_commands()[-1]


def install_hint_text() -> str:
    return " && ".join(recommended_install_commands())


_runtime_override: dict[str, Any] | None = None


def set_playwright_runtime_override(diag: dict[str, Any] | None) -> None:
    global _runtime_override
    _runtime_override = diag


def classify_playwright_error(message: str) -> RuntimeErrorKind:
    low = (message or "").lower()
    if "sync api inside the asyncio loop" in low or "async api instead" in low:
        return "asyncio_sync_api_misuse"
    if "playwright" in low and ("not installed" in low or "no module" in low):
        return "playwright_package_missing"
    if "executable doesn't exist" in low or "chromium" in low and "not found" in low:
        return "chromium_missing"
    if "chromium" in low or "launch" in low:
        return "launch_failed"
    return "unknown"


def _failure_kind_from_runtime(kind: RuntimeErrorKind) -> FailureKind:
    mapping: dict[RuntimeErrorKind, FailureKind] = {
        "ready": "ready",
        "asyncio_sync_api_misuse": "sync_api_inside_asyncio_loop",
        "playwright_package_missing": "playwright_package_missing",
        "chromium_missing": "chromium_browser_missing",
        "launch_failed": "launch_failed",
        "unknown": "unknown",
    }
    return mapping.get(kind, "unknown")


def normalize_browser_diagnostics(raw: dict[str, Any]) -> dict[str, Any]:
    """Single diagnostic object for API + Mission Control."""
    err_text = str(raw.get("launch_probe_error") or raw.get("chromium_error") or "")
    if raw.get("execution_ready"):
        kind: RuntimeErrorKind = "ready"
    else:
        classified = classify_playwright_error(err_text)
        raw_kind = raw.get("runtime_error_kind")
        kind = classified if classified != "unknown" else (raw_kind or "unknown")  # type: ignore[assignment]
    failure_kind = _failure_kind_from_runtime(kind)
    execution_ready = bool(raw.get("execution_ready"))
    runtime_bug = failure_kind == "sync_api_inside_asyncio_loop"

    chromium = str(raw.get("chromium_browser") or "unknown")
    if runtime_bug:
        chromium = "unknown"

    install_cmd: str | None = None
    install_cmds: list[str] = []
    if not execution_ready and not runtime_bug:
        if failure_kind in ("playwright_package_missing", "unknown") and raw.get(
            "playwright_package"
        ) != "installed":
            install_cmds = recommended_install_commands()
            install_cmd = recommended_install_commands()[0]
        elif failure_kind == "chromium_browser_missing":
            install_cmds = [recommended_install_command()]
            install_cmd = recommended_install_command()
        elif failure_kind == "launch_failed" and "executable doesn't exist" in str(
            raw.get("launch_probe_error") or ""
        ).lower():
            install_cmds = [recommended_install_command()]
            install_cmd = recommended_install_command()

    user_message = runtime_not_ready_message(raw) if not execution_ready else (
        "Playwright runtime is ready for supervised browser sessions."
    )
    if execution_ready:
        user_message = (
            "Playwright runtime is ready for supervised browser sessions."
        )
        if _last_successful_browser_use_at:
            user_message += f" Last successful browser use: {_format_ts(_last_successful_browser_use_at)}."

    failure_layer = "aethos_runtime" if runtime_bug else "browser_runtime"
    if failure_kind == "playwright_package_missing":
        failure_layer = "python_environment"

    normalized = {
        **raw,
        "execution_ready": execution_ready,
        "failure_kind": failure_kind,
        "failure_layer": failure_layer,
        "runtime_bug": runtime_bug,
        "user_message": user_message,
        "install_command": install_cmd,
        "recommended_install_command": install_cmd,
        "recommended_install_commands": install_cmds,
        "install_hint": " && ".join(install_cmds) if install_cmds else None,
        "chromium_browser": chromium,
        "playwright_package": raw.get("playwright_package", "unknown"),
        "runtime_python": raw.get("python_executable"),
        "last_successful_browser_use_at": _last_successful_browser_use_at,
    }
    return normalized


def _format_ts(ts: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _playwright_version() -> str | None:
    try:
        from importlib.metadata import version

        return version("playwright")
    except Exception:
        return None


def _probe_import_only() -> dict[str, Any]:
    """Safe on any thread — no sync_playwright()."""
    py = sys.executable
    browsers_env = os.environ.get("PLAYWRIGHT_BROWSERS_PATH") or ""
    diag: dict[str, Any] = {
        "python_executable": py,
        "python_version": sys.version.split()[0],
        "playwright_import_ok": False,
        "playwright_package": "missing",
        "playwright_version": None,
        "chromium_browser": "unknown",
        "import_error": None,
        "chromium_error": None,
        "browser_cache_path": browsers_env or None,
        "playwright_browsers_path_env": browsers_env or None,
        "chromium_executable_path": None,
        "launch_probe_ok": False,
        "launch_probe_error": None,
        "runtime_error_kind": "playwright_package_missing",
        "execution_ready": False,
        "probe_thread": threading.current_thread().name,
    }
    try:
        import playwright  # noqa: F401

        diag["playwright_import_ok"] = True
        diag["playwright_package"] = "installed"
        diag["playwright_version"] = _playwright_version()
        diag["runtime_error_kind"] = "unknown"
    except Exception as exc:
        diag["import_error"] = _safe_error(str(exc))
    return normalize_browser_diagnostics(diag)


def _probe_launch_on_current_thread() -> dict[str, Any]:
    """Must run only on the dedicated browser executor thread."""
    from aethos_core.runtime.browser_runtime import assert_on_browser_executor_thread

    assert_on_browser_executor_thread(caller="browser_diagnostics.launch_probe")
    diag = _probe_import_only()
    if diag["playwright_package"] != "installed":
        return diag

    try:
        from playwright.sync_api import sync_playwright

        pw = sync_playwright().start()
        try:
            exe = pw.chromium.executable_path
            diag["chromium_executable_path"] = exe
            if exe and Path(exe).is_file():
                diag["chromium_browser"] = "installed"
                if not diag.get("browser_cache_path"):
                    diag["browser_cache_path"] = str(Path(exe).parent.parent)
            else:
                diag["chromium_browser"] = "missing"
                diag["chromium_error"] = "Chromium executable not found on disk for this runtime."
            browser = pw.chromium.launch(headless=True, timeout=20_000)
            browser.close()
            diag["launch_probe_ok"] = True
            diag["launch_probe_error"] = None
            diag["runtime_error_kind"] = "ready"
            diag["execution_ready"] = True
        except Exception as exc:
            err = _safe_error(str(exc))
            kind = classify_playwright_error(err)
            diag["launch_probe_ok"] = False
            diag["launch_probe_error"] = err
            diag["runtime_error_kind"] = kind
            diag["execution_ready"] = False
            if kind == "asyncio_sync_api_misuse":
                diag["chromium_browser"] = "unknown"
                diag["chromium_error"] = None
            elif kind == "chromium_missing":
                diag["chromium_browser"] = "missing"
                diag["chromium_error"] = err
            else:
                diag["chromium_error"] = err
        finally:
            pw.stop()
    except Exception as exc:
        err = _safe_error(str(exc))
        kind = classify_playwright_error(err)
        diag["launch_probe_ok"] = False
        diag["launch_probe_error"] = err
        diag["runtime_error_kind"] = kind
        diag["execution_ready"] = False
        if kind == "asyncio_sync_api_misuse":
            diag["chromium_browser"] = "unknown"

    return normalize_browser_diagnostics(diag)


def clear_browser_diagnostics_cache_for_tests() -> None:
    global _cached_success_diag, _last_successful_browser_use_at
    _cached_success_diag = None
    _last_successful_browser_use_at = None


def probe_playwright_runtime(*, run_launch_probe: bool = False) -> dict[str, Any]:
    if _runtime_override is not None:
        return normalize_browser_diagnostics(dict(_runtime_override))

    if _cached_success_diag and _last_successful_browser_use_at:
        return normalize_browser_diagnostics(dict(_cached_success_diag))

    if not run_launch_probe:
        return _probe_import_only()

    from aethos_core.runtime.browser_executor import browser_executor

    if threading.current_thread() is browser_executor._thread:
        return _probe_launch_on_current_thread()
    return probe_playwright_on_browser_thread()


def probe_playwright_on_browser_thread(*, timeout: float = 45.0) -> dict[str, Any]:
    if _runtime_override is not None:
        return normalize_browser_diagnostics(dict(_runtime_override))

    if _cached_success_diag and _last_successful_browser_use_at:
        return normalize_browser_diagnostics(dict(_cached_success_diag))

    from aethos_core.runtime.browser_runtime import run_browser_sync

    raw = run_browser_sync(_probe_launch_on_current_thread, timeout=timeout)
    return raw


def runtime_not_ready_message(diag: dict[str, Any] | None = None) -> str:
    d = diag or probe_playwright_on_browser_thread()
    if d.get("user_message") and d.get("execution_ready"):
        return str(d["user_message"])
    kind = d.get("failure_kind") or d.get("runtime_error_kind") or "unknown"
    if kind in ("sync_api_inside_asyncio_loop", "asyncio_sync_api_misuse"):
        return (
            "AethOS runtime bug: Playwright Sync API was called inside the asyncio event loop. "
            "Restart the API after updating; do not run `playwright install` for this error."
        )
    if kind == "playwright_package_missing" or d.get("playwright_package") != "installed":
        cmd = d.get("install_command") or recommended_install_command()
        return (
            "Playwright package is not installed in the AethOS runtime environment. "
            f"Use: {cmd}"
        )
    if kind == "chromium_browser_missing" or d.get("chromium_browser") == "missing":
        cmd = d.get("install_command") or recommended_install_command()
        return (
            "Chromium browser is not installed for Playwright in the AethOS runtime environment. "
            f"Use: {cmd}"
        )
    if d.get("launch_probe_error"):
        return (
            "Chromium could not be launched in the AethOS runtime environment. "
            f"{d['launch_probe_error']}"
        )
    return str(d.get("user_message") or "Playwright runtime is not ready.")


def validate_browser_runtime_for_execution() -> dict[str, Any]:
    diag = probe_playwright_on_browser_thread()
    if not diag.get("execution_ready"):
        kind = diag.get("failure_kind") or diag.get("runtime_error_kind") or "unknown"
        raise BrowserRuntimeNotReady(
            runtime_not_ready_message(diag),
            error_kind=kind if isinstance(kind, str) else "unknown",  # type: ignore[arg-type]
        )
    return diag


def is_browser_runtime_error(exc: BaseException) -> bool:
    from aethos_core.runtime.browser_runtime import BrowserRuntimeBoundaryError

    if isinstance(exc, BrowserRuntimeBoundaryError):
        return True
    if isinstance(exc, BrowserRuntimeNotReady):
        return True
    msg = str(exc).lower()
    if classify_playwright_error(msg) == "asyncio_sync_api_misuse":
        return True
    return (
        "playwright" in msg
        or "chromium" in msg
        or "browser is not installed" in msg
        or "runtime environment" in msg
        or "browser runtime bug" in msg
        or "aethos runtime bug" in msg
    )


def should_mark_profile_expired_from_error(exc: BaseException) -> bool:
    if is_browser_runtime_error(exc):
        return False
    if isinstance(exc, BrowserRuntimeNotReady):
        return False
    msg = str(exc).lower()
    if "runtime" in msg or "playwright" in msg or "chromium" in msg:
        return False
    return any(
        token in msg
        for token in (
            "expired",
            "not logged",
            "login_wall",
            "login wall",
            "not active",
            "missing on disk",
            "revoked",
        )
    )
