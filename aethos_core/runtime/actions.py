# SPDX-License-Identifier: Apache-2.0
"""Approved runtime actions — propose → approve → execute → report."""

from __future__ import annotations

import re
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any
from uuid import uuid4

BROWSER_ASYNC_LAUNCH_TYPES = frozenset(
    {
        "browser_navigation_plan",
        "browser_login_required_notice",
    }
)

ACTION_TYPES = frozenset(
    {
        "runtime_restart",
        "terminal_probe",
        "vercel_cli_probe",
        "settings_change_proposal",
        "browser_status_check",
        "browser_navigation_plan",
        "browser_login_required_notice",
    }
)


class ActionStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    FAILED = "failed"
    DENIED = "denied"


@dataclass
class ActionEvent:
    id: str
    action_id: str
    event_type: str
    message: str
    status: str
    action_type: str
    session_id: str
    at: float = field(default_factory=time)
    browser_session_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        out = {
            "id": self.id,
            "action_id": self.action_id,
            "event_type": self.event_type,
            "message": self.message,
            "status": self.status,
            "action_type": self.action_type,
            "session_id": self.session_id,
            "at": self.at,
        }
        if self.browser_session_id:
            out["browser_session_id"] = self.browser_session_id
        return out


@dataclass
class RuntimeAction:
    id: str
    action_type: str
    status: ActionStatus
    summary: str
    params: dict[str, Any] = field(default_factory=dict)
    source: str = "chat"
    session_id: str = "default"
    created_at: float = field(default_factory=time)
    approved_at: float | None = None
    completed_at: float | None = None
    result: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "action_type": self.action_type,
            "status": self.status.value,
            "summary": self.summary,
            "params": self.params,
            "source": self.source,
            "session_id": self.session_id,
            "created_at": self.created_at,
            "approved_at": self.approved_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error,
        }


def _first_line(text: str | None, max_len: int = 120) -> str:
    if not text:
        return ""
    line = (text.strip().splitlines() or [""])[0]
    return line[:max_len]


def _vercel_version_snip(result: str | None) -> str:
    if not result:
        return ""
    m = re.search(r"version:\s*(\S+)", result, re.I)
    return m.group(1) if m else _first_line(result, 40)


def message_for_event(action: "RuntimeAction", event_type: str) -> str:
    """Short operational copy for chat system bubbles."""
    at = action.action_type
    if event_type == "action_approved":
        if at == "vercel_cli_probe":
            return "⏳ Action approved — running Vercel CLI probe…"
        if at == "terminal_probe":
            return "⏳ Action approved — running terminal probe…"
        if at == "runtime_restart":
            return "⏳ Restart action approved — preparing operator steps…"
        if at == "settings_change_proposal":
            return "⏳ Settings change approved — recording proposal…"
        if at in {"browser_status_check", "browser_navigation_plan", "browser_login_required_notice"}:
            from aethos_core.runtime.browser_lifecycle import action_approved_browser_message

            target = str(action.params.get("target") or "site")
            return action_approved_browser_message(
                target=target,
                status_check=at == "browser_status_check",
            )
        return f"⏳ Action approved — running {at.replace('_', ' ')}…"

    if event_type == "action_completed":
        if at == "vercel_cli_probe":
            ver = _vercel_version_snip(action.result)
            if ver:
                return f"✅ Vercel CLI detected — version {ver}"
            return "✅ Vercel CLI probe completed."
        if at == "terminal_probe":
            return f"✅ Terminal probe completed. {_first_line(action.result, 80)}"
        if at == "runtime_restart":
            return (
                "✅ Restart procedure prepared. "
                "Operator action is still required in MVP."
            )
        if at == "settings_change_proposal":
            return f"✅ Settings proposal recorded. {_first_line(action.result, 80)}"
        if at in {"browser_status_check", "browser_navigation_plan", "browser_login_required_notice"}:
            from aethos_core.runtime.browser_lifecycle import action_completed_browser_message

            target = str(action.params.get("target") or "site")
            sess_status = str(action.params.get("browser_session_status") or "")
            if at == "browser_status_check":
                return f"✅ Browser status check completed. {_first_line(action.result, 80)}"
            if sess_status:
                return action_completed_browser_message(
                    target=target,
                    session_status=sess_status,
                    login_notice=at == "browser_login_required_notice",
                )
            return f"✅ Browser action completed. {_first_line(action.result, 80)}"
        return f"✅ Action completed. {_first_line(action.result, 80)}"

    if event_type == "action_failed":
        err = action.error or "Action failed."
        if "host executor" in err.lower():
            return "⚠️ Terminal probe could not run because host executor is disabled."
        if action.action_type in {
            "browser_status_check",
            "browser_navigation_plan",
            "browser_login_required_notice",
        }:
            low = err.lower()
            if "disabled" in low and "browser_automation" in low.replace(" ", ""):
                return (
                    "⚠️ Browser automation is disabled. "
                    "Enable BROWSER_AUTOMATION_ENABLED=true and restart AethOS."
                )
            if "playwright package" in low or "package is not installed" in low:
                return (
                    "⚠️ Browser session could not start — Playwright package is missing "
                    "in the AethOS runtime environment."
                )
            if "chromium" in low and ("not installed" in low or "missing" in low):
                return (
                    "⚠️ Browser session could not start — Chromium is not installed "
                    "for Playwright in the AethOS runtime environment."
                )
            if "playwright" in low and "runtime environment" in low:
                return f"⚠️ Browser session could not start — {_first_line(err, 100)}"
            if "playwright" in low and "not installed" in low:
                return (
                    "⚠️ Browser session could not start — Playwright is not installed "
                    "in the AethOS runtime environment."
                )
            return f"⚠️ Browser session could not start — {_first_line(err, 80)}"
        return f"⚠️ {_first_line(err, 100)}"

    if event_type == "action_denied":
        if at in {"browser_status_check", "browser_navigation_plan", "browser_login_required_notice"}:
            target = str(action.params.get("target") or "site")
            return f"🚫 Browser job denied — no browser session opened for {target}."
        return f"🚫 Action denied — {_deny_label(at)}"

    return f"Action update: {event_type}"


