# SPDX-License-Identifier: Apache-2.0
"""Correlated diagnosis from multi-source evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.evidence_correlation.evidence_conflict_detector import ConflictReport, detect_evidence_conflicts
from aethos_core.evidence_correlation.evidence_freshness import (
    assess_event_freshness,
    assess_health_freshness,
    assess_inventory_freshness,
    assess_log_freshness,
    is_low_signal_logs,
    parse_timestamp,
)
from aethos_core.evidence_correlation.evidence_timeline import TimelineEntry, build_evidence_timeline
from aethos_core.evidence_correlation.next_step_planner import NextStepPlan, plan_best_next_step


@dataclass
class CorrelatedDiagnosis:
    correlation_lines: list[str] = field(default_factory=list)
    conclusion: str = ""
    best_next_step: str = ""
    next_step_reason: str = ""
    confidence_note: str = ""
    conflicts: list[str] = field(default_factory=list)
    timeline: list[TimelineEntry] = field(default_factory=list)
    freshness: dict[str, str] = field(default_factory=dict)
    root_cause_confirmed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_lines": list(self.correlation_lines),
            "conclusion": self.conclusion,
            "best_next_step": self.best_next_step,
            "next_step_reason": self.next_step_reason,
            "confidence_note": self.confidence_note,
            "conflicts": list(self.conflicts),
            "freshness": dict(self.freshness),
            "root_cause_confirmed": self.root_cause_confirmed,
        }


def correlate_evidence(
    evidence: dict[str, Any],
    *,
    reference_time: datetime | None = None,
) -> CorrelatedDiagnosis:
    logs = list(evidence.get("logs") or [])
    events = list(evidence.get("events") or [])
    root = dict(evidence.get("root_cause") or {})
    root_category = str(root.get("category") or "")
    service_name = str((evidence.get("target") or {}).get("service") or "")
    current_status = str(evidence.get("status") or evidence.get("deployment_state") or "")
    deployment_state = str(evidence.get("deployment_state") or "")

    logs_freshness = assess_log_freshness(logs, reference_time=reference_time)
    events_freshness = assess_event_freshness(events, reference_time=reference_time)
    inventory_at = parse_timestamp(evidence.get("inventory_collected_at"))
    health_at = parse_timestamp(evidence.get("health_collected_at")) or inventory_at
    inventory_freshness = assess_inventory_freshness(collected_at=inventory_at, reference_time=reference_time)
    health_freshness = assess_health_freshness(collected_at=health_at, reference_time=reference_time)

    low_signal = is_low_signal_logs(logs, root_category=root_category)
    conflicts = detect_evidence_conflicts(
        current_status=current_status,
        deployment_state=deployment_state,
        logs_freshness=logs_freshness,
        events_freshness=events_freshness,
        events=events,
        logs=logs,
        low_signal_logs=low_signal,
    )
    next_step: NextStepPlan = plan_best_next_step(
        service_name=service_name,
        root_category=root_category,
        logs_freshness=logs_freshness,
        events_freshness=events_freshness,
        inventory_freshness=inventory_freshness,
        low_signal_logs=low_signal,
        conflicts=conflicts,
        events_available=bool(events),
    )

    correlation_lines = _correlation_lines(
        logs_freshness=logs_freshness,
        events_freshness=events_freshness,
        inventory_freshness=inventory_freshness,
        health_freshness=health_freshness,
        low_signal=low_signal,
        conflicts=conflicts,
    )
    conclusion = _build_conclusion(
        service_name=service_name,
        current_status=current_status,
        low_signal=low_signal,
        logs_freshness=logs_freshness,
        events_freshness=events_freshness,
        conflicts=conflicts,
        root=root,
    )
    confidence_note = _confidence_note(
        root=root,
        logs_freshness=logs_freshness,
        events_freshness=events_freshness,
        conflicts=conflicts,
        low_signal=low_signal,
    )

    return CorrelatedDiagnosis(
        correlation_lines=correlation_lines,
        conclusion=conclusion,
        best_next_step=next_step.action,
        next_step_reason=next_step.reason,
        confidence_note=confidence_note,
        conflicts=[conflict.summary for conflict in conflicts.conflicts],
        timeline=build_evidence_timeline(logs=logs, events=events, current_status=current_status),
        freshness={
            "runtime_logs": logs_freshness.freshness,
            "service_events": events_freshness.freshness,
            "provider_inventory": inventory_freshness.freshness,
            "health_check": health_freshness.freshness,
        },
        root_cause_confirmed=_root_cause_confirmed(root, conflicts, low_signal),
    )


def _correlation_lines(
    *,
    logs_freshness,
    events_freshness,
    inventory_freshness,
    health_freshness,
    low_signal: bool,
    conflicts: ConflictReport,
) -> list[str]:
    lines = [
        f"- Runtime logs are **{logs_freshness.freshness}**"
        + (" but low-signal." if low_signal and logs_freshness.freshness == "fresh" else "."),
        f"- Service events are **{events_freshness.freshness}** relative to the current failure.",
        f"- Provider inventory is **{inventory_freshness.freshness}**.",
        f"- Health snapshot is **{health_freshness.freshness}**.",
    ]
    for conflict in conflicts.conflicts:
        lines.append(f"- Conflict: {conflict.summary}")
    return lines


def _build_conclusion(
    *,
    service_name: str,
    current_status: str,
    low_signal: bool,
    logs_freshness,
    events_freshness,
    conflicts: ConflictReport,
    root: dict[str, Any],
) -> str:
    label = service_name or "The service"
    status = str(current_status or "unknown").lower()
    unhealthy = status in {"failed", "crashed", "error", "unhealthy"}

    if unhealthy and low_signal and events_freshness.freshness == "stale":
        return (
            f"{label} is unhealthy, but the current root cause is still unconfirmed. "
            "Logs are fresh but only show storage-engine activity, while service events are stale and may not explain the current state."
        )

    if unhealthy and conflicts.has_conflicts and any(c.kind == "success_event_vs_failed_status" for c in conflicts.conflicts):
        return (
            f"{label} remains unhealthy even though the latest available service event shows success. "
            "The current failure is not fully explained by the available service events."
        )

    if root.get("bounded_diagnosis") and unhealthy:
        return (
            f"{label} is unhealthy, but AethOS is keeping this diagnosis bounded until fresher correlated evidence is available."
        )

    if unhealthy:
        return f"{label} is unhealthy. Available evidence supports investigation but not a final root-cause claim yet."

    return f"{label} evidence has been correlated across logs, events, and current status."


def _confidence_note(*, root, logs_freshness, events_freshness, conflicts, low_signal) -> str:
    if root.get("confidence") == "high" and logs_freshness.freshness == "fresh" and events_freshness.freshness == "fresh" and not conflicts.has_conflicts:
        return "Logs and events agree closely — confidence is stronger."
    if low_signal or events_freshness.freshness == "stale" or conflicts.has_conflicts:
        return "Evidence quality is mixed or incomplete — confidence remains bounded."
    if logs_freshness.freshness == "fresh" and events_freshness.freshness == "fresh":
        return "Fresh logs and fresh events align with the current failure state."
    return "More correlated evidence is needed before increasing confidence."


def _root_cause_confirmed(root: dict[str, Any], conflicts: ConflictReport, low_signal: bool) -> bool:
    if low_signal or conflicts.has_conflicts:
        return False
    if root.get("bounded_diagnosis"):
        return False
    return str(root.get("confidence") or "low") in {"high", "medium"} and str(root.get("category") or "") not in {
        "insufficient_evidence",
        "unknown_runtime_failure",
        "database_startup_or_storage_activity",
    }
