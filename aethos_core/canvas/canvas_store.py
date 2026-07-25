# SPDX-License-Identifier: Apache-2.0
"""Live Canvas render store (handoff §11).

The Live Canvas is a render surface ONLY — it cannot execute mutations. The agent
pushes structured read-only views (status, diff, research report, job timeline,
table, markdown) via the canvas_render tool; the operator views them in the canvas
panel. Governed job state still flows from Mission Control. Gated by
CANVAS_SURFACE_ENABLED, default off.

With ``DATABASE_URL``: rows in shared Postgres ``canvas_views`` (api/worker/replicas).
Without ``DATABASE_URL``: local-first gitignored JSON file.
"""

from __future__ import annotations

import json
import logging
import secrets
import time
from pathlib import Path
from typing import Any

_log = logging.getLogger(__name__)

ALLOWED_VIEW_TYPES = frozenset(
    {"status", "diff", "research_report", "job_timeline", "table", "markdown"}
)
_MAX_VIEWS_PER_SESSION = 50


def _rows_have_content(rows: Any) -> bool:
    """True when at least one row carries a non-empty value — guards against a wall of
    empty cells (the agent emitting placeholder/empty rows that render as all '—')."""
    if not isinstance(rows, list):
        return False
    for row in rows:
        if isinstance(row, dict):
            for value in row.values():
                if value not in (None, "", "—", "-") and not (
                    isinstance(value, (list, dict)) and not value
                ):
                    return True
        elif isinstance(row, (str, int, float)) and str(row).strip() not in ("", "—", "-"):
            return True
    return False


def is_structured_canvas_view_data(view_type: str, data: Any) -> tuple[bool, str]:
    """Validate view payload — rejects prose-only dumps (never the model's chat reply as data)."""
    vt = (view_type or "").strip().lower()
    if data is None:
        return False, "missing_data"
    if isinstance(data, str):
        if vt == "markdown" and data.strip():
            return True, ""
        return False, "prose_string_not_structured"
    if not isinstance(data, dict):
        return False, "data_must_be_object"

    keys = set(data.keys())
    if keys <= {"summary", "source"} and str(data.get("source") or "") == "agent_runtime":
        return False, "prose_summary_not_structured_view"
    if keys == {"summary"} or (keys <= {"summary", "source"} and "summary" in keys):
        summary = str(data.get("summary") or "")
        if summary and not any(k in data for k in ("events", "rows", "columns", "content", "hunks", "items")):
            return False, "summary_only_not_structured_view"

    if vt == "job_timeline":
        events = data.get("events")
        rows = data.get("rows")
        if isinstance(events, list) and events:
            if not _rows_have_content(events):
                return False, "job_timeline_rows_all_empty"
            return True, ""
        if isinstance(rows, list) and rows:
            if not _rows_have_content(rows):
                return False, "job_timeline_rows_all_empty"
            return True, ""
        return False, "job_timeline_requires_events_or_rows"
    if vt == "table":
        rows = data.get("rows")
        columns = data.get("columns")
        if isinstance(rows, list) and rows:
            if not _rows_have_content(rows):
                return False, "table_rows_all_empty"
            return True, ""
        if isinstance(columns, list) and columns and isinstance(rows, list):
            # Columns with an explicitly empty row list is a header-only skeleton — reject.
            return False, "table_rows_all_empty"
        if isinstance(columns, list) and columns:
            return True, ""
        return False, "table_requires_rows_or_columns"
    if vt == "diff":
        if any(k in data for k in ("before", "after", "hunks", "lines", "diff", "old_text", "new_text")):
            return True, ""
        return False, "diff_requires_structured_diff_fields"
    if vt == "markdown":
        content = data.get("content") or data.get("markdown") or data.get("text")
        if isinstance(content, str) and content.strip():
            return True, ""
        return False, "markdown_requires_content"
    if vt == "status":
        if any(k in data for k in ("status", "items", "fields", "services", "checks", "rows", "ok")):
            return True, ""
        return False, "status_requires_structured_fields"
    if vt == "research_report":
        if data.get("sections") or data.get("findings") or isinstance(data.get("report"), (dict, list)):
            return True, ""
        return False, "research_report_requires_sections"
    return True, ""