def _deny_label(action_type: str) -> str:
    if action_type == "vercel_cli_probe":
        return "Vercel CLI probe was not run."
    if action_type == "terminal_probe":
        return "Terminal probe was not run."
    if action_type == "runtime_restart":
        return "Runtime restart was not run."
    if action_type == "settings_change_proposal":
        return "Settings change was not applied."
    if action_type in {
        "browser_status_check",
        "browser_navigation_plan",
        "browser_login_required_notice",
    }:
        return "no browser session opened"
    return f"{action_type.replace('_', ' ')} was not run."


def _new_id() -> str:
    return f"act-{uuid4().hex[:12]}"


def _event_id(action_id: str, event_type: str) -> str:
    return f"{action_id}:{event_type}"


def _summary_for(action_type: str, params: dict[str, Any]) -> str:
    if action_type == "runtime_restart":
        return "Restart AethOS API (operator-confirmed)"
    if action_type == "terminal_probe":
        return "Read-only terminal capability probe"
    if action_type == "vercel_cli_probe":
        return "Read-only Vercel CLI probe (which vercel, vercel --version)"
    if action_type == "settings_change_proposal":
        flag = params.get("flag", "unknown")
        value = params.get("value", "?")
        return f"Propose setting {flag}={value} in .env"
    if action_type == "browser_status_check":
        target = params.get("target", "unknown")
        return f"Browser status check — {target} (supervised)"
    if action_type == "browser_navigation_plan":
        target = params.get("target", "unknown")
        return f"Browser navigation plan — {target} (supervised)"
    if action_type == "browser_login_required_notice":
        target = params.get("target", "unknown")
        return f"Browser login notice — {target} (supervised, no credentials stored)"
    return action_type


def _execute_runtime_restart() -> str:
    return (
        "Restart recorded. The running API process cannot stop itself safely in MVP.\n"
        "Operator steps:\n"
        "1. Stop uvicorn on port 8010\n"
        "2. `.venv/bin/uvicorn aethos_core.api.main:app --reload --port 8010`\n"
        "3. Restart web dev server if needed"
    )


