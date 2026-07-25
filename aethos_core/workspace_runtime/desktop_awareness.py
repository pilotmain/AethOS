# SPDX-License-Identifier: Apache-2.0
"""Desktop awareness — governed observation only."""

from __future__ import annotations

import platform
import subprocess
from time import time
from typing import Any

from aethos_core.workspace_runtime.workspace_artifacts import store_workspace_runtime_artifact


def observe_desktop_environment(*, capture_screenshot: bool = False) -> dict[str, Any]:
    """Governed desktop observation — no stealth surveillance."""
    windows = observe_active_windows()
    processes = observe_process_summary()
    env = {
        "platform": platform.system(),
        "platform_release": platform.release(),
        "cpu_count": _safe_cpu_count(),
        "observed_at": time(),
        "screenshot_captured": False,
        "stealth_surveillance": False,
    }
    if capture_screenshot:
        env["screenshot_captured"] = False
        env["screenshot_note"] = "Screenshot capture requires explicit user request and approval."
    snapshot = {
        "windows": windows,
        "processes": processes,
        "environment": env,
        "readonly": True,
    }
    store_workspace_runtime_artifact(
        artifact_type="workspace_environment_snapshot",
        payload=snapshot,
        summary="Desktop environment snapshot (governed observation)",
    )
    return snapshot


def observe_active_windows() -> dict[str, Any]:
    system = platform.system()
    if system == "Darwin":
        return _darwin_frontmost()
    return {"ok": True, "active_window": None, "note": f"Window detection limited on {system}"}


def observe_process_summary(*, limit: int = 12) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            ["ps", "-eo", "comm=", "-r"],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        lines = [ln.strip() for ln in (proc.stdout or "").splitlines() if ln.strip()][:limit]
        artifact = store_workspace_runtime_artifact(
            artifact_type="workspace_process_snapshot",
            payload={"processes": lines, "count": len(lines)},
            summary=f"Process summary ({len(lines)} entries)",
        )
        return {"ok": True, "processes": lines, "artifact_id": artifact.get("artifact_id")}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def _darwin_frontmost() -> dict[str, Any]:
    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
    try:
        proc = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5.0,
            check=False,
        )
        app = (proc.stdout or "").strip() or None
        payload = {"active_application": app, "platform": "Darwin"}
        artifact = store_workspace_runtime_artifact(
            artifact_type="workspace_window_snapshot",
            payload=payload,
            summary=f"Active window: {app or 'unknown'}",
        )
        return {"ok": True, "active_application": app, "artifact_id": artifact.get("artifact_id")}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def _safe_cpu_count() -> int:
    try:
        import os

        return os.cpu_count() or 0
    except (OSError, TypeError):
        return 0
