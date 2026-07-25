# SPDX-License-Identifier: Apache-2.0
"""Browser automation capability status — honest supervised sessions."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.runtime.authority import authority
from aethos_core.runtime.browser_diagnostics import (
    probe_playwright_on_browser_thread,
    probe_playwright_runtime,
)
from aethos_core.runtime.browser_profile_store import store_diagnostics
from aethos_core.runtime.browser_executor import get_browser_executor_status
from aethos_core.runtime.browser_session import browser_session_store


def get_browser_runtime_diagnostics() -> dict[str, Any]:
    """Diagnostics for the active API process — launch probe on browser thread only."""
    return probe_playwright_on_browser_thread()


def get_browser_capability_status(*, probe_launch: bool = True) -> dict[str, Any]:
    """Safe capability shape for API and Mission Control."""
    s = get_settings()
    caps = authority.capabilities
    enabled = bool(caps.get("browser_automation_enabled"))
    if probe_launch:
        diag = probe_playwright_on_browser_thread()
    else:
        diag = probe_playwright_runtime(run_launch_probe=False)
    execution_ready = bool(diag["execution_ready"])
    package_ok = diag["playwright_package"] == "installed"
    chromium = diag["chromium_browser"]
    runtime_bug = bool(diag.get("runtime_bug"))
    failure_kind = str(diag.get("failure_kind") or "unknown")

    provider = s.browser_provider if enabled and execution_ready else "none"

    execution_implemented = execution_ready
    available = enabled and execution_ready

    env_var = "BROWSER_AUTOMATION_ENABLED"
    active = browser_session_store.active_session()
    profile_diag = store_diagnostics()

    if not enabled:
        foundation_label = "Off"
        execution_label = "Not available (foundation off)"
    elif runtime_bug:
        foundation_label = "Ready"
        execution_label = "AethOS runtime bug (Playwright sync/async boundary)"
    elif not package_ok:
        foundation_label = "Ready"
        execution_label = "Playwright package missing in AethOS runtime"
    elif chromium == "missing":
        foundation_label = "Ready"
        execution_label = "Chromium browser not installed for Playwright"
    elif execution_ready:
        foundation_label = "Ready"
        execution_label = "Supervised sessions available"
    else:
        foundation_label = "Ready"
        execution_label = str(diag.get("user_message") or "Playwright runtime not ready")[:120]

    return {
        "enabled": enabled,
        "available": available,
        "provider": provider if enabled else "none",
        "requires_approval": True,
        "supports_login_sessions": "supervised_only",
        "status_label": foundation_label,
        "foundation_label": foundation_label,
        "execution_label": execution_label,
        "env_var": env_var,
        "playwright_installed": execution_ready,
        "playwright_package": diag["playwright_package"],
        "chromium_browser": chromium,
        "execution_ready": execution_ready,
        "execution_implemented": execution_implemented,
        "browser_headless": s.browser_headless,
        "active_session": active.to_dict() if active else None,
        "active_session_count": browser_session_store.active_count(),
        "failure_kind": failure_kind,
        "failure_layer": diag.get("failure_layer"),
        "runtime_bug": runtime_bug,
        "user_message": diag.get("user_message"),
        "last_successful_browser_use_at": diag.get("last_successful_browser_use_at"),
        "diagnostics": diag,
        "profile_store_path": profile_diag.get("profile_store_path"),
        "saved_profile_count": profile_diag.get("profile_count", 0),
        "profile_store": profile_diag,
        "executor_status": get_browser_executor_status(),
    }