def _uses_postgres() -> bool:
    from aethos_core.canvas.canvas_db import canvas_uses_postgres

    return canvas_uses_postgres()


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (getattr(get_settings(), "canvas_store_dir", "data/canvas") or "data/canvas").strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "canvas.json"


def _empty_store() -> dict[str, Any]:
    return {"sessions": {}}


def _load_file_store() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return _empty_store()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_store()
    return data if isinstance(data, dict) else _empty_store()


def _save_file_store(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = dict(data)
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _session_lookup_keys(session_id: str) -> list[str]:
    """All canvas store keys that should share views for this live chat session."""
    from aethos_core.channels.session_alias import resolve_canonical_session_id, session_ids_for_lookup

    sid = (session_id or "default").strip() or "default"
    keys: list[str] = [sid]
    canonical = resolve_canonical_session_id(sid)
    keys.append(canonical)
    keys.extend(session_ids_for_lookup(sid))
    keys.extend(session_ids_for_lookup(canonical))
    return list(dict.fromkeys(k for k in keys if k))


def _merge_views_for_session(store: dict[str, Any], session_id: str) -> list[dict[str, Any]]:
    sessions = store.get("sessions") or {}
    merged: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for key in _session_lookup_keys(session_id):
        for view in list(sessions.get(key) or []):
            if not isinstance(view, dict):
                continue
            vid = str(view.get("id") or "")
            if vid and vid in seen_ids:
                continue
            if vid:
                seen_ids.add(vid)
            merged.append(view)
    merged.sort(key=lambda v: float(v.get("created_at") or 0), reverse=True)
    return merged


def init_canvas_store_schema() -> None:
    """Boot-time schema for Postgres canvas store (no-op for file mode)."""
    from aethos_core.canvas.canvas_db import init_canvas_schema

    init_canvas_schema()


def _dedupe_views_by_type(views: list[dict[str, Any]], view_type: str) -> list[dict[str, Any]]:
    vt = (view_type or "").strip().lower()
    kept = [v for v in views if str(v.get("view_type") or "").lower() != vt]
    return kept


def render_canvas_view(
    *,
    session_id: str,
    view_type: str,
    title: str,
    data: Any,
) -> dict[str, Any]:
    """Push a read-only structured view to the Live Canvas. Never executes anything."""
    from aethos_core.canvas.session_context import canvas_write_session_id
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "canvas_surface_enabled", True):
        return {"ok": False, "error": "canvas_surface_disabled"}
    vt = (view_type or "").strip().lower()
    if vt not in ALLOWED_VIEW_TYPES:
        return {"ok": False, "error": "unsupported_view_type", "allowed": sorted(ALLOWED_VIEW_TYPES)}
    valid, reason = is_structured_canvas_view_data(vt, data)
    if not valid:
        return {"ok": False, "error": reason or "invalid_view_data"}
    sid = canvas_write_session_id(session_id)
    fallback = (session_id or "default").strip()[:64] or "default"
    write_keys = list(dict.fromkeys(_session_lookup_keys(sid) + _session_lookup_keys(fallback)))
    view_id = f"cv-{secrets.token_hex(5)}"
    view = {
        "id": view_id,
        "view_type": vt,
        "title": (title or vt)[:200],
        "data": data,
        "read_only": True,
        "created_at": time.time(),
    }
    if _uses_postgres():
        from aethos_core.canvas.canvas_db import delete_canvas_views_by_type, insert_canvas_view

        delete_canvas_views_by_type(session_keys=write_keys, view_type=vt)
        insert_canvas_view(
            session_keys=write_keys,
            view_id=view_id,
            view_type=vt,
            title=view["title"],
            data=data,
        )
    else:
        store = _load_file_store()
        sessions = dict(store.get("sessions") or {})
        for key in write_keys:
            views = _dedupe_views_by_type(list(sessions.get(key) or []), vt)
            views.append(view)
            sessions[key] = views[-_MAX_VIEWS_PER_SESSION:]
        store["sessions"] = sessions
        _save_file_store(store)
    _log.info(
        "canvas_render write session_id=%s write_keys=%s view_type=%s view_id=%s backend=%s",
        sid,
        write_keys,
        vt,
        view_id,
        "postgres" if _uses_postgres() else "file",
    )
    return {"ok": True, "view_id": view_id, "view_type": vt, "read_only": True, "session_id": sid}


