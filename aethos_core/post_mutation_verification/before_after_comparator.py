# SPDX-License-Identifier: Apache-2.0
"""Before/after comparison for post-mutation verification."""

from __future__ import annotations

from dataclasses import dataclass

from aethos_core.post_mutation_verification.verification_evidence_collector import VerificationEvidence


@dataclass
class BeforeAfterComparison:
    before_status: str
    after_status: str
    before_evidence: str
    after_evidence: str
    after_logs: str
    after_health: str
    health_improved: bool
    health_unchanged_failed: bool
    logs_after_restart_present: bool
    new_crash_after_restart: bool
    change_summary: str

    def to_dict(self) -> dict[str, str]:
        return {
            "before_status": self.before_status,
            "after_status": self.after_status,
            "before_evidence": self.before_evidence,
            "after_evidence": self.after_evidence,
            "after_logs": self.after_logs,
            "after_health": self.after_health,
            "change_summary": self.change_summary,
        }


def compare_before_after(evidence: VerificationEvidence) -> BeforeAfterComparison:
    before_status = evidence.deployment_status_before or "failed"
    after_status = evidence.deployment_status_after or "unknown"
    before_evidence = _before_evidence_phrase(evidence)
    after_evidence = _after_evidence_phrase(evidence)
    after_logs = evidence.log_summary or "not collected yet"
    after_health = evidence.service_health or "unknown"

    before_failed = _failed(before_status) or _failed(after_health)
    after_failed = _failed(after_status) or _failed(after_health)
    health_improved = before_failed and not after_failed and after_status != "unknown"
    health_unchanged_failed = before_failed and after_failed
    logs_present = evidence.logs_after_execution or evidence.startup_markers_present
    new_crash = evidence.new_crash_detected

    change_parts: list[str] = []
    if health_improved:
        change_parts.append("Service health appears improved after restart.")
    elif health_unchanged_failed:
        change_parts.append("Service still appears failed after restart.")
    elif evidence.restart_verification_state == "stabilizing":
        change_parts.append("Restart submitted; service is still stabilizing.")
    elif evidence.low_signal_logs:
        change_parts.append("Restart evidence is present but inconclusive.")
    else:
        change_parts.append("Outcome is not fully verified yet.")

    if logs_present and evidence.startup_markers_present:
        change_parts.append("Post-restart logs show startup/recovery markers.")
    elif evidence.low_signal_logs:
        change_parts.append("Logs only show low-signal WiredTiger or stale event activity.")

    if new_crash:
        change_parts.append("New failure signals appeared after the mutation.")

    return BeforeAfterComparison(
        before_status=before_status,
        after_status=after_status,
        before_evidence=before_evidence,
        after_evidence=after_evidence,
        after_logs=after_logs,
        after_health=after_health,
        health_improved=health_improved,
        health_unchanged_failed=health_unchanged_failed,
        logs_after_restart_present=logs_present,
        new_crash_after_restart=new_crash,
        change_summary=" ".join(change_parts),
    )


def _before_evidence_phrase(evidence: VerificationEvidence) -> str:
    if evidence.low_signal_logs or "wiredtiger" in evidence.log_summary.lower():
        return "WiredTiger logs, stale/low-signal events"
    if evidence.deployment_status_before:
        return f"deployment status: {evidence.deployment_status_before}"
    return "failed service context before restart"


def _after_evidence_phrase(evidence: VerificationEvidence) -> str:
    if evidence.deployment_status_after:
        return f"deployment status: {evidence.deployment_status_after}"
    if evidence.restart_verification_state:
        return evidence.restart_verification_state.replace("_", " ")
    if evidence.log_summary:
        return evidence.log_summary[:160]
    return "post-restart evidence not yet collected"


def _failed(value: str) -> bool:
    low = str(value or "").lower()
    return low in {"failed", "crashed", "error", "unhealthy"}
