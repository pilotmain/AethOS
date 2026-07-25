# SPDX-License-Identifier: Apache-2.0
"""Persist canonical Railway deployment lifecycle records."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_SESSION_STORE: dict[str, dict[str, Any]] = {}
_INDEX_FILENAME = "global_lifecycle_index.json"


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_lifecycle"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}_lifecycle.json"


def _index_path() -> Path:
    return _store_dir() / _INDEX_FILENAME


def empty_lifecycle_record(*, repo: str = "") -> dict[str, Any]:
    return {
        "lifecycle_id": "",
        "session_id": "",
        "repo": repo,
        "branch": "main",
        "project": "",
        "environment": "",
        "service_name": "",
        "readiness": {"status": "unknown", "checked_at": None, "checks": {}},
        "plan": {
            "exists": False,
            "mutation_ready": False,
            "review_confirmed": False,
            "snapshot": {},
        },
        "preflight": {
            "exists": False,
            "preflight_id": "",
            "approved": False,
            "snapshot": {},
        },
        "simulation": {
            "exists": False,
            "ready_to_execute": False,
            "blocking_reasons": [],
            "snapshot": {},
        },
        "updated_at": "",
    }


def session_lifecycle_file_exists(*, session_id: str) -> bool:
    return _session_path(session_id).is_file()


def inspect_global_lifecycle_index() -> dict[str, Any]:
    """Return index existence/readability without raising on corruption."""
    path = _index_path()
    if not path.is_file():
        return {
            "exists": False,
            "readable": False,
            "entries": 0,
            "latest_lifecycle_id": "",
            "latest_by_repo": {},
            "error": None,
            "index": None,
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "exists": True,
            "readable": False,
            "entries": 0,
            "latest_lifecycle_id": "",
            "latest_by_repo": {},
            "error": str(exc),
            "index": None,
        }
    except OSError as exc:
        return {
            "exists": True,
            "readable": False,
            "entries": 0,
            "latest_lifecycle_id": "",
            "latest_by_repo": {},
            "error": str(exc),
            "index": None,
        }
    if not isinstance(raw, dict):
        return {
            "exists": True,
            "readable": False,
            "entries": 0,
            "latest_lifecycle_id": "",
            "latest_by_repo": {},
            "error": "index payload is not a JSON object",
            "index": None,
        }
    raw.setdefault("entries", [])
    raw.setdefault("latest_lifecycle_id", "")
    raw.setdefault("latest_by_repo", {})
    entries = list(raw.get("entries") or [])
    return {
        "exists": True,
        "readable": True,
        "entries": len(entries),
        "latest_lifecycle_id": str(raw.get("latest_lifecycle_id") or ""),
        "latest_by_repo": dict(raw.get("latest_by_repo") or {}),
        "error": None,
        "index": raw,
    }


def _load_index() -> dict[str, Any]:
    inspected = inspect_global_lifecycle_index()
    index = inspected.get("index")
    if isinstance(index, dict):
        return index
    return {"entries": [], "latest_lifecycle_id": "", "latest_by_repo": {}}


def _save_index(index: dict[str, Any]) -> None:
    try:
        _index_path().write_text(json.dumps(index, indent=2), encoding="utf-8")
    except OSError:
        pass


def _entry_sort_key(entry: dict[str, Any]) -> str:
    return str(entry.get("updated_at") or "")


def _read_session_lifecycle_file(session_id: str) -> dict[str, Any] | None:
    path = _session_path(session_id)
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("repo"):
            return dict(raw)
    except (OSError, json.JSONDecodeError):
        pass
    return None


def save_lifecycle_record(*, session_id: str, record: dict[str, Any]) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    payload = dict(record)
    payload["session_id"] = session_id
    payload["updated_at"] = datetime.now(UTC).isoformat()
    if not payload.get("lifecycle_id"):
        payload["lifecycle_id"] = f"rlc-{uuid.uuid4().hex[:12]}"
    repo = str(payload.get("repo") or "").strip()
    if not repo:
        return payload

    _SESSION_STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass

    index = _load_index()
    lid = str(payload["lifecycle_id"])
    entries = [row for row in list(index.get("entries") or []) if str(row.get("lifecycle_id") or "") != lid]
    entries.append(
        {
            "lifecycle_id": lid,
            "session_id": session_id,
            "repo": repo,
            "updated_at": payload["updated_at"],
            "active": True,
        }
    )
    entries.sort(key=_entry_sort_key, reverse=True)
    latest_by_repo = dict(index.get("latest_by_repo") or {})
    latest_by_repo[repo.lower()] = lid
    index["entries"] = entries[:64]
    index["latest_lifecycle_id"] = lid
    index["latest_by_repo"] = latest_by_repo
    _save_index(index)
    return payload


def get_lifecycle_session(*, session_id: str) -> dict[str, Any] | None:
    session_id = (session_id or "default").strip()
    cached = _SESSION_STORE.get(session_id)
    if cached is not None:
        return dict(cached)
    record = _read_session_lifecycle_file(session_id)
    if record:
        _SESSION_STORE[session_id] = record
        return dict(record)
    return None


def load_lifecycle_by_id(lifecycle_id: str) -> dict[str, Any] | None:
    target = (lifecycle_id or "").strip()
    if not target:
        return None
    index = _load_index()
    session_ids: list[str] = []
    for entry in index.get("entries") or []:
        if str(entry.get("lifecycle_id") or "") == target:
            sid = str(entry.get("session_id") or "").strip()
            if sid and sid not in session_ids:
                session_ids.append(sid)
    for session_id in session_ids:
        record = _read_session_lifecycle_file(session_id)
        if record and str(record.get("lifecycle_id") or "") == target:
            return record
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in _store_dir().glob("*_lifecycle.json"):
        if path.name == _INDEX_FILENAME:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or str(raw.get("lifecycle_id") or "") != target:
            continue
        sort_key = str(raw.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = dict(raw)
    return newest


def load_lifecycle_by_repo(repo: str) -> dict[str, Any] | None:
    target = (repo or "").strip().lower()
    if not target:
        return None
    index = _load_index()
    pid = dict(index.get("latest_by_repo") or {}).get(target)
    if pid:
        record = load_lifecycle_by_id(str(pid))
        if record and str(record.get("repo") or "").lower() == target:
            return record
    entries = sorted(list(index.get("entries") or []), key=_entry_sort_key, reverse=True)
    for entry in entries:
        if str(entry.get("repo") or "").lower() != target:
            continue
        record = load_lifecycle_by_id(str(entry.get("lifecycle_id") or ""))
        if record:
            return record
    return _load_newest_lifecycle_from_files(repo=target)


def load_latest_active_lifecycle() -> dict[str, Any] | None:
    index = _load_index()
    latest_id = str(index.get("latest_lifecycle_id") or "").strip()
    if latest_id:
        record = load_lifecycle_by_id(latest_id)
        if record:
            return record
    entries = sorted(list(index.get("entries") or []), key=_entry_sort_key, reverse=True)
    for entry in entries:
        if not entry.get("active", True):
            continue
        record = load_lifecycle_by_id(str(entry.get("lifecycle_id") or ""))
        if record:
            return record
    return _load_newest_lifecycle_from_files()


def _load_newest_lifecycle_from_files(*, repo: str | None = None) -> dict[str, Any] | None:
    newest: dict[str, Any] | None = None
    newest_key = ""
    target = (repo or "").strip().lower()
    for path in _store_dir().glob("*_lifecycle.json"):
        if path.name == _INDEX_FILENAME:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("repo"):
            continue
        if target and str(raw.get("repo") or "").lower() != target:
            continue
        sort_key = str(raw.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = dict(raw)
    return newest


def clear_stale_global_lifecycle_index() -> dict[str, Any]:
    """Reset global lifecycle index when entries point at missing lifecycle files."""
    inspected = inspect_global_lifecycle_index()
    if not inspected.get("exists"):
        return {"cleared": False, "reason": "index_missing"}
    entries = list((inspected.get("index") or {}).get("entries") or [])
    _save_index({"entries": [], "latest_lifecycle_id": "", "latest_by_repo": {}})
    return {"cleared": True, "removed_entries": len(entries)}


def clear_for_tests() -> None:
    _SESSION_STORE.clear()
    try:
        _index_path().unlink(missing_ok=True)
    except OSError:
        pass
    for path in _store_dir().glob("*.json"):
        path.unlink()
