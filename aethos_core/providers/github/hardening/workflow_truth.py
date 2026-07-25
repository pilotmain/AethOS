# SPDX-License-Identifier: Apache-2.0
"""GitHub workflow truth — actual workflow completion proof."""

from __future__ import annotations

from typing import Any


def assess_workflow_truth(*, provider_result: dict[str, Any], readonly_artifact: dict[str, Any]) -> dict[str, Any]:
    conclusion = str(provider_result.get("conclusion") or provider_result.get("status") or "").lower()
    summary = str(readonly_artifact.get("summary") or "").lower()
    completed = conclusion in ("success", "completed") or "completed" in summary
    failed = conclusion in ("failure", "failed", "cancelled") or "failed" in summary
    return {
        "workflow_completed": completed and not failed,
        "critical_failures": failed,
        "conclusion": conclusion or None,
        "run_detected": bool(provider_result.get("run_id") or provider_result.get("new_run_id")),
    }