def _latest_session_in_file_store(store: dict[str, Any]) -> str:
    sessions = store.get("sessions") or {}
    best_sid = ""
    best_ts = -1.0
    for key, views in sessions.items():
        for view in views or []:
            if not isinstance(view, dict):
                continue
            ts = float(view.get("created_at") or 0)
            if ts > best_ts:
                best_ts = ts
                best_sid = key
    return best_sid


def get_canvas_state(*, session_id: str, limit: int = 20, include_fallback: bool = True) -> dict[str, Any]:
    """Read canvas views for a session.

    ``include_fallback`` (default True) makes an empty session fall back to the tenant's
    most recent render so the UI auto-shows the latest drawing across windows. Pass False
    for exact per-session checks (e.g. verifying THIS turn wrote a view) — the fallback
    would otherwise mask a real session count and confound before/after verification.
    """
    sid = (session_id or "default").strip() or "default"
    lookup_keys = _session_lookup_keys(sid)
    resolved_session = sid
    fell_back = False
    if _uses_postgres():
        from aethos_core.canvas.canvas_db import latest_canvas_session_for_tenant, list_canvas_views

        views = list_canvas_views(session_keys=lookup_keys, limit=_MAX_VIEWS_PER_SESSION)
        if not views and include_fallback:
            # Cross-window/browser: the panel may be bound to a different session id than
            # the chat that rendered. Auto-show the tenant's most recent render so the
            # operator sees it without having to match session ids by hand.
            latest_sid = latest_canvas_session_for_tenant()
            if latest_sid and latest_sid not in lookup_keys:
                fb = list_canvas_views(session_keys=[latest_sid], limit=_MAX_VIEWS_PER_SESSION)
                if fb:
                    views = fb
                    resolved_session = latest_sid
                    fell_back = True
        for row in views:
            row.pop("_session_id", None)
    else:
        store = _load_file_store()
        views = _merge_views_for_session(store, sid)
        if not views and include_fallback:
            latest_sid = _latest_session_in_file_store(store)
            if latest_sid and latest_sid not in lookup_keys:
                fb = _merge_views_for_session(store, latest_sid)
                if fb:
                    views = fb
                    resolved_session = latest_sid
                    fell_back = True
    _log.info(
        "canvas_state read request_session_id=%s lookup_keys=%s view_count=%d fell_back=%s resolved=%s backend=%s",
        sid,
        lookup_keys,
        len(views),
        fell_back,
        resolved_session,
        "postgres" if _uses_postgres() else "file",
    )
    capped = views[: max(1, min(limit, _MAX_VIEWS_PER_SESSION))]
    return {
        "ok": True,
        "session_id": sid,
        "resolved_session": resolved_session,
        "showing_latest_render": fell_back,
        "read_only": True,
        "view_count": len(views),
        "views": capped,
    }


def clear_canvas_for_tests() -> None:
    if _uses_postgres():
        from aethos_core.canvas.canvas_db import clear_canvas_views_for_tests, reset_canvas_db_for_tests

        clear_canvas_views_for_tests()
        reset_canvas_db_for_tests()
        return
    path = _store_path()
    if path.is_file():
        path.unlink()
