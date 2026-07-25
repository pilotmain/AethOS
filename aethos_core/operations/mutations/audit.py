# SPDX-License-Identifier: Apache-2.0
"""Mutation audit record schema — evidence-first."""

from __future__ import annotations

from typing import Any


def build_audit_stub(
    *,
    request: str,
    provider: str,
    operation_type: str,
    target_name: str | None,
    risk_tier: str,
    approver: str | None = None,
    result: str = "design_only_blocked",
) -> dict[str, Any]:
    return {
        "request": request,
        "provider": provider,
        "operation_type": operation_type,
        "target_name": target_name,
        "risk_tier": risk_tier,
        "approver": approver,
        "approved_actions": [],
        "before_state": None,
        "after_state": None,
        "evidence": [],
        "result": result,
        "phase": "9.6_governed_execution",
    }


def finalize_audit_record(
    stub: dict[str, Any],
    *,
    execution_artifact: dict[str, Any],
    job_id: str | None = None,
) -> dict[str, Any]:
    record = dict(stub)
    record["job_id"] = job_id
    record["after_state"] = execution_artifact.get("provider_result")
    record["evidence"] = [
        {
            "kind": "mutation_execution_artifact",
            "executed": execution_artifact.get("executed"),
            "provider": execution_artifact.get("provider"),
            "operation_type": execution_artifact.get("operation_type"),
        }
    ]
    if execution_artifact.get("verification_job_id"):
        record["evidence"].append(
            {"kind": "verification_job", "job_id": execution_artifact["verification_job_id"]}
        )
    return record
