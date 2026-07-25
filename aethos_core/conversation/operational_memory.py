# SPDX-License-Identifier: Apache-2.0
"""Operational memory — real conversation continuity and investigation persistence."""

from __future__ import annotations

import json
from time import time
from typing import Any

from pathlib import Path

_NS = "operational_memory"


def _memory_root() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "conversation" / "operational_memory"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_key(session_id: str) -> str:
    return (session_id or "default").strip() or "default"


def _empty_memory() -> dict[str, Any]:
    return {
        "last_focus": None,
        "focus_topics": [],
        "unresolved_issues": [],
        "active_investigations": [],
        "temporal_snapshots": [],
        "channel": "chat",
    }


def load_operational_memory(*, session_id: str = "default") -> dict[str, Any]:
    from aethos_core.tenancy.tenant_data_store import get_record, set_record

    key = _session_key(session_id)
    stored = get_record(_NS, key, default=None)
    if isinstance(stored, dict) and stored:
        return stored
    path = _memory_root() / f"memory_{key}.json"
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                set_record(_NS, key, data)
                return data
        except (OSError, json.JSONDecodeError):
            pass
    return _empty_memory()


def save_operational_memory(*, session_id: str = "default", memory: dict[str, Any]) -> None:
    from aethos_core.tenancy.tenant_data_store import set_record

    memory["updated_at"] = time()
    set_record(_NS, _session_key(session_id), memory)


def record_focus_recovery(*, session_id: str = "default", focus: str, channel: str = "chat") -> None:
    mem = load_operational_memory(session_id=session_id)
    mem["last_focus"] = focus
    topics: list[str] = mem.get("focus_topics") or []
    if focus not in topics:
        topics.insert(0, focus)
    mem["focus_topics"] = topics[:12]
    mem["channel"] = channel
    save_operational_memory(session_id=session_id, memory=mem)


def track_unresolved_issue(*, session_id: str = "default", issue: str) -> None:
    mem = load_operational_memory(session_id=session_id)
    issues: list[str] = mem.get("unresolved_issues") or []
    if issue not in issues:
        issues.insert(0, issue)
    mem["unresolved_issues"] = issues[:12]
    save_operational_memory(session_id=session_id, memory=mem)


def persist_investigation(*, session_id: str = "default", investigation: str) -> None:
    mem = load_operational_memory(session_id=session_id)
    invs: list[str] = mem.get("active_investigations") or []
    if investigation not in invs:
        invs.insert(0, investigation)
    mem["active_investigations"] = invs[:8]
    save_operational_memory(session_id=session_id, memory=mem)


def snapshot_operator_context(*, session_id: str = "default", context: dict[str, Any]) -> None:
    mem = load_operational_memory(session_id=session_id)
    snaps: list[dict[str, Any]] = mem.get("temporal_snapshots") or []
    snaps.insert(0, {"at": time(), **context})
    mem["temporal_snapshots"] = snaps[:20]
    save_operational_memory(session_id=session_id, memory=mem)


def build_continuity_context(*, session_id: str = "default") -> dict[str, Any]:
    """Merge operational memory into continuity context for living intelligence."""
    mem = load_operational_memory(session_id=session_id)
    from aethos_core.presence.live.live_presence_runtime import get_live_focus

    live = get_live_focus(session_id=session_id)
    focus_topics = list(dict.fromkeys((mem.get("focus_topics") or []) + ([live.get("topic")] if live.get("topic") else [])))
    unresolved = mem.get("unresolved_issues") or []
    investigations = mem.get("active_investigations") or []

    return {
        "focus_topics": [t for t in focus_topics if t][:8],
        "unresolved_issues": unresolved[:8],
        "active_investigations": investigations[:8],
        "last_focus": mem.get("last_focus") or live.get("topic"),
        "channel": mem.get("channel") or "chat",
        "has_memory": bool(focus_topics or unresolved or investigations),
    }


def seed_default_operational_context(*, session_id: str = "default") -> None:
    """Seed operational context when continuity memory provides the journey."""
    from aethos_core.human_centered.continuity_memory import load_continuity_memory, seed_default_continuity

    seed_default_continuity(session_id=session_id)
    continuity = load_continuity_memory(session_id=session_id)
    mem = load_operational_memory(session_id=session_id)
    if mem.get("focus_topics"):
        return
    focus = continuity.get("focus") or "Living Intelligence"
    mem.update({
        "last_focus": continuity.get("current_system_focus") or focus,
        "focus_topics": [focus, continuity.get("current_system_focus") or "Runtime integrity"],
        "unresolved_issues": continuity.get("unresolved") or [],
        "active_investigations": continuity.get("collaboration_context") or [],
        "channel": "mission_control",
    })
    save_operational_memory(session_id=session_id, memory=mem)


def clear_operational_memory_for_tests() -> None:
    from aethos_core.tenancy.tenant_data_store import clear_namespace

    root = _memory_root()
    for p in root.glob("*.json"):
        p.unlink()
    clear_namespace(_NS)


def delete_operational_memory(*, session_id: str = "default") -> None:
    from aethos_core.tenancy.tenant_data_store import delete_record

    delete_record(_NS, _session_key(session_id))
    path = _memory_root() / f"memory_{_session_key(session_id)}.json"
    if path.is_file():
        path.unlink()
