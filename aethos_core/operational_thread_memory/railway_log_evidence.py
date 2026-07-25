# SPDX-License-Identifier: Apache-2.0
"""Structured Railway log entries and timestamp-based restart evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class StructuredLogEntry:
    timestamp: str | None
    level: str
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "message": self.message,
        }


@dataclass
class RestartLogEvidence:
    approval_time: str | None = None
    latest_timestamp: str | None = None
    latest_entry: StructuredLogEntry | None = None
    startup_after_approval: bool = False
    timestamp_after_approval: bool = False
    timestamps_available: bool = False
    logs_unavailable: bool = False
    conclusion: str = "unknown"
    entries: list[StructuredLogEntry] = field(default_factory=list)
    service_health: str = "unknown"
    restart_verification_state: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "approval_time": self.approval_time,
            "latest_timestamp": self.latest_timestamp,
            "latest_entry": self.latest_entry.to_dict() if self.latest_entry else None,
            "startup_after_approval": self.startup_after_approval,
            "timestamp_after_approval": self.timestamp_after_approval,
            "timestamps_available": self.timestamps_available,
            "logs_unavailable": self.logs_unavailable,
            "conclusion": self.conclusion,
            "entries": [entry.to_dict() for entry in self.entries],
            "service_health": self.service_health,
            "restart_verification_state": self.restart_verification_state,
        }


def normalize_log_entries(raw_logs: list[Any] | None) -> list[StructuredLogEntry]:
    entries: list[StructuredLogEntry] = []
    for row in raw_logs or []:
        if isinstance(row, str):
            text = row.strip()
            if text:
                entries.append(StructuredLogEntry(timestamp=None, level="INFO", message=text))
            continue
        if not isinstance(row, dict):
            continue
        message = str(row.get("message") or row.get("text") or row.get("line") or "").strip()
        if not message:
            continue
        timestamp = row.get("timestamp") or row.get("created") or row.get("created_at")
        if timestamp is not None:
            from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

            timestamp = normalize_railway_timestamp_to_utc(timestamp) or timestamp
        level = str(row.get("level") or row.get("severity") or "INFO")
        entries.append(
            StructuredLogEntry(
                timestamp=str(timestamp) if timestamp is not None else None,
                level=level,
                message=message,
            )
        )
    return entries


def latest_structured_log(entries: list[StructuredLogEntry]) -> StructuredLogEntry | None:
    best: StructuredLogEntry | None = None
    for entry in entries:
        if entry.timestamp is None:
            continue
        if best is None or str(entry.timestamp) > str(best.timestamp):
            best = entry
    if best is not None:
        return best
    return entries[-1] if entries else None


def collect_restart_log_evidence(job: Any) -> RestartLogEvidence:
    params = getattr(job, "params", None) or {}
    artifact = dict(params.get("mutation_execution") or {})
    bundle = dict(params.get("provider_evidence_bundle") or artifact.get("provider_evidence_bundle") or {})
    approval_time = str(
        params.get("mutation_execution_approved_at_iso")
        or bundle.get("approved_at")
        or artifact.get("mutation_execution_approved_at_iso")
        or ""
    ) or None

    raw_logs = list(bundle.get("logs_excerpt") or [])
    provider_result = artifact.get("provider_result") or {}
    rollback = provider_result.get("rollback_metadata") or {}
    if not raw_logs:
        raw_logs = list(getattr(job, "logs_after", []) or artifact.get("logs_after") or [])

    entries = normalize_log_entries(raw_logs)
    latest = latest_structured_log(entries)
    timestamps_available = any(entry.timestamp for entry in entries)

    logs_before_latest = rollback.get("logs_before_latest_timestamp")
    logs_after_latest = rollback.get("logs_after_latest_timestamp") or (latest.timestamp if latest else None)

    from aethos_core.providers.railway.hardening.restart_transition import verify_restart_via_logs

    log_proof = verify_restart_via_logs(
        logs_before_latest=str(logs_before_latest) if logs_before_latest else None,
        logs_after_latest=str(logs_after_latest) if logs_after_latest else None,
        approved_at=approval_time,
        logs_after=[entry.to_dict() for entry in entries if entry.timestamp],
    )

    startup_after_approval = False
    startup_row: dict[str, Any] | None = None
    from aethos_core.operational_skill_runtime.evidence_collector import detect_startup_after_approval

    startup_after_approval, startup_row = detect_startup_after_approval(
        [entry.to_dict() for entry in entries],
        approval_time=approval_time,
    )
    if not startup_after_approval and latest and latest.message and bool(log_proof.get("detected")):
        startup_after_approval = "startup" in latest.message.lower() or "application startup" in latest.message.lower()

    restart_state = str(
        params.get("restart_verification_state")
        or (params.get("verification_artifact") or {}).get("evidence", {}).get("restart_verification_state")
        or bundle.get("verification", {}).get("status")
        or ""
    )
    health = str(params.get("restart_service_health") or bundle.get("evidence", {}).get("health_confirmed") or "unknown")
    if health is True:
        health = "online"
    elif health is False:
        health = "unknown"

    evidence = RestartLogEvidence(
        approval_time=approval_time,
        latest_timestamp=(latest.timestamp if latest else None)
        or str(log_proof.get("latest_timestamp") or "")
        or None,
        latest_entry=latest,
        startup_after_approval=startup_after_approval and bool(log_proof.get("detected") or startup_row),
        timestamp_after_approval=bool(log_proof.get("detected") or startup_after_approval),
        timestamps_available=timestamps_available,
        logs_unavailable=not entries,
        entries=entries[-20:],
        service_health=str(health),
        restart_verification_state=restart_state,
    )
    evidence.conclusion = _conclusion_from_evidence(evidence, restart_state=restart_state, log_proof=log_proof)
    return evidence


def refresh_restart_log_evidence(job: Any, *, bypass_cache: bool = True) -> RestartLogEvidence:
    evidence = collect_restart_log_evidence(job)
    params = getattr(job, "params", None) or {}
    restart_state = str(
        params.get("restart_verification_state")
        or (params.get("verification_artifact") or {}).get("evidence", {}).get("restart_verification_state")
        or evidence.restart_verification_state
        or ""
    )
    evidence.restart_verification_state = restart_state

    if not bypass_cache and evidence.entries and evidence.timestamps_available:
        return evidence

    service = str(params.get("target_name") or "")
    if not service:
        target = dict(params.get("target") or {})
        service = str(target.get("service_name") or "")
    if not service:
        if evidence.entries:
            return evidence
        evidence.logs_unavailable = True
        evidence.conclusion = "logs_unavailable"
        return evidence

    try:
        from aethos_core.providers.railway.railway_log_evidence import (
            fetch_fresh_logs_for_verification,
            pick_newer_log_entries,
            resolve_verification_target,
        )

        target = resolve_verification_target(job)
        fresh_payload = fetch_fresh_logs_for_verification(
            target=target,
            approval_time=evidence.approval_time,
            bypass_cache=bypass_cache,
            limit=50,
        )
        fresh_rows = list(fresh_payload.get("logs") or [])
        cached_rows = [entry.to_dict() for entry in evidence.entries]
        selected_rows = pick_newer_log_entries(cached_rows, fresh_rows, prefer_fresh=bypass_cache)

        if not selected_rows and evidence.entries:
            return evidence

        entries = normalize_log_entries(selected_rows)
        latest = latest_structured_log(entries)
        evidence.entries = entries[-50:]
        evidence.timestamps_available = any(entry.timestamp for entry in entries)
        evidence.latest_entry = latest
        evidence.latest_timestamp = latest.timestamp if latest else None
        evidence.logs_unavailable = not entries

        from aethos_core.providers.railway.hardening.restart_transition import verify_restart_via_logs

        log_proof = verify_restart_via_logs(
            logs_before_latest=None,
            logs_after_latest=evidence.latest_timestamp,
            approved_at=evidence.approval_time,
            logs_after=[entry.to_dict() for entry in entries if entry.timestamp],
        )
        evidence.timestamp_after_approval = bool(log_proof.get("detected"))
        from aethos_core.operational_skill_runtime.evidence_collector import detect_startup_after_approval

        startup_detected, startup_row = detect_startup_after_approval(
            [entry.to_dict() for entry in entries],
            approval_time=evidence.approval_time,
        )
        if startup_detected:
            evidence.timestamp_after_approval = True
        if startup_row:
            evidence.startup_after_approval = True
            evidence.latest_timestamp = str(startup_row.get("timestamp") or evidence.latest_timestamp)
            evidence.latest_entry = StructuredLogEntry(
                timestamp=evidence.latest_timestamp,
                level=str(startup_row.get("level") or "INFO"),
                message=str(startup_row.get("message") or ""),
            )
        elif latest and latest.message:
            startup = "startup" in latest.message.lower() or "application startup" in latest.message.lower()
            evidence.startup_after_approval = startup and evidence.timestamp_after_approval
        evidence.conclusion = _conclusion_from_evidence(
            evidence,
            restart_state=restart_state,
            log_proof=log_proof,
        )
    except Exception:
        if evidence.entries and evidence.timestamps_available:
            return evidence
        evidence.logs_unavailable = True
        evidence.conclusion = "logs_unavailable"
    return evidence


def assess_restart_from_logs(*, approval_time: str | None, entries: list[StructuredLogEntry]) -> dict[str, Any]:
    from aethos_core.providers.railway.hardening.restart_transition import verify_restart_via_logs

    latest = latest_structured_log(entries)
    if not entries:
        return {"verified": False, "reason": "no_logs", "latest_timestamp": None}
    if not any(entry.timestamp for entry in entries):
        return {
            "verified": False,
            "reason": "no_timestamps",
            "latest_timestamp": None,
            "message": "Railway returned recent logs, but no timestamp was available in the log payload. I cannot use these logs as restart proof yet.",
        }
    proof = verify_restart_via_logs(
        logs_before_latest=None,
        logs_after_latest=latest.timestamp if latest else None,
        approved_at=approval_time,
        logs_after=[entry.to_dict() for entry in entries if entry.timestamp],
    )
    return {
        "verified": bool(proof.get("detected")),
        "reason": "timestamp_after_approval" if proof.get("detected") else "timestamp_before_approval_or_missing",
        "latest_timestamp": proof.get("latest_timestamp") or (latest.timestamp if latest else None),
        "message": proof.get("summary"),
    }


def _conclusion_from_evidence(
    evidence: RestartLogEvidence,
    *,
    restart_state: str,
    log_proof: dict[str, Any],
) -> str:
    if evidence.logs_unavailable:
        return "logs_unavailable"
    if not evidence.timestamps_available:
        return "logs_without_timestamps"
    if evidence.approval_time and evidence.latest_timestamp and not evidence.timestamp_after_approval:
        return "restart_unconfirmed"
    if restart_state in {"restart_transition_detected", "log_restart_detected", "verified"}:
        return "restart_verified"
    if restart_state in {"restart_unverified", "service_online_but_restart_unproven"}:
        return "restart_unverified"
    if log_proof.get("detected"):
        return "restart_evidence_detected"
    if restart_state in {"stabilizing", "restart_requested", "execution_stabilizing"}:
        if evidence.approval_time and not evidence.timestamp_after_approval:
            return "restart_unconfirmed"
        return "still_stabilizing"
    if restart_state == "execution_failed":
        return "execution_failed"
    return "inconclusive"
