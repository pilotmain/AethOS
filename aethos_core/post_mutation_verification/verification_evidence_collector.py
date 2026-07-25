# SPDX-License-Identifier: Apache-2.0
"""Collect post-mutation verification evidence from execution artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.post_mutation_verification.verification_context import VerificationContext

_STARTUP_MARKERS = (
    "listening",
    "ready",
    "started",
    "startup complete",
    "application startup",
    "boot",
)
_LOW_SIGNAL_MARKERS = (
    "wiredtiger",
    "stale service events",
    "low-signal",
    "no fatal error",
)


@dataclass
class VerificationEvidence:
    provider_command_submitted: bool = False
    execution_completed: bool = False
    logs_after_execution: bool = False
    startup_markers_present: bool = False
    low_signal_logs: bool = False
    service_health: str = "unknown"
    deployment_status_before: str = ""
    deployment_status_after: str = ""
    restart_verification_state: str = ""
    verification_state: str = ""
    verified_flag: bool = False
    new_crash_detected: bool = False
    log_summary: str = ""
    evidence_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_command_submitted": self.provider_command_submitted,
            "execution_completed": self.execution_completed,
            "logs_after_execution": self.logs_after_execution,
            "startup_markers_present": self.startup_markers_present,
            "low_signal_logs": self.low_signal_logs,
            "service_health": self.service_health,
            "deployment_status_before": self.deployment_status_before,
            "deployment_status_after": self.deployment_status_after,
            "restart_verification_state": self.restart_verification_state,
            "verification_state": self.verification_state,
            "verified_flag": self.verified_flag,
            "new_crash_detected": self.new_crash_detected,
            "log_summary": self.log_summary,
            "evidence_notes": list(self.evidence_notes),
        }


def collect_verification_evidence(context: VerificationContext) -> VerificationEvidence:
    params = context.execution_params
    log_text = (context.log_summary or "").lower()
    evidence = VerificationEvidence(
        provider_command_submitted=context.provider_command_submitted,
        execution_completed=context.execution_completed,
        logs_after_execution=bool(log_text),
        service_health=context.service_health,
        deployment_status_before=context.deployment_status_before,
        deployment_status_after=context.deployment_status_after,
        restart_verification_state=context.restart_verification_state,
        verification_state=context.verification_state,
        verified_flag=params.get("verified") is True,
        log_summary=context.log_summary,
    )

    if log_text:
        evidence.startup_markers_present = any(marker in log_text for marker in _STARTUP_MARKERS)
        evidence.low_signal_logs = any(marker in log_text for marker in _LOW_SIGNAL_MARKERS)
        if "restart" in log_text or "deploy" in log_text:
            evidence.logs_after_execution = True

    restart_state = context.restart_verification_state.lower()
    if restart_state in {"restart_transition_detected", "log_restart_detected"}:
        evidence.startup_markers_present = True
        evidence.logs_after_execution = True
    if restart_state in {"restart_unverified", "service_online_but_restart_unproven", "stabilizing", "restart_requested"}:
        evidence.low_signal_logs = True

    before_failed = _is_failed_status(context.deployment_status_before)
    after_failed = _is_failed_status(context.deployment_status_after)
    if after_failed and context.execution_completed:
        evidence.new_crash_detected = True
        evidence.evidence_notes.append("Service still appears failed after mutation.")
    elif before_failed and not after_failed and context.deployment_status_after:
        evidence.evidence_notes.append("Deployment status improved after mutation.")

    if not evidence.logs_after_execution and not context.before_snapshot:
        evidence.evidence_notes.append("Missing post-execution log evidence.")
    elif evidence.low_signal_logs:
        evidence.evidence_notes.append("Logs only show low-signal startup/storage activity.")

    readonly = _readonly_summary(context)
    if readonly:
        evidence.log_summary = evidence.log_summary or readonly
        low = readonly.lower()
        if any(marker in low for marker in _LOW_SIGNAL_MARKERS):
            evidence.low_signal_logs = True

    return evidence


def _readonly_summary(context: VerificationContext) -> str:
    artifact = context.verification_artifact or {}
    evidence = artifact.get("evidence") if isinstance(artifact, dict) else None
    if isinstance(evidence, dict):
        readonly = evidence.get("readonly_execution") or {}
        if isinstance(readonly, dict):
            return str(readonly.get("summary") or "")
    return ""


def _is_failed_status(status: str) -> bool:
    low = str(status or "").lower()
    return low in {"failed", "crashed", "error", "unhealthy"}
