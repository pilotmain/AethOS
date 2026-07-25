# SPDX-License-Identifier: Apache-2.0
"""Universal provider evidence bundle — tool output to governed claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

_STARTUP_MARKERS = (
    "application startup complete",
    "application startup",
    "startup complete",
    "started server",
    "listening on",
    "ready to accept",
    "booting worker",
    "starting container",
)


@dataclass
class UniversalEvidenceBundle:
    provider: str
    operation: str
    target: dict[str, Any]
    command_submitted: bool = False
    command_name: str | None = None
    command_response: dict[str, Any] = field(default_factory=dict)
    approved_at: str | None = None
    logs_after_approval: list[dict[str, Any]] = field(default_factory=list)
    latest_log_timestamp: str | None = None
    startup_log_observed_after_approval: bool = False
    health: str = "unknown"
    verification_status: str = "unknown"
    diagnosis: dict[str, Any] | None = None
    next_action: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "operation": self.operation,
            "target": dict(self.target),
            "command_submitted": self.command_submitted,
            "command_name": self.command_name,
            "command_response": dict(self.command_response),
            "approved_at": self.approved_at,
            "logs_after_approval": list(self.logs_after_approval),
            "latest_log_timestamp": self.latest_log_timestamp,
            "startup_log_observed_after_approval": self.startup_log_observed_after_approval,
            "health": self.health,
            "verification_status": self.verification_status,
            "diagnosis": self.diagnosis,
            "next_action": self.next_action,
        }


def is_startup_log_message(message: str) -> bool:
    lower = (message or "").lower()
    return any(marker in lower for marker in _STARTUP_MARKERS)


def detect_startup_after_approval(
    entries: list[dict[str, Any]],
    *,
    approval_time: str | None,
) -> tuple[bool, dict[str, Any] | None]:
    """Scan all log lines — not only the latest — for startup evidence after approval."""
    if not entries or not approval_time:
        return False, None

    from aethos_core.providers.railway.hardening.restart_transition import _parse_datetime
    from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

    approved_dt = _parse_datetime(approval_time)
    if approved_dt is None:
        return False, None

    best: dict[str, Any] | None = None
    for row in entries:
        message = str(row.get("message") or row.get("text") or "")
        if not is_startup_log_message(message):
            continue
        ts_raw = row.get("timestamp") or row.get("created") or row.get("created_at")
        ts = normalize_railway_timestamp_to_utc(ts_raw) if ts_raw is not None else None
        if ts is None:
            continue
        ts_dt = _parse_datetime(ts)
        if ts_dt is None or ts_dt <= approved_dt:
            continue
        candidate = {"timestamp": ts, "message": message, "level": row.get("level") or "INFO"}
        if best is None or ts > str(best.get("timestamp") or ""):
            best = candidate

    return best is not None, best


def logs_after_approval(entries: list[dict[str, Any]], *, approval_time: str | None) -> list[dict[str, Any]]:
    if not approval_time:
        return list(entries)
    from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

    since = normalize_railway_timestamp_to_utc(approval_time) or approval_time
    out: list[dict[str, Any]] = []
    for row in entries:
        ts = normalize_railway_timestamp_to_utc(row.get("timestamp") or row.get("created") or row.get("created_at"))
        if ts and ts > since:
            out.append({**row, "timestamp": ts})
    return out


def latest_log_timestamp(entries: list[dict[str, Any]]) -> str | None:
    from aethos_core.providers.railway.railway_log_evidence import normalize_railway_timestamp_to_utc

    latest: str | None = None
    for row in entries:
        ts = normalize_railway_timestamp_to_utc(row.get("timestamp") or row.get("created") or row.get("created_at"))
        if ts and (latest is None or ts > latest):
            latest = ts
    return latest


def resolve_command_state(job: Any) -> tuple[bool, str | None]:
    """Resolve command_submitted and command_name from job params and evidence bundle."""
    params = getattr(job, "params", None) or {}
    artifact = dict(params.get("mutation_execution") or {})
    bundle = dict(params.get("provider_evidence_bundle") or artifact.get("provider_evidence_bundle") or {})
    provider_result = dict(artifact.get("provider_result") or params.get("provider_result") or {})

    command_name = (
        bundle.get("command")
        or params.get("command")
        or artifact.get("command")
        or provider_result.get("command")
        or (bundle.get("provider_response") or {}).get("graphql_operation")
    )
    submitted = bool(
        params.get("restart_command_submitted")
        or artifact.get("restart_command_submitted")
        or bundle.get("command_submitted")
        or provider_result.get("restart_command_submitted")
        or provider_result.get("command_submitted")
        or (bundle.get("evidence") or {}).get("restart_command_submitted")
    )
    if not submitted and params.get("execution_state") in {
        "provider_mutation_requested",
        "execution_stabilizing",
        "execution_completed",
    }:
        submitted = bool(command_name)
    return submitted, str(command_name) if command_name else None


def build_universal_evidence_from_job(job: Any, *, log_entries: list[dict[str, Any]] | None = None) -> UniversalEvidenceBundle:
    params = getattr(job, "params", None) or {}
    target = dict(params.get("target") or {})
    provider = str(params.get("provider") or "railway")
    operation = str(params.get("operation_type") or "restart")
    command_submitted, command_name = resolve_command_state(job)

    bundle = dict(params.get("provider_evidence_bundle") or {})
    approved_at = str(
        params.get("mutation_execution_approved_at_iso")
        or bundle.get("approved_at")
        or ""
    ) or None

    entries = list(log_entries or [])
    if not entries:
        entries = list(bundle.get("logs_excerpt") or [])

    post_approval = logs_after_approval(entries, approval_time=approved_at)
    startup, _startup_row = detect_startup_after_approval(entries, approval_time=approved_at)
    latest_ts = latest_log_timestamp(entries)

    health = str(params.get("restart_service_health") or (bundle.get("evidence") or {}).get("health_confirmed") or "unknown")
    if health is True:
        health = "online"
    elif health is False:
        health = "unknown"

    verification_status = str(
        params.get("restart_verification_state")
        or (bundle.get("verification") or {}).get("status")
        or "unknown"
    )

    from aethos_core.providers.railway.hardening.restart_transition import verify_restart_via_logs

    proof = verify_restart_via_logs(
        logs_before_latest=None,
        logs_after_latest=latest_ts,
        approved_at=approved_at,
        logs_after=[row for row in entries if row.get("timestamp")],
    )
    if startup or proof.get("detected"):
        if verification_status in {"unknown", "stabilizing", "restart_requested"}:
            verification_status = "restart_evidence_detected"

    next_action = None
    if not command_submitted:
        next_action = "confirm provider command was submitted"
    elif not startup and approved_at and latest_ts and not proof.get("detected"):
        next_action = "fetch fresh runtime logs after approval"
    elif startup:
        next_action = "restart verification supported by runtime startup logs"

    return UniversalEvidenceBundle(
        provider=provider,
        operation=operation,
        target={
            "service_name": str(params.get("target_name") or target.get("service_name") or ""),
            "project_name": str(target.get("project_name") or ""),
            "environment": str(target.get("environment") or "production"),
            "service_id": str(target.get("service_id") or ""),
        },
        command_submitted=command_submitted,
        command_name=command_name,
        command_response=dict(bundle.get("provider_response") or params.get("provider_result") or {}),
        approved_at=approved_at,
        logs_after_approval=post_approval,
        latest_log_timestamp=latest_ts,
        startup_log_observed_after_approval=startup,
        health=health,
        verification_status=verification_status,
        diagnosis=dict(bundle.get("diagnosis") or params.get("provider_diagnosis") or {}) or None,
        next_action=next_action,
    )
