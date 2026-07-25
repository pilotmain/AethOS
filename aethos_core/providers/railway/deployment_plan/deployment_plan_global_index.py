# SPDX-License-Identifier: Apache-2.0
"""Global index for Railway deployment plans — survives session cache resets."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_INDEX_FILENAME = "global_plan_index.json"


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[3] / "data" / "railway_deployment_plan"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _index_path() -> Path:
    return _store_dir() / _INDEX_FILENAME


def _load_index() -> dict[str, Any]:
    path = _index_path()
    if not path.is_file():
        return {"entries": [], "latest_plan_id": "", "latest_by_repo": {}}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            raw.setdefault("entries", [])
            raw.setdefault("latest_plan_id", "")
            raw.setdefault("latest_by_repo", {})
            return raw
    except (OSError, json.JSONDecodeError):
        pass
    return {"entries": [], "latest_plan_id": "", "latest_by_repo": {}}


def _save_index(index: dict[str, Any]) -> None:
    try:
        _index_path().write_text(json.dumps(index, indent=2), encoding="utf-8")
    except OSError:
        pass


def _entry_sort_key(entry: dict[str, Any]) -> str:
    return str(entry.get("updated_at") or "")


def register_plan_in_global_index(
    *,
    session_id: str,
    plan: dict[str, Any],
    plan_id: str | None = None,
) -> str:
    """Record plan create/update; return plan_id."""
    repo = str(plan.get("repo") or "").strip()
    if not repo:
        return ""
    session_id = (session_id or "default").strip()
    pid = (plan_id or str(plan.get("plan_id") or "")).strip() or f"plan-{uuid.uuid4().hex[:12]}"
    updated_at = str(plan.get("updated_at") or datetime.now(UTC).isoformat())

    index = _load_index()
    entries: list[dict[str, Any]] = list(index.get("entries") or [])
    entries = [row for row in entries if str(row.get("plan_id") or "") != pid]
    entries.append(
        {
            "plan_id": pid,
            "session_id": session_id,
            "repo": repo,
            "updated_at": updated_at,
            "active": True,
            "stage": str(plan.get("stage") or ""),
        }
    )
    entries.sort(key=_entry_sort_key, reverse=True)

    latest_by_repo: dict[str, str] = dict(index.get("latest_by_repo") or {})
    latest_by_repo[repo.lower()] = pid

    index["entries"] = entries[:64]
    index["latest_plan_id"] = pid
    index["latest_by_repo"] = latest_by_repo
    _save_index(index)
    return pid


def _read_session_plan_file(session_id: str) -> dict[str, Any] | None:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    path = _store_dir() / f"{safe}_plan.json"
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and raw.get("repo"):
            return dict(raw)
    except (OSError, json.JSONDecodeError):
        pass
    return None


def load_plan_by_id(plan_id: str) -> dict[str, Any] | None:
    index = _load_index()
    session_id = ""
    for entry in index.get("entries") or []:
        if str(entry.get("plan_id") or "") == plan_id:
            session_id = str(entry.get("session_id") or "")
            break
    if not session_id:
        return None
    plan = _read_session_plan_file(session_id)
    if plan:
        return plan
    entries = sorted(list(index.get("entries") or []), key=_entry_sort_key, reverse=True)
    for entry in entries:
        if str(entry.get("plan_id") or "") != plan_id:
            continue
        alt_session = str(entry.get("session_id") or "")
        if alt_session and alt_session != session_id:
            plan = _read_session_plan_file(alt_session)
            if plan:
                return plan
    return None


def load_newest_plan_from_files() -> dict[str, Any] | None:
    """Fallback when index metadata exists but primary session file is missing."""
    newest: dict[str, Any] | None = None
    newest_key = ""
    for path in _store_dir().glob("*_plan.json"):
        if path.name == _INDEX_FILENAME:
            continue
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(raw, dict) or not raw.get("repo"):
            continue
        sort_key = str(raw.get("updated_at") or path.stat().st_mtime)
        if sort_key >= newest_key:
            newest_key = sort_key
            newest = dict(raw)
    return newest


def load_latest_active_plan() -> dict[str, Any] | None:
    index = _load_index()
    latest_id = str(index.get("latest_plan_id") or "").strip()
    if latest_id:
        plan = load_plan_by_id(latest_id)
        if plan:
            return plan
    entries = sorted(list(index.get("entries") or []), key=_entry_sort_key, reverse=True)
    for entry in entries:
        if not entry.get("active", True):
            continue
        plan = load_plan_by_id(str(entry.get("plan_id") or ""))
        if plan:
            return plan
    return load_newest_plan_from_files()


def load_plan_by_repo(repo: str) -> dict[str, Any] | None:
    target = (repo or "").strip().lower()
    if not target:
        return None
    index = _load_index()
    latest_by_repo: dict[str, str] = dict(index.get("latest_by_repo") or {})
    pid = latest_by_repo.get(target)
    if pid:
        plan = load_plan_by_id(pid)
        if plan and str(plan.get("repo") or "").lower() == target:
            return plan
    entries = sorted(list(index.get("entries") or []), key=_entry_sort_key, reverse=True)
    for entry in entries:
        if str(entry.get("repo") or "").lower() == target:
            plan = load_plan_by_id(str(entry.get("plan_id") or ""))
            if plan:
                return plan
    return None


def load_plan_from_route_trace(*, session_id: str = "default") -> dict[str, Any] | None:
    try:
        from aethos_core.chat.route_trace import get_last_route_trace

        trace = get_last_route_trace(session_id=session_id)
        if not trace:
            return None
        if str(trace.get("route_id") or "") != "railway_deployment_plan":
            return None
        repo = str(trace.get("repo") or "").strip()
        if repo:
            return load_plan_by_repo(repo)
    except Exception:
        pass
    return None


def clear_global_index_for_tests() -> None:
    try:
        _index_path().unlink(missing_ok=True)
    except OSError:
        pass
