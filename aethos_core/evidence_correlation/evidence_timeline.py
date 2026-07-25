# SPDX-License-Identifier: Apache-2.0
"""Evidence timeline construction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from aethos_core.evidence_correlation.evidence_freshness import parse_timestamp


@dataclass
class TimelineEntry:
    timestamp: str
    source: str
    kind: str
    summary: str


def build_evidence_timeline(
    *,
    logs: list[dict[str, Any]],
    events: list[dict[str, Any]],
    current_status: str = "",
) -> list[TimelineEntry]:
    entries: list[tuple[Any, TimelineEntry]] = []

    for log in logs:
        ts = parse_timestamp(log.get("timestamp") or log.get("time") or log.get("created_at"))
        message = str(log.get("message") or log.get("msg") or "")[:160]
        entries.append(
            (
                ts,
                TimelineEntry(
                    timestamp=(ts.isoformat() if ts else "unknown"),
                    source="runtime_logs",
                    kind="log",
                    summary=message or "log line",
                ),
            )
        )

    for event in events:
        ts = parse_timestamp(event.get("created_at"))
        state = str(event.get("state") or "unknown")
        message = str(event.get("message") or f"deployment state={state}")[:160]
        entries.append(
            (
                ts,
                TimelineEntry(
                    timestamp=(ts.isoformat() if ts else "unknown"),
                    source="service_events",
                    kind="event",
                    summary=f"{state}: {message}",
                ),
            )
        )

    if current_status:
        entries.append(
            (
                None,
                TimelineEntry(
                    timestamp="current",
                    source="provider_inventory",
                    kind="status",
                    summary=f"current status={current_status}",
                ),
            )
        )

    entries.sort(key=lambda item: (item[0] is None, item[0] or ""), reverse=True)
    return [entry for _, entry in entries]
