# SPDX-License-Identifier: Apache-2.0
"""Operator fatigue prevention — reduce noise and attention exhaustion."""

from __future__ import annotations

from typing import Any

from aethos_core.presence.signal_deduplication import deduplicate_signals


def apply_fatigue_prevention(
    events: list[dict[str, Any]],
    *,
    focus: dict[str, Any] | None = None,
    dismissed_ids: set[str] | None = None,
    budget: int = 12,
) -> dict[str, Any]:
    """Apply dedupe, escalation decay, focus routing, and attention budgeting."""
    deduped = deduplicate_signals(events)
    dismissed = dismissed_ids or set()

    decayed: list[dict[str, Any]] = []
    suppressed = 0
    for event in deduped:
        eid = str(event.get("event_id") or event.get("summary", "")[:40])
        if eid in dismissed:
            priority = str(event.get("priority") or "PASSIVE")
            if priority in ("PASSIVE", "NOTICE"):
                suppressed += 1
                continue
            event = {**event, "priority": "PASSIVE", "fatigue_decay": True}
        decayed.append(event)

    focus_mode = (focus or {}).get("mode")
    if focus_mode == "deployment_debug":
        decayed = [
            e
            for e in decayed
            if float(e.get("context_weight") or 0.5) >= 0.15
            or str(e.get("priority", "")).upper() in ("CRITICAL", "URGENT")
            or "deployment" in str(e.get("summary", "")).lower()
        ]

    decayed.sort(
        key=lambda e: (
            {"CRITICAL": 4, "URGENT": 3, "ELEVATED": 2, "NOTICE": 1, "PASSIVE": 0}.get(str(e.get("priority", "PASSIVE")).upper(), 0),
            e.get("attention_score", 0),
        ),
        reverse=True,
    )
    surfaced = decayed[:budget]
    passive_count = sum(1 for e in deduped if str(e.get("priority", "PASSIVE")).upper() == "PASSIVE")
    fatigue_score = round(min(1.0, suppressed / max(len(events), 1) + passive_count / max(len(deduped), 1) * 0.3), 2)

    return {
        "events": surfaced,
        "dedupe_count": len(events) - len(deduped),
        "suppressed_count": suppressed,
        "surfaced_count": len(surfaced),
        "fatigue_score": fatigue_score,
        "attention_budget": budget,
        "summary": f"Fatigue prevention: {len(events)} → {len(surfaced)} surfaced ({suppressed} decayed).",
    }
