# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 Phase 8 — operational goal lifecycle evidence."""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

GoalStatus = Literal["goal_started", "goal_completed", "goal_blocked", "goal_abandoned"]

_lock = threading.Lock()
_memory_goals: list[dict[str, Any]] = []


@dataclass
class OperationalGoalRecord:
    goal_id: str
    session_id: str
    headline: str
    provider: str
    status: GoalStatus
    goal_kind: str = "deploy_planning"
    steps_completed: list[str] = field(default_factory=list)
    steps_pending: list[str] = field(default_factory=list)
    started_at: str = ""
    updated_at: str = ""
    user_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _store_dir() -> Path:
    from aethos_core.operational_session.kernel_reality_registry import _store_dir as base

    return base()


def _goals_path() -> Path:
    return _store_dir() / "goals.jsonl"


def _enabled() -> bool:
    from aethos_core.operational_session.kernel_reality_registry import reality_capture_enabled

    return reality_capture_enabled()


def append_goal_record(record: OperationalGoalRecord) -> None:
    payload = record.to_dict()
    with _lock:
        _memory_goals.append(payload)
        if _enabled():
            with _goals_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_goal_records(*, limit: int = 2000) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    path = _goals_path()
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                gid = str(row.get("goal_id") or "")
                if gid and gid in seen:
                    continue
                if gid:
                    seen.add(gid)
                rows.append(row)
    with _lock:
        for row in _memory_goals:
            gid = str(row.get("goal_id") or "")
            if gid and gid in seen:
                continue
            if gid:
                seen.add(gid)
            rows.append(row)
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def _active_goal_for_session(session_id: str) -> dict[str, Any] | None:
    for row in reversed(load_goal_records(limit=500)):
        if row.get("session_id") != session_id:
            continue
        if row.get("status") == "goal_started":
            return row
    return None


def record_goal_started(
    *,
    session_id: str,
    headline: str,
    provider: str,
    goal_kind: str,
    user_text: str,
    steps_pending: list[str],
) -> OperationalGoalRecord | None:
    if not _enabled():
        return None
    now = datetime.now(UTC).isoformat()
    record = OperationalGoalRecord(
        goal_id=str(uuid.uuid4()),
        session_id=session_id,
        headline=headline[:200],
        provider=provider,
        status="goal_started",
        goal_kind=goal_kind,
        steps_pending=list(steps_pending),
        started_at=now,
        updated_at=now,
        user_text=user_text[:500],
    )
    append_goal_record(record)
    _increment_goal_metrics("goal_started")
    return record


def record_goal_progress(
    *,
    session_id: str,
    step_id: str,
    steps_pending: list[str] | None = None,
) -> None:
    if not _enabled():
        return
    active = _active_goal_for_session(session_id)
    if active is None:
        return
    completed = list(active.get("steps_completed") or [])
    if step_id and step_id not in completed:
        completed.append(step_id)
    pending = list(steps_pending if steps_pending is not None else active.get("steps_pending") or [])
    record = OperationalGoalRecord(
        goal_id=str(active.get("goal_id")),
        session_id=session_id,
        headline=str(active.get("headline") or ""),
        provider=str(active.get("provider") or ""),
        status="goal_started",
        goal_kind=str(active.get("goal_kind") or ""),
        steps_completed=completed,
        steps_pending=pending,
        started_at=str(active.get("started_at") or ""),
        updated_at=datetime.now(UTC).isoformat(),
        user_text=str(active.get("user_text") or ""),
    )
    append_goal_record(record)


