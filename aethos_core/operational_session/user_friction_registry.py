# SPDX-License-Identifier: Apache-2.0
"""KERNEL_REALITY_PROOF_001 Phase 9 — user friction and retry evidence."""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_lock = threading.Lock()
_session_state: dict[str, dict[str, Any]] = {}


@dataclass
class FrictionSnapshot:
    session_id: str
    repeated_question_count: int = 0
    retry_count: int = 0
    clarification_count: int = 0
    fallback_count: int = 0
    correction_count: int = 0
    last_requests: list[str] | None = None

    def __post_init__(self) -> None:
        if self.last_requests is None:
            self.last_requests = []


def _store_dir() -> Path:
    from aethos_core.operational_session.kernel_reality_registry import _store_dir as base

    return base()


def _friction_path() -> Path:
    return _store_dir() / "friction_events.jsonl"


def _enabled() -> bool:
    from aethos_core.operational_session.kernel_reality_registry import reality_capture_enabled

    return reality_capture_enabled()


def _normalize_request(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())[:200]


def record_friction_event(
    *,
    session_id: str,
    request: str,
    ok: bool,
    intent: str,
    fallback_used: bool = False,
    provider_misroute: bool = False,
    manual_correction: bool = False,
) -> dict[str, Any]:
    if not _enabled():
        return {}

    norm = _normalize_request(request)
    with _lock:
        state = dict(_session_state.get(session_id) or {})
        last_requests: list[str] = list(state.get("last_requests") or [])
        repeated = int(state.get("repeated_question_count") or 0)
        retry = int(state.get("retry_count") or 0)
        clarify = int(state.get("clarification_count") or 0)
        fallback = int(state.get("fallback_count") or 0)
        correction = int(state.get("correction_count") or 0)

        if norm and norm in last_requests[-3:]:
            repeated += 1
        if norm:
            last_requests.append(norm)
            last_requests = last_requests[-10:]

        if "needs_target" in intent or "clarification" in intent.lower():
            clarify += 1
        if fallback_used:
            fallback += 1
        if provider_misroute or manual_correction:
            correction += 1
        if not ok and norm:
            state["last_failed_request"] = norm
        elif ok and state.get("last_failed_request") == norm:
            retry += 1
            state.pop("last_failed_request", None)

        state.update(
            {
                "repeated_question_count": repeated,
                "retry_count": retry,
                "clarification_count": clarify,
                "fallback_count": fallback,
                "correction_count": correction,
                "last_requests": last_requests,
            }
        )
        _session_state[session_id] = state

    event = {
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id,
        "request": request[:200],
        "ok": ok,
        "intent": intent,
        **state,
    }
    with _lock:
        if _enabled():
            with _friction_path().open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(event, ensure_ascii=False) + "\n")

    from aethos_core.observability.metrics import increment

    if repeated:
        increment("user_repeated_question_total")
    if retry:
        increment("user_retry_total")
    if clarify:
        increment("user_clarification_total")
    return event


def load_friction_events(*, limit: int = 5000) -> list[dict[str, Any]]:
    path = _friction_path()
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit and len(rows) > limit:
        return rows[-limit:]
    return rows


def friction_summary(*, days: int = 7) -> dict[str, Any]:
    from aethos_core.operational_session.kernel_reality_registry import _day_key

    events = load_friction_events()
    if not events:
        return {
            "repeated_question_count": 0,
            "retry_count": 0,
            "clarification_count": 0,
            "fallback_count": 0,
            "correction_count": 0,
            "friction_trend": "unknown",
            "declining_friction": False,
        }

    if days:
        day_keys = sorted({_day_key(str(e.get("timestamp") or "")) for e in events})[-days:]
        events = [e for e in events if _day_key(str(e.get("timestamp") or "")) in day_keys]

    repeated = sum(int(e.get("repeated_question_count") or 0) for e in events)
    retry = sum(int(e.get("retry_count") or 0) for e in events)
    clarify = sum(int(e.get("clarification_count") or 0) for e in events)
    fallback = sum(int(e.get("fallback_count") or 0) for e in events)
    correction = sum(int(e.get("correction_count") or 0) for e in events)

    trend = _friction_trend(events, days=days)
    return {
        "repeated_question_count": repeated,
        "retry_count": retry,
        "clarification_count": clarify,
        "fallback_count": fallback,
        "correction_count": correction,
        "friction_trend": trend,
        "declining_friction": trend == "declining",
        "total_friction_events": len(events),
    }


def _friction_trend(events: list[dict], *, days: int) -> str:
    from aethos_core.operational_session.kernel_reality_registry import _day_key

    by_day: dict[str, int] = {}
    for event in events:
        day = _day_key(str(event.get("timestamp") or ""))
        friction = sum(
            int(event.get(k) or 0)
            for k in ("repeated_question_count", "retry_count", "clarification_count", "correction_count")
        )
        by_day[day] = by_day.get(day, 0) + friction
    keys = sorted(by_day.keys())
    if len(keys) < 2:
        return "insufficient_data"
    mid = len(keys) // 2
    first = sum(by_day[k] for k in keys[:mid])
    second = sum(by_day[k] for k in keys[mid:])
    if second < first:
        return "declining"
    if second > first:
        return "rising"
    return "stable"


def clear_friction_registry_for_tests() -> None:
    with _lock:
        _session_state.clear()
    path = _friction_path()
    if path.exists():
        path.unlink()