def _execute_terminal_probe(host_executor_enabled: bool) -> str:
    if not host_executor_enabled:
        raise RuntimeError("Host executor is disabled. Enable HOST_EXECUTOR_ENABLED in .env first.")
    proc = subprocess.run(
        ["uname", "-s"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    shell = shutil.which("bash") or shutil.which("sh") or "not found"
    return (
        f"Terminal probe OK.\n"
        f"- shell on PATH: {shell}\n"
        f"- uname: {(proc.stdout or proc.stderr).strip() or 'no output'}"
    )


def _execute_vercel_cli_probe(vercel_on_path: bool) -> str:
    vercel = shutil.which("vercel")
    if not vercel:
        return "Vercel CLI not found on PATH. Install with: npm i -g vercel"
    lines = [f"Vercel CLI: {vercel}"]
    ver = subprocess.run(
        [vercel, "--version"],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    lines.append(f"version: {(ver.stdout or ver.stderr).strip()}")
    return "\n".join(lines)


def _execute_browser_job(
    action_type: str,
    params: dict[str, Any],
    *,
    action_id: str | None = None,
    chat_session_id: str = "default",
) -> tuple[str, dict[str, Any]]:
    from aethos_core.runtime.browser_session import browser_session_store

    result, updates = browser_session_store.execute_approved_browser_action(
        action_type,
        params,
        action_id=action_id,
        chat_session_id=chat_session_id,
    )
    return result, updates


def _execute_settings_proposal(params: dict[str, Any]) -> str:
    flag = params.get("flag", "")
    value = params.get("value", "")
    return (
        f"Settings change approved as a proposal only (MVP does not write .env).\n"
        f"Add to `.env`: {flag}={value}\n"
        "Then restart the API."
    )


class ActionStore:
    """In-memory action registry and lifecycle event stream."""

    def __init__(self) -> None:
        self._actions: dict[str, RuntimeAction] = {}
        self._events: list[ActionEvent] = []
        self._lock = threading.Lock()

    def _emit(self, action: RuntimeAction, event_type: str) -> ActionEvent:
        bsid = action.params.get("browser_session_id")
        bsid_str = str(bsid) if bsid else None
        event = ActionEvent(
            id=_event_id(action.id, event_type),
            action_id=action.id,
            event_type=event_type,
            message=message_for_event(action, event_type),
            status=action.status.value,
            action_type=action.action_type,
            session_id=action.session_id,
            browser_session_id=bsid_str,
        )
        self._events.append(event)
        return event

    def propose(
        self,
        action_type: str,
        params: dict[str, Any] | None = None,
        *,
        source: str = "api",
        session_id: str = "default",
    ) -> RuntimeAction:
        if action_type not in ACTION_TYPES:
            raise ValueError(f"Unknown action_type: {action_type}")
        action = RuntimeAction(
            id=_new_id(),
            action_type=action_type,
            status=ActionStatus.PENDING,
            summary=_summary_for(action_type, params or {}),
            params=params or {},
            source=source,
            session_id=(session_id or "default")[:64],
        )
        self._actions[action.id] = action
        return action

    def get(self, action_id: str) -> RuntimeAction | None:
        return self._actions.get(action_id)

    def approve(
        self,
        action_id: str,
        *,
        host_executor_enabled: bool,
        vercel_cli_on_path: bool,
    ) -> RuntimeAction:
        action = self._actions.get(action_id)
        if not action:
            raise KeyError(action_id)
        if action.status != ActionStatus.PENDING:
            raise ValueError(f"Action {action_id} is not pending (status={action.status.value})")

        action.status = ActionStatus.APPROVED
        action.approved_at = time()
        self._emit(action, "action_approved")

        try:
            if action.action_type == "runtime_restart":
                action.result = _execute_runtime_restart()
            elif action.action_type == "terminal_probe":
                action.result = _execute_terminal_probe(host_executor_enabled)
            elif action.action_type == "vercel_cli_probe":
                action.result = _execute_vercel_cli_probe(vercel_cli_on_path)
            elif action.action_type == "settings_change_proposal":
                action.result = _execute_settings_proposal(action.params)
            elif action.action_type in {
                "browser_status_check",
                "browser_navigation_plan",
                "browser_login_required_notice",
            }:
                action.result, updates = _execute_browser_job(
                    action.action_type,
                    action.params,
                    action_id=action.id,
                    chat_session_id=action.session_id,
                )
                action.params = {**action.params, **updates}
                if action.action_type in BROWSER_ASYNC_LAUNCH_TYPES:
                    return action
            else:
                raise ValueError(f"Unsupported action: {action.action_type}")
            action.status = ActionStatus.COMPLETED
            action.completed_at = time()
            self._emit(action, "action_completed")
        except Exception as exc:
            action.status = ActionStatus.FAILED
            action.error = str(exc)
            action.completed_at = time()
            self._emit(action, "action_failed")
        return action

    def complete_browser_launch(
        self,
        action_id: str,
        *,
        success: bool,
        session_id: str = "",
        session_status: str = "",
        target: str = "",
        login_notice: bool = False,
        error: str | None = None,
    ) -> None:
        with self._lock:
            action = self._actions.get(action_id)
            if not action:
                return
            if action.status not in (ActionStatus.APPROVED, ActionStatus.PENDING):
                return
            if session_id:
                action.params["browser_session_id"] = session_id
            if session_status:
                action.params["browser_session_status"] = session_status
            if success:
                action.status = ActionStatus.COMPLETED
                action.result = (
                    f"Supervised browser session ready for `{target or action.params.get('target')}`. "
                    f"URL lifecycle tracked as `{session_id}`."
                )
                action.completed_at = time()
                self._emit(action, "action_completed")
            else:
                action.status = ActionStatus.FAILED
                action.error = error or "Browser session failed"
                action.completed_at = time()
                self._emit(action, "action_failed")

    def deny(self, action_id: str) -> RuntimeAction:
        action = self._actions.get(action_id)
        if not action:
            raise KeyError(action_id)
        if action.status != ActionStatus.PENDING:
            raise ValueError(f"Action {action_id} is not pending (status={action.status.value})")
        action.status = ActionStatus.DENIED
        action.completed_at = time()
        self._emit(action, "action_denied")
        return action

    def list_events(
        self,
        *,
        action_ids: list[str] | None = None,
        session_id: str | None = None,
        since: float = 0.0,
    ) -> list[dict[str, Any]]:
        out: list[ActionEvent] = []
        id_set = set(action_ids) if action_ids else None
        for event in self._events:
            if event.at < since:
                continue
            if id_set is not None and event.action_id not in id_set:
                continue
            # When polling explicit action IDs, do not filter by session (IDs are authoritative).
            if id_set is None and session_id and event.session_id != session_id:
                continue
            out.append(event)
        out.sort(key=lambda e: e.at)
        return [e.to_dict() for e in out]

    def list_all(self) -> list[RuntimeAction]:
        return sorted(self._actions.values(), key=lambda a: a.created_at, reverse=True)

    def list_grouped(self) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {
            "pending": [],
            "approved": [],
            "completed": [],
            "failed": [],
            "denied": [],
        }
        for action in self.list_all():
            grouped[action.status.value].append(action.to_dict())
        return grouped


def run_governed_shell_command(command: str, *, timeout_sec: float = 120.0, cwd: str | None = None) -> dict[str, Any]:
    from aethos_core.config import get_settings

    if not get_settings().host_executor_enabled:
        return {"ok": False, "error": "host_executor_disabled", "tool": "shell"}
    cmd = (command or "").strip()
    if not cmd:
        return {"ok": False, "error": "empty_command", "tool": "shell"}
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=min(float(timeout_sec), 300.0),
            cwd=cwd or None,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "tool": "shell",
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[:12000],
            "stderr": (proc.stderr or "")[:4000],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "timeout", "tool": "shell"}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "tool": "shell"}


def read_governed_file(path: str, *, max_bytes: int = 24000) -> dict[str, Any]:
    from pathlib import Path

    target = Path(path).expanduser()
    if not target.is_file():
        return {"ok": False, "error": "file_not_found", "tool": "file_read", "path": str(target)}
    try:
        content = target.read_text(encoding="utf-8", errors="replace")[:max_bytes]
        return {"ok": True, "tool": "file_read", "path": str(target), "content": content}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "tool": "file_read", "path": str(target)}