def record_goal_completed(*, session_id: str, goal_id: str = "") -> None:
    if not _enabled():
        return
    active = _active_goal_for_session(session_id)
    if active is None and not goal_id:
        return
    src = active or {}
    record = OperationalGoalRecord(
        goal_id=str(goal_id or src.get("goal_id") or uuid.uuid4()),
        session_id=session_id,
        headline=str(src.get("headline") or ""),
        provider=str(src.get("provider") or ""),
        status="goal_completed",
        goal_kind=str(src.get("goal_kind") or ""),
        steps_completed=list(src.get("steps_completed") or []),
        steps_pending=[],
        started_at=str(src.get("started_at") or ""),
        updated_at=datetime.now(UTC).isoformat(),
        user_text=str(src.get("user_text") or ""),
    )
    append_goal_record(record)
    _increment_goal_metrics("goal_completed")


def record_goal_blocked(*, session_id: str, reason: str = "") -> None:
    if not _enabled():
        return
    active = _active_goal_for_session(session_id)
    if active is None:
        return
    record = OperationalGoalRecord(
        goal_id=str(active.get("goal_id")),
        session_id=session_id,
        headline=str(active.get("headline") or ""),
        provider=str(active.get("provider") or ""),
        status="goal_blocked",
        goal_kind=str(active.get("goal_kind") or ""),
        steps_completed=list(active.get("steps_completed") or []),
        steps_pending=list(active.get("steps_pending") or []),
        started_at=str(active.get("started_at") or ""),
        updated_at=datetime.now(UTC).isoformat(),
        user_text=reason[:500] or str(active.get("user_text") or ""),
    )
    append_goal_record(record)
    _increment_goal_metrics("goal_blocked")


def record_readonly_goal_completed(
    *,
    session_id: str,
    operation: str,
    provider: str,
    user_text: str,
) -> None:
    """Lightweight completed goal for single-turn readonly operations."""
    if not _enabled():
        return
    now = datetime.now(UTC).isoformat()
    record = OperationalGoalRecord(
        goal_id=str(uuid.uuid4()),
        session_id=session_id,
        headline=f"Readonly: {operation.replace('_', ' ')}",
        provider=provider,
        status="goal_completed",
        goal_kind="readonly_execute",
        steps_completed=[operation],
        steps_pending=[],
        started_at=now,
        updated_at=now,
        user_text=user_text[:500],
    )
    append_goal_record(record)
    _increment_goal_metrics("goal_completed")


def _increment_goal_metrics(event: str) -> None:
    from aethos_core.observability.metrics import increment

    increment(f"operational_{event}")


def goal_completion_summary(*, days: int = 7) -> dict[str, Any]:
    from aethos_core.operational_session.kernel_reality_registry import _day_key

    records = load_goal_records()
    if not records:
        return {
            "goals_started": 0,
            "goals_completed": 0,
            "goals_blocked": 0,
            "goals_abandoned": 0,
            "goal_completion_rate": None,
            "goal_abandonment_rate": None,
            "goal_block_rate": None,
            "meets_20_completed": False,
        }

    scoped = records
    if days:
        cutoff_days = sorted({_day_key(str(r.get("updated_at") or "")) for r in records})[-days:]
        scoped = [r for r in records if _day_key(str(r.get("updated_at") or "")) in cutoff_days]

    started = sum(1 for r in scoped if r.get("status") == "goal_started")
    completed = sum(1 for r in scoped if r.get("status") == "goal_completed")
    blocked = sum(1 for r in scoped if r.get("status") == "goal_blocked")
    abandoned = sum(1 for r in scoped if r.get("status") == "goal_abandoned")
    terminal = completed + blocked + abandoned
    return {
        "goals_started": started,
        "goals_completed": completed,
        "goals_blocked": blocked,
        "goals_abandoned": abandoned,
        "goal_completion_rate": round(completed / terminal, 4) if terminal else None,
        "goal_abandonment_rate": round(abandoned / terminal, 4) if terminal else None,
        "goal_block_rate": round(blocked / terminal, 4) if terminal else None,
        "meets_20_completed": completed >= 20,
    }


def clear_goal_registry_for_tests() -> None:
    with _lock:
        _memory_goals.clear()
    path = _goals_path()
    if path.exists():
        path.unlink()
