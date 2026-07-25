# SPDX-License-Identifier: Apache-2.0
"""Railway restart transition verification — prove deployment changed after approval."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.hardening.health_observer import observe_health_recovery

RESTART_REQUESTED = "restart_requested"
RESTART_TRANSITION_DETECTED = "restart_transition_detected"
RESTART_UNVERIFIED = "restart_unverified"
SERVICE_ONLINE_BUT_RESTART_UNPROVEN = "service_online_but_restart_unproven"
VERIFICATION_FAILED = "verification_failed"
STABILIZING = "stabilizing"
LOG_RESTART_DETECTED = "log_restart_detected"

_RESTART_LOG_MARKERS = (
    "restart",
    "starting",
    "started",
    "boot",
    "listening",
    "ready",
    "deploy",
    "application startup complete",
    "application startup",
    "startup complete",
)


@dataclass
class RailwayDeploymentSnapshot:
    service_id: str
    active_deployment_id: str | None = None
    active_deployment_created_at: str | None = None
    latest_deployment_id: str | None = None
    latest_deployment_status: str | None = None
    captured_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "active_deployment_id": self.active_deployment_id,
            "active_deployment_created_at": self.active_deployment_created_at,
            "latest_deployment_id": self.latest_deployment_id,
            "latest_deployment_status": self.latest_deployment_status,
            "captured_at": self.captured_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> RailwayDeploymentSnapshot | None:
        if not isinstance(data, dict) or not data.get("service_id"):
            return None
        return cls(
            service_id=str(data.get("service_id") or ""),
            active_deployment_id=_optional_str(data.get("active_deployment_id")),
            active_deployment_created_at=_optional_str(data.get("active_deployment_created_at")),
            latest_deployment_id=_optional_str(data.get("latest_deployment_id")),
            latest_deployment_status=_optional_str(data.get("latest_deployment_status")),
            captured_at=str(data.get("captured_at") or ""),
        )


@dataclass
class RestartVerificationResult:
    state: str
    verified: bool
    transition_detected: bool
    service_online: bool
    provider_request_accepted: bool
    summary: str
    before_snapshot: dict[str, Any]
    after_snapshot: dict[str, Any] | None = None
    provider_request: str = "unknown"
    restart_transition: str = "not_detected"
    service_health: str = "unknown"
    final_verification: str = "unverified"
    restart_command_submitted: bool = False
    transition_proof: str = "none"
    checks: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "verified": self.verified,
            "transition_detected": self.transition_detected,
            "service_online": self.service_online,
            "provider_request_accepted": self.provider_request_accepted,
            "summary": self.summary,
            "before_snapshot": dict(self.before_snapshot),
            "after_snapshot": dict(self.after_snapshot) if self.after_snapshot else None,
            "provider_request": self.provider_request,
            "restart_transition": self.restart_transition,
            "service_health": self.service_health,
            "final_verification": self.final_verification,
            "restart_command_submitted": self.restart_command_submitted,
            "transition_proof": self.transition_proof,
            "checks": list(self.checks),
        }


def _optional_str(value: Any) -> str | None:
    text = str(value or "").strip()
    return text or None


def capture_railway_deployment_snapshot(
    token: str,
    service_id: str,
    *,
    captured_at: str | None = None,
) -> RailwayDeploymentSnapshot:
    from aethos_core.providers.railway.api_client import list_service_deployments

    deployments = list_service_deployments(token, service_id=service_id, limit=5)
    return snapshot_from_deployments(
        service_id,
        deployments,
        captured_at or datetime.now(UTC).isoformat(),
    )


def snapshot_from_deployments(
    service_id: str,
    deployments: list[dict[str, Any]],
    captured_at: str,
) -> RailwayDeploymentSnapshot:
    latest = deployments[0] if deployments else {}
    dep_id = _optional_str(latest.get("id"))
    created_at = _optional_str(latest.get("created_at"))
    status = _optional_str(latest.get("state"))
    return RailwayDeploymentSnapshot(
        service_id=service_id,
        active_deployment_id=dep_id,
        active_deployment_created_at=created_at,
        latest_deployment_id=dep_id,
        latest_deployment_status=status,
        captured_at=captured_at,
    )


def _parse_datetime(value: str | datetime | float | int | None) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=UTC)
    text = str(value).strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def _timestamp_after(value: str | None, reference: datetime) -> bool:
    parsed = _parse_datetime(value)
    if parsed is None:
        return False
    return parsed > reference


def _extract_deployments_from_readonly(readonly_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    deployments = readonly_artifact.get("deployments")
    if isinstance(deployments, list):
        return [row for row in deployments if isinstance(row, dict)]
    evidence = readonly_artifact.get("evidence") or readonly_artifact.get("items") or []
    if isinstance(evidence, list):
        rows: list[dict[str, Any]] = []
        for item in evidence:
            if isinstance(item, dict) and item.get("id"):
                rows.append(item)
        if rows:
            return rows
    return []


def extract_after_snapshot_from_readonly(
    *,
    readonly_artifact: dict[str, Any],
    service_id: str,
) -> RailwayDeploymentSnapshot | None:
    deployments = _extract_deployments_from_readonly(readonly_artifact)
    if not deployments:
        return None
    captured_at = str(readonly_artifact.get("captured_at") or datetime.now(UTC).isoformat())
    return snapshot_from_deployments(service_id, deployments, captured_at)


def _resolve_after_snapshot(
    *,
    service_id: str,
    provider_result: dict[str, Any],
    readonly_artifact: dict[str, Any],
    explicit_after: RailwayDeploymentSnapshot | dict[str, Any] | None,
) -> RailwayDeploymentSnapshot | None:
    if explicit_after is not None:
        if isinstance(explicit_after, RailwayDeploymentSnapshot):
            return explicit_after
        parsed = RailwayDeploymentSnapshot.from_dict(explicit_after)
        if parsed:
            return parsed

    rollback = provider_result.get("rollback_metadata") or {}
    if isinstance(rollback, dict):
        after_raw = rollback.get("deployment_snapshot_after")
        parsed = RailwayDeploymentSnapshot.from_dict(after_raw if isinstance(after_raw, dict) else None)
        if parsed:
            return parsed

    return extract_after_snapshot_from_readonly(readonly_artifact=readonly_artifact, service_id=service_id)


def _deployment_id(snapshot: RailwayDeploymentSnapshot | None) -> str | None:
    if snapshot is None:
        return None
    return snapshot.active_deployment_id or snapshot.latest_deployment_id


def _deployment_created_at(snapshot: RailwayDeploymentSnapshot | None) -> str | None:
    if snapshot is None:
        return None
    return snapshot.active_deployment_created_at


def _detect_transition(
    *,
    before: RailwayDeploymentSnapshot,
    after: RailwayDeploymentSnapshot,
    approved_at: datetime | None,
) -> bool:
    before_id = _deployment_id(before)
    after_id = _deployment_id(after)
    if before_id and after_id and before_id != after_id:
        return True
    after_created = _deployment_created_at(after)
    if approved_at and after_created and _timestamp_after(after_created, approved_at):
        return True
    before_created = _deployment_created_at(before)
    if before_created and after_created and after_created != before_created:
        if approved_at is None or _timestamp_after(after_created, approved_at):
            return True
    return False


def verify_restart_via_logs(
    *,
    logs_before_latest: str | None,
    logs_after_latest: str | None,
    approved_at: datetime | str | float | None,
    logs_after: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    approved_dt = _parse_datetime(approved_at)
    after_latest = logs_after_latest
    if logs_after and approved_dt:
        for row in logs_after:
            ts = _parse_datetime(row.get("timestamp"))
            if ts and ts > approved_dt:
                message = str(row.get("message") or "").lower()
                if any(marker in message for marker in _RESTART_LOG_MARKERS):
                    return {
                        "detected": True,
                        "latest_timestamp": str(row.get("timestamp")),
                        "summary": "Railway deployment logs show activity after approval.",
                    }
    if after_latest and logs_before_latest and after_latest > logs_before_latest:
        if approved_dt is None or _timestamp_after(after_latest, approved_dt):
            return {
                "detected": True,
                "latest_timestamp": after_latest,
                "summary": "Railway deployment log timestamp advanced after approval.",
            }
    if after_latest and approved_dt and _timestamp_after(after_latest, approved_dt):
        return {
            "detected": True,
            "latest_timestamp": after_latest,
            "summary": "Railway deployment log timestamp is newer than approval time.",
        }
    return {"detected": False, "latest_timestamp": after_latest, "summary": "No post-approval log activity detected."}


def _log_evidence_from_provider(provider_result: dict[str, Any]) -> dict[str, Any]:
    rollback = provider_result.get("rollback_metadata") or {}
    if not isinstance(rollback, dict):
        rollback = {}
    evidence = provider_result.get("evidence") or {}
    if not isinstance(evidence, dict):
        evidence = {}
    return {
        "logs_before_latest_timestamp": rollback.get("logs_before_latest_timestamp") or evidence.get("logs_before_latest_timestamp"),
        "logs_after_latest_timestamp": rollback.get("logs_after_latest_timestamp") or evidence.get("logs_after_latest_timestamp"),
    }


def verify_railway_restart_transition(
    *,
    service_id: str,
    before_snapshot: RailwayDeploymentSnapshot | dict[str, Any],
    approved_at: datetime | str | float | None,
    after_snapshot: RailwayDeploymentSnapshot | dict[str, Any] | None = None,
    provider_result: dict[str, Any] | None = None,
    readonly_artifact: dict[str, Any] | None = None,
    provider_request_accepted: bool | None = None,
) -> RestartVerificationResult:
    """Compare Railway deployment state before and after mutation."""
    provider_result = provider_result or {}
    readonly_artifact = readonly_artifact or {}

    if isinstance(before_snapshot, dict):
        before = RailwayDeploymentSnapshot.from_dict(before_snapshot)
    else:
        before = before_snapshot
    if before is None:
        before = RailwayDeploymentSnapshot(service_id=service_id, captured_at=datetime.now(UTC).isoformat())

    approved_dt = _parse_datetime(approved_at)
    if provider_result.get("restart_command_submitted") is None:
        command_submitted = (
            bool(provider_request_accepted)
            if provider_request_accepted is not None
            else bool(provider_result.get("ok"))
        )
    else:
        command_submitted = bool(provider_result.get("restart_command_submitted"))
    accepted = command_submitted
    health = observe_health_recovery(readonly_artifact=readonly_artifact, provider_result=provider_result)
    service_online = bool(health.get("runtime_reachable"))

    provider_request = "accepted" if command_submitted else ("failed" if not accepted else "unknown")
    service_health = "online" if service_online else "unknown"
    if not command_submitted and not accepted:
        summary = "Railway restart verification failed — restart command was not submitted to the provider."
        return RestartVerificationResult(
            state=VERIFICATION_FAILED,
            verified=False,
            transition_detected=False,
            service_online=service_online,
            provider_request_accepted=False,
            summary=summary,
            before_snapshot=before.to_dict(),
            provider_request="failed",
            restart_transition="not_detected",
            service_health=service_health,
            final_verification="failed",
            restart_command_submitted=False,
            transition_proof="none",
        )
    if not command_submitted:
        summary = (
            "Approval was recorded, but Railway did not show provider-side restart command evidence."
        )
        return RestartVerificationResult(
            state=RESTART_UNVERIFIED,
            verified=False,
            transition_detected=False,
            service_online=service_online,
            provider_request_accepted=False,
            summary=summary,
            before_snapshot=before.to_dict(),
            provider_request="failed",
            restart_transition="not_detected",
            service_health=service_health,
            final_verification="unverified",
            restart_command_submitted=False,
            transition_proof="none",
        )

    after = _resolve_after_snapshot(
        service_id=service_id,
        provider_result=provider_result,
        readonly_artifact=readonly_artifact,
        explicit_after=after_snapshot,
    )

    if after is None:
        summary = (
            "Railway accepted the restart request, but no post-mutation deployment snapshot is available yet."
        )
        return RestartVerificationResult(
            state=STABILIZING,
            verified=False,
            transition_detected=False,
            service_online=service_online,
            provider_request_accepted=True,
            summary=summary,
            before_snapshot=before.to_dict(),
            provider_request="accepted",
            restart_transition="not_detected",
            service_health=service_health,
            final_verification="unverified",
            checks=[{"check": "Provider restart request accepted", "status": "confirmed", "detail": ""}],
        )

    transition_detected = _detect_transition(before=before, after=after, approved_at=approved_dt)
    transition_proof = "deployment" if transition_detected else "none"
    log_evidence = _log_evidence_from_provider(provider_result)
    log_proof = verify_restart_via_logs(
        logs_before_latest=log_evidence.get("logs_before_latest_timestamp"),
        logs_after_latest=log_evidence.get("logs_after_latest_timestamp"),
        approved_at=approved_dt,
    )
    if not transition_detected and log_proof.get("detected"):
        transition_detected = True
        transition_proof = "logs"

    before_id = _deployment_id(before)
    after_id = _deployment_id(after)
    after_created = _deployment_created_at(after)

    checks: list[dict[str, str]] = [
        {"check": "Provider restart command submitted", "status": "confirmed", "detail": ""},
    ]

    if transition_detected:
        proof_label = "deployment transition" if transition_proof == "deployment" else "log activity"
        checks.append(
            {
                "check": f"Restart {proof_label} detected",
                "status": "confirmed",
                "detail": f"{before_id or 'unknown'} -> {after_id or 'unknown'}",
            }
        )
        if service_online:
            checks.append({"check": "Service health recovered", "status": "confirmed", "detail": health.get("summary", "")})
            summary = (
                "Railway shows a new restart/deployment transition after approval, "
                "and the service is reachable again."
            )
            return RestartVerificationResult(
                state=RESTART_TRANSITION_DETECTED if transition_proof == "deployment" else LOG_RESTART_DETECTED,
                verified=True,
                transition_detected=True,
                service_online=True,
                provider_request_accepted=True,
                summary=summary,
                before_snapshot=before.to_dict(),
                after_snapshot=after.to_dict(),
                provider_request="accepted",
                restart_transition="detected",
                service_health="online",
                final_verification="verified",
                restart_command_submitted=True,
                transition_proof=transition_proof,
                checks=checks,
            )
        summary = (
            "Railway shows a restart/deployment transition after approval, "
            "but service health is not confirmed yet."
        )
        return RestartVerificationResult(
            state=STABILIZING,
            verified=False,
            transition_detected=True,
            service_online=False,
            provider_request_accepted=True,
            summary=summary,
            before_snapshot=before.to_dict(),
            after_snapshot=after.to_dict(),
            provider_request="accepted",
            restart_transition="detected",
            service_health=service_health,
            final_verification="unverified",
            checks=checks,
        )

    if service_online:
        summary = (
            "The service is online, but Railway still shows the same active deployment from before approval. "
            "Availability does not prove a restart occurred."
        )
        return RestartVerificationResult(
            state=SERVICE_ONLINE_BUT_RESTART_UNPROVEN,
            verified=False,
            transition_detected=False,
            service_online=True,
            provider_request_accepted=True,
            summary=summary,
            before_snapshot=before.to_dict(),
            after_snapshot=after.to_dict(),
            provider_request="accepted",
            restart_transition="not_detected",
            service_health="online",
            final_verification="unverified",
            checks=checks,
        )

    if before_id and after_id and before_id == after_id and approved_dt and after_created and not _timestamp_after(after_created, approved_dt):
        summary = (
            "Railway still shows the same active deployment from before approval, "
            "and its timestamp is not newer than approval time."
        )
        return RestartVerificationResult(
            state=RESTART_UNVERIFIED,
            verified=False,
            transition_detected=False,
            service_online=False,
            provider_request_accepted=True,
            summary=summary,
            before_snapshot=before.to_dict(),
            after_snapshot=after.to_dict(),
            provider_request="accepted",
            restart_transition="not_detected",
            service_health=service_health,
            final_verification="unverified",
            checks=checks,
        )

    summary = (
        "Railway accepted the restart request, but no deployment/restart transition has been observed yet."
    )
    return RestartVerificationResult(
        state=RESTART_REQUESTED,
        verified=False,
        transition_detected=False,
        service_online=service_online,
        provider_request_accepted=True,
        summary=summary,
        before_snapshot=before.to_dict(),
        after_snapshot=after.to_dict(),
        provider_request="accepted",
        restart_transition="not_detected",
        service_health=service_health,
        final_verification="unverified",
        checks=checks,
    )
