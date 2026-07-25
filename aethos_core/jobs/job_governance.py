# SPDX-License-Identifier: Apache-2.0
"""Job governance — approval and safety rules."""

from __future__ import annotations

from typing import Any

from aethos_core.jobs.job_registry import BLOCKED_JOB_ACTIONS, DURABLE_JOB_TYPES, MUTATION_JOB_TYPES


def assess_job_governance(*, job_type: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    params = params or {}
    action = str(params.get("action") or job_type)
    if action in BLOCKED_JOB_ACTIONS:
        return {"allowed": False, "reason": "blocked_action", "requires_approval": False}
    spec = DURABLE_JOB_TYPES.get(job_type)
    if spec:
        return {
            "allowed": True,
            "requires_approval": bool(spec.get("requires_approval")),
            "readonly": bool(spec.get("readonly", True)),
            "reason": "durable_readonly_job",
        }
    if job_type in MUTATION_JOB_TYPES:
        return {"allowed": True, "requires_approval": True, "readonly": False, "reason": "mutation_requires_approval"}
    return {"allowed": False, "reason": "unknown_job_type", "requires_approval": False}
