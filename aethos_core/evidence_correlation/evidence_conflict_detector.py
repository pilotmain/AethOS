# SPDX-License-Identifier: Apache-2.0
"""Detect contradictions across evidence sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.evidence_correlation.evidence_freshness import SourceFreshness, parse_timestamp


@dataclass
class EvidenceConflict:
    kind: str
    summary: str
    detail: str = ""


@dataclass
class ConflictReport:
    conflicts: list[EvidenceConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return bool(self.conflicts)


def detect_evidence_conflicts(
    *,
    current_status: str,
    deployment_state: str,
    logs_freshness: SourceFreshness,
    events_freshness: SourceFreshness,
    events: list[dict[str, Any]],
    logs: list[dict[str, Any]],
    low_signal_logs: bool,
) -> ConflictReport:
    report = ConflictReport()
    status = str(current_status or deployment_state or "").lower()
    is_failed = status in {"failed", "crashed", "error", "unhealthy"}

    latest_success = _latest_event_with_state(events, {"success", "active", "running", "deployed", "completed"})
    latest_failure = _latest_event_with_state(events, {"failed", "crashed", "error", "removed"})

    if is_failed and latest_success and latest_failure:
        success_ts = parse_timestamp(latest_success.get("created_at"))
        failure_ts = parse_timestamp(latest_failure.get("created_at"))
        if success_ts and failure_ts and success_ts >= failure_ts:
            report.conflicts.append(
                EvidenceConflict(
                    kind="success_event_vs_failed_status",
                    summary="Latest service event shows success while current status remains failed.",
                    detail=str(latest_success.get("message") or latest_success.get("state") or ""),
                )
            )

    if is_failed and logs_freshness.freshness == "fresh" and events_freshness.freshness == "stale":
        report.conflicts.append(
            EvidenceConflict(
                kind="fresh_logs_stale_events",
                summary="Runtime logs are current but service events are stale relative to the current failure.",
                detail="Events may not explain the present unhealthy state.",
            )
        )

    if is_failed and low_signal_logs and logs_freshness.freshness in {"fresh", "unknown"}:
        report.conflicts.append(
            EvidenceConflict(
                kind="fresh_low_signal_logs",
                summary="Logs are available but only show low-signal startup/storage activity.",
                detail="Current root cause is still unconfirmed from logs alone.",
            )
        )

    if is_failed and events_freshness.freshness == "stale" and not events:
        report.conflicts.append(
            EvidenceConflict(
                kind="missing_events",
                summary="No usable service events were available for the current failure window.",
            )
        )

    if (
        is_failed
        and latest_failure
        and logs_freshness.latest_timestamp
        and events_freshness.latest_timestamp
        and logs_freshness.latest_timestamp > events_freshness.latest_timestamp
        and (logs_freshness.latest_timestamp - events_freshness.latest_timestamp).days >= 1
    ):
        report.conflicts.append(
            EvidenceConflict(
                kind="log_event_time_skew",
                summary="Log timestamps are much newer than the latest service event.",
                detail="Event history may be incomplete or stale for this failure.",
            )
        )

    return report


def _latest_event_with_state(events: list[dict[str, Any]], states: set[str]) -> dict[str, Any] | None:
    matched = [event for event in events if str(event.get("state") or "").lower() in states]
    if not matched:
        return None
    matched.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return matched[0]