def write_governed_file(path: str, content: str, *, append: bool = False) -> dict[str, Any]:
    from aethos_core.config import get_settings
    from pathlib import Path

    if not get_settings().host_executor_enabled:
        return {"ok": False, "error": "host_executor_disabled", "tool": "file_write"}
    target = Path(path).expanduser()
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        if append and target.is_file():
            existing = target.read_text(encoding="utf-8", errors="replace")
            target.write_text(existing + content, encoding="utf-8")
        else:
            target.write_text(content, encoding="utf-8")
        return {"ok": True, "tool": "file_write", "path": str(target), "bytes": len(content.encode("utf-8"))}
    except OSError as exc:
        return {"ok": False, "error": str(exc), "tool": "file_write", "path": str(target)}


def run_governed_http_request(
    *,
    url: str,
    method: str = "GET",
    timeout_sec: float = 30.0,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    import httpx

    target = (url or "").strip()
    if not target.startswith(("http://", "https://")):
        return {"ok": False, "error": "invalid_url", "tool": "http_request"}
    try:
        with httpx.Client(timeout=min(float(timeout_sec), 60.0), follow_redirects=True) as client:
            response = client.request(method.upper(), target, headers=headers or {})
        return {
            "ok": response.status_code < 400,
            "tool": "http_request",
            "status_code": response.status_code,
            "body": (response.text or "")[:8000],
        }
    except httpx.HTTPError as exc:
        return {"ok": False, "error": str(exc), "tool": "http_request"}


# Process singleton
action_store = ActionStore()
