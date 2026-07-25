# SPDX-License-Identifier: Apache-2.0
"""Application adapters — governed local integration."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def open_in_application(*, app: str, path: str | None = None, workspace_hint: str | None = None) -> dict[str, Any]:
    """Open workspace in governed application adapter — proposal only."""
    app_lower = app.lower()
    if app_lower in ("vscode", "code"):
        return _open_vscode(path, workspace_hint)
    if app_lower == "cursor":
        return _open_cursor(path, workspace_hint)
    if app_lower == "terminal":
        return {"ok": False, "error": "use_terminal_preflight", "reason": "Use terminal preflight for bounded commands."}
    if app_lower == "browser":
        return {"ok": True, "action": "browser_evidence", "note": "Use governed browser evidence substrate."}
    if app_lower == "docker":
        return docker_readonly_inventory()
    if app_lower in ("kubernetes", "kubectl"):
        return kubectl_readonly_state()
    if app_lower == "github_desktop":
        return {"ok": True, "status": "readonly", "note": "GitHub Desktop status via git remote only."}
    return {"ok": False, "error": "unsupported_app", "app": app}


def _resolve_path(path: str | None, workspace_hint: str | None) -> Path | None:
    if path:
        p = Path(path).expanduser()
        return p if p.is_dir() else None
    if workspace_hint:
        from aethos_core.local_workspace.readonly.actions import _repo_from_hint

        return Path(_repo_from_hint(workspace_hint, session_id="default"))
    return None


def _open_vscode(path: str | None, workspace_hint: str | None) -> dict[str, Any]:
    target = _resolve_path(path, workspace_hint)
    if not target:
        return {"ok": False, "error": "path_not_found"}
    code = shutil.which("code")
    if not code:
        return {"ok": False, "error": "code_cli_not_found", "proposal": f"Open {target} in VS Code manually."}
    return {
        "ok": True,
        "approval_required": True,
        "command_proposal": [code, str(target)],
        "note": "Opening requires explicit approval — not executed automatically.",
        "autonomous_execution_blocked": True,
    }


def _open_cursor(path: str | None, workspace_hint: str | None) -> dict[str, Any]:
    target = _resolve_path(path, workspace_hint)
    if not target:
        return {"ok": False, "error": "path_not_found"}
    cursor = shutil.which("cursor")
    if not cursor:
        return {"ok": False, "error": "cursor_cli_not_found", "proposal": f"Open {target} in Cursor manually."}
    return {
        "ok": True,
        "approval_required": True,
        "command_proposal": [cursor, str(target)],
        "autonomous_execution_blocked": True,
    }


def docker_readonly_inventory() -> dict[str, Any]:
    if not shutil.which("docker"):
        return {"ok": False, "error": "docker_not_available"}
    try:
        proc = subprocess.run(["docker", "ps", "--format", "{{.Names}}\t{{.Status}}"], capture_output=True, text=True, timeout=10, check=False)
        return {"ok": True, "containers": (proc.stdout or "").strip().splitlines()[:20], "readonly": True}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}


def kubectl_readonly_state() -> dict[str, Any]:
    if not shutil.which("kubectl"):
        return {"ok": False, "error": "kubectl_not_available"}
    try:
        proc = subprocess.run(["kubectl", "get", "pods", "-A", "--no-headers"], capture_output=True, text=True, timeout=15, check=False)
        return {"ok": True, "pods": (proc.stdout or "").strip().splitlines()[:20], "readonly": True}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": str(exc)}
