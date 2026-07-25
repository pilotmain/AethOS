# SPDX-License-Identifier: Apache-2.0
"""Approve provider E2E orchestration jobs — Mission Control gate."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.provider_e2e_orchestration.approval_gate import (
    ProviderE2EApprovalError,
    build_approval_gate_validation_report,
    validate_approval_gate,
)


def approve_provider_e2e_orchestration(job_id: str) -> tuple[Any, dict[str, Any]]:
    """Validate gates, stamp approval, enqueue orchestration execution."""
    from aethos_core.runtime.jobs import job_store

    job = job_store.get(job_id)
    gate = validate_approval_gate(job, for_execution=False)
    if not gate.ok:
        raise ProviderE2EApprovalError(gate.detail or gate.failure_state or "approval blocked")

    approval_id = f"e2e-approval-{job_id}-{int(datetime.now(UTC).timestamp())}"
    job.params["provider_e2e_approved"] = True
    job.params["approval_id"] = approval_id
    job.params["execution_status"] = "approved"
    job.params["approval_gate_report"] = build_approval_gate_validation_report(gate)
    job.params["provider_e2e_approved_at_iso"] = datetime.now(UTC).isoformat()

    from aethos_core.runtime.job_executor import job_executor

    job_executor.enqueue(job_id)
    return job, {"approval_id": approval_id, "gate": job.params["approval_gate_report"]}
