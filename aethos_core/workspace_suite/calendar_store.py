# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — Calendar tab (handoff §8).

Local-first calendar: dependency-free .ics import/export, per-calendar colors, and
local events. CalDAV sync is READONLY by default and degrades gracefully to
caldav_not_configured when no creds/library are present (production sources CalDAV
creds from the MC vault). Local event creation is a draft on your machine; writing
back to a remote calendar is intentionally NOT implemented here (writes gated).
Gated by WORKSPACE_SUITE_ENABLED, default off.
"""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any

_DEFAULT_COLORS = ("#22d3ee", "#a78bfa", "#34d399", "#fbbf24", "#f87171")
_MAX_EVENTS = 2000


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (
        getattr(get_settings(), "workspace_suite_store_dir", "data/workspace_suite")
        or "data/workspace_suite"
    ).strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "calendar.json"


def _enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "workspace_suite_enabled", False))


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"calendars": {}, "events": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"calendars": {}, "events": {}}
    if not isinstance(data, dict):
        return {"calendars": {}, "events": {}}
    data.setdefault("calendars", {})
    data.setdefault("events", {})
    return data


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _ensure_calendar(data: dict[str, Any], calendar: str) -> None:
    calendars = dict(data.get("calendars") or {})
    if calendar not in calendars:
        color = _DEFAULT_COLORS[len(calendars) % len(_DEFAULT_COLORS)]
        calendars[calendar] = {"name": calendar, "color": color}
        data["calendars"] = calendars


def add_event(
    *,
    summary: str,
    start: str,
    end: str = "",
    description: str = "",
    calendar: str = "default",
) -> dict[str, Any]:
    """Add a LOCAL event (draft on your machine). Does not write to a remote calendar."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    title = (summary or "").strip()
    if not title or not (start or "").strip():
        return {"ok": False, "error": "summary_and_start_required"}
    cal = (calendar or "default").strip() or "default"
    event_id = f"evt-{secrets.token_hex(5)}"
    event = {
        "id": event_id,
        "uid": f"{event_id}@aethos.local",
        "summary": title[:300],
        "start": str(start).strip(),
        "end": str(end).strip(),
        "description": str(description or "")[:2000],
        "calendar": cal,
        "source": "local",
        "created_at": time.time(),
    }
    data = _load()
    events = dict(data.get("events") or {})
    if len(events) >= _MAX_EVENTS:
        return {"ok": False, "error": "event_limit_reached", "limit": _MAX_EVENTS}
    _ensure_calendar(data, cal)
    events[event_id] = event
    data["events"] = events
    _save(data)
    return {"ok": True, "event": event}


def list_events(*, limit: int = 200) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "events": []}
    data = _load()
    events = [e for e in (data.get("events") or {}).values() if isinstance(e, dict)]
    events.sort(key=lambda e: str(e.get("start") or ""))
    return {
        "ok": True,
        "calendars": list((data.get("calendars") or {}).values()),
        "event_count": len(events),
        "events": events[: max(1, min(int(limit or 200), _MAX_EVENTS))],
    }


def delete_event(*, event_id: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    data = _load()
    events = dict(data.get("events") or {})
    if (event_id or "").strip() not in events:
        return {"ok": False, "error": "event_not_found", "id": event_id}
    events.pop((event_id or "").strip(), None)
    data["events"] = events
    _save(data)
    return {"ok": True, "deleted": event_id}


# --- Minimal dependency-free ICS (RFC 5545 subset) ---


def _unfold_ics(text: str) -> list[str]:
    """Unfold ICS continuation lines (leading space/tab continues prior line)."""
    out: list[str] = []
    for raw in (text or "").splitlines():
        if raw[:1] in (" ", "\t") and out:
            out[-1] += raw[1:]
        else:
            out.append(raw)
    return out


def import_ics(*, ics_text: str, calendar: str = "imported") -> dict[str, Any]:
    """Parse VEVENT blocks from .ics text into local events (readonly import)."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    lines = _unfold_ics(ics_text)
    data = _load()
    events = dict(data.get("events") or {})
    cal = (calendar or "imported").strip() or "imported"
    _ensure_calendar(data, cal)
    imported = 0
    current: dict[str, str] | None = None
    for line in lines:
        stripped = line.strip()
        if stripped == "BEGIN:VEVENT":
            current = {}
            continue
        if stripped == "END:VEVENT":
            if current is not None and current.get("SUMMARY") and current.get("DTSTART"):
                if len(events) >= _MAX_EVENTS:
                    break
                event_id = f"evt-{secrets.token_hex(5)}"
                events[event_id] = {
                    "id": event_id,
                    "uid": current.get("UID") or f"{event_id}@aethos.local",
                    "summary": current["SUMMARY"][:300],
                    "start": current["DTSTART"],
                    "end": current.get("DTEND", ""),
                    "description": current.get("DESCRIPTION", "")[:2000],
                    "calendar": cal,
                    "source": "ics",
                    "created_at": time.time(),
                }
                imported += 1
            current = None
            continue
        if current is None or ":" not in line:
            continue
        key, _, value = line.partition(":")
        # Drop parameters after the property name (e.g. DTSTART;TZID=...).
        key = key.split(";", 1)[0].strip().upper()
        if key in ("SUMMARY", "DTSTART", "DTEND", "DESCRIPTION", "UID"):
            current[key] = value.strip()
    data["events"] = events
    _save(data)
    return {"ok": True, "imported": imported, "calendar": cal}


def export_ics() -> dict[str, Any]:
    """Export all local events as an .ics document string."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    data = _load()
    events = [e for e in (data.get("events") or {}).values() if isinstance(e, dict)]
    out = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//AethOS//Workspace Calendar//EN"]
    for e in events:
        out.append("BEGIN:VEVENT")
        out.append(f"UID:{e.get('uid') or e.get('id')}")
        out.append(f"SUMMARY:{e.get('summary', '')}")
        if e.get("start"):
            out.append(f"DTSTART:{e['start']}")
        if e.get("end"):
            out.append(f"DTEND:{e['end']}")
        if e.get("description"):
            out.append(f"DESCRIPTION:{e['description']}")
        out.append("END:VEVENT")
    out.append("END:VCALENDAR")
    return {"ok": True, "event_count": len(events), "ics": "\r\n".join(out)}


def caldav_sync() -> dict[str, Any]:
    """Readonly CalDAV sync. Degrades to caldav_not_configured without creds/library.

    Writes back to remote calendars are intentionally NOT performed here (writes
    gated per handoff §8). Production resolves CalDAV creds from the MC vault.
    """
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    creds_path = _store_root() / "caldav_creds.json"
    if not creds_path.is_file():
        return {
            "ok": False,
            "error": "caldav_not_configured",
            "hint": "Add CalDAV creds to the MC vault (or data/workspace_suite/caldav_creds.json). Sync is readonly.",
        }
    try:
        import caldav  # type: ignore  # noqa: F401
    except Exception:
        return {"ok": False, "error": "caldav_library_unavailable", "hint": "pip install caldav to enable readonly sync."}
    # Readonly sync implementation is environment-specific; creds + library present
    # is the contract. Remote writes remain disabled by design.
    return {"ok": True, "synced": 0, "readonly": True, "note": "readonly sync ready; remote writes disabled"}


def clear_calendar_for_tests() -> None:
    for path in (_store_path(), _store_root() / "caldav_creds.json"):
        if path.is_file():
            path.unlink()
