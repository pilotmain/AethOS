# SPDX-License-Identifier: Apache-2.0
"""Verification runtime — evidence-first restart/operation verification."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_skill_runtime.evidence_collector import (
    UniversalEvidenceBundle,
    build_universal_evidence_from_job,
    detect_startup_after_approval,
)


def verify_job_evidence(job: Any, *, log_entries: list[dict[str, Any]] | None = None) -> UniversalEvidenceBundle:
    entries = list(log_entries or [])
    if not entries:
        params = getattr(job, "params", None) or {}
        bundle = dict(params.get("provider_evidence_bundle") or {})
        entries = list(bundle.get("logs_excerpt") or [])
    return build_universal_evidence_from_job(job, log_entries=entries)


def verification_summary(bundle: UniversalEvidenceBundle) -> str:
    if bundle.startup_log_observed_after_approval:
        return (
            "Restart evidence detected — startup log observed after approval "
            f"at `{bundle.latest_log_timestamp or 'unknown'}`."
        )
    if bundle.command_submitted and not bundle.logs_after_approval:
        return "Provider command submitted; waiting for post-approval runtime logs."
    if bundle.logs_after_approval and not bundle.startup_log_observed_after_approval:
        return "Logs exist after approval, but no startup marker was detected yet."
    return "Verification inconclusive — insufficient post-approval evidence."
