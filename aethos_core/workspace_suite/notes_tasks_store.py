# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — Notes & Tasks tab store (handoff §8).

Quick notes, checklist todos, and cron-style scheduled tasks. Local-first and
gitignored. Scheduled tasks are RECORDED only — they never auto-execute; any
action a task implies still runs through the governed preflight → approve → execute
path (handoff §8: "Scheduled actions run through governed jobs"). This store does
not fire jobs. Gated by WORKSPACE_SUITE_ENABLED, default off.
"""

from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Any

_NS_NOTES_TASKS = "workspace_notes_tasks"

_MAX_ITEMS = 1000
_MAX_TEXT_CHARS = 8_000


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (
        getattr(get_settings(), "workspace_suite_store_dir", "data/workspace_suite")
        or "data/workspace_suite"
    ).strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "notes_tasks.json"


def _empty() -> dict[str, Any]:
    return {"notes": {}, "tasks": {}}


def _load() -> dict[str, Any]:
    from aethos_core.storage.hosted_json_store import load_json_blob

    data = load_json_blob(_NS_NOTES_TASKS, _store_path(), _empty)
    if not isinstance(data, dict):
        return _empty()
    data.setdefault("notes", {})
    data.setdefault("tasks", {})
    return data


def _save(data: dict[str, Any]) -> None:
    from aethos_core.storage.hosted_json_store import save_json_blob

    save_json_blob(_NS_NOTES_TASKS, _store_path(), data)


def _enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "workspace_suite_enabled", False))


def add_note(*, text: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    body = str(text or "").strip()[:_MAX_TEXT_CHARS]
    if not body:
        return {"ok": False, "error": "text_required"}
    note_id = f"note-{secrets.token_hex(5)}"
    note = {"id": note_id, "text": body, "created_at": time.time()}
    store = _load()
    notes = dict(store.get("notes") or {})
    if len(notes) >= _MAX_ITEMS:
        return {"ok": False, "error": "note_limit_reached", "limit": _MAX_ITEMS}
    notes[note_id] = note
    store["notes"] = notes
    _save(store)
    return {"ok": True, "note": note}


def list_notes(*, limit: int = 100) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "notes": []}
    store = _load()
    notes = [n for n in (store.get("notes") or {}).values() if isinstance(n, dict)]
    notes.sort(key=lambda n: float(n.get("created_at") or 0), reverse=True)
    return {"ok": True, "note_count": len(notes), "notes": notes[: max(1, min(int(limit or 100), _MAX_ITEMS))]}


def delete_note(*, note_id: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    notes = dict(store.get("notes") or {})
    if (note_id or "").strip() not in notes:
        return {"ok": False, "error": "note_not_found", "id": note_id}
    notes.pop((note_id or "").strip(), None)
    store["notes"] = notes
    _save(store)
    return {"ok": True, "deleted": note_id}


def add_task(*, text: str, scheduled_for: str | None = None) -> dict[str, Any]:
    """Add a checklist task. scheduled_for is a free-form cron/ISO hint — recorded only."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    body = str(text or "").strip()[:_MAX_TEXT_CHARS]
    if not body:
        return {"ok": False, "error": "text_required"}
    task_id = f"task-{secrets.token_hex(5)}"
    now = time.time()
    task = {
        "id": task_id,
        "text": body,
        "done": False,
        "scheduled_for": (str(scheduled_for).strip() or None) if scheduled_for else None,
        # Scheduled tasks never auto-run — any action routes through governed jobs.
        "auto_execute": False,
        "created_at": now,
        "updated_at": now,
    }
    store = _load()
    tasks = dict(store.get("tasks") or {})
    if len(tasks) >= _MAX_ITEMS:
        return {"ok": False, "error": "task_limit_reached", "limit": _MAX_ITEMS}
    tasks[task_id] = task
    store["tasks"] = tasks
    _save(store)
    return {"ok": True, "task": task}


def set_task_done(*, task_id: str, done: bool = True) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    tasks = dict(store.get("tasks") or {})
    task = tasks.get((task_id or "").strip())
    if not isinstance(task, dict):
        return {"ok": False, "error": "task_not_found", "id": task_id}
    task["done"] = bool(done)
    task["updated_at"] = time.time()
    tasks[task["id"]] = task
    store["tasks"] = tasks
    _save(store)
    return {"ok": True, "task": task}


def list_tasks(*, limit: int = 200) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "tasks": []}
    store = _load()
    tasks = [t for t in (store.get("tasks") or {}).values() if isinstance(t, dict)]
    tasks.sort(key=lambda t: (bool(t.get("done")), -float(t.get("created_at") or 0)))
    return {"ok": True, "task_count": len(tasks), "tasks": tasks[: max(1, min(int(limit or 200), _MAX_ITEMS))]}


def delete_task(*, task_id: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    tasks = dict(store.get("tasks") or {})
    if (task_id or "").strip() not in tasks:
        return {"ok": False, "error": "task_not_found", "id": task_id}
    tasks.pop((task_id or "").strip(), None)
    store["tasks"] = tasks
    _save(store)
    return {"ok": True, "deleted": task_id}


def clear_notes_tasks_for_tests() -> None:
    from aethos_core.storage.hosted_json_store import clear_json_blob_for_tests

    clear_json_blob_for_tests(_NS_NOTES_TASKS, _store_path())
