# SPDX-License-Identifier: Apache-2.0
"""Preflight lifecycle status — approval clarity without execution."""

from __future__ import annotations

from aethos_core.operations.operation_models import OperationPreflight

PREFLIGHT_STATUSES = frozenset(
    {
        "ready_for_approval",
        "ready_for_readonly_diagnostic",
        "needs_information",
        "blocked",
        "superseded",
        "execution_not_enabled",
    }
)


def derive_preflight_status(preflight: OperationPreflight) -> str:
    cap = preflight.current_state or {}
    if preflight.target_status == "ambiguous":
        return "needs_information"
    if preflight.target_status == "missing":
        return "needs_information"
    if preflight.target_status == "blocked_by_browser_runtime":
        if cap.get("api_capable"):
            if preflight.operation_type in ("check_logs", "why_down", "inspect_failed_deployment"):
                return "ready_for_readonly_diagnostic"
            return "ready_for_approval"
        return "blocked"
    if preflight.missing_information:
        return "needs_information"
    extra_blockers = [
        b
        for b in preflight.blockers
        if "Phase 9.2" not in b and "Phase 9.3B" not in b and "not enabled" not in b.lower()
    ]
    if extra_blockers:
        return "blocked"
    if preflight.operation_type in (
        "why_down",
        "inspect_failed_deployment",
        "check_logs",
        "list_deployments",
        "list_domains",
        "project_details",
        "workflow_runs",
        "workflow_diagnostic",
        "workflow_jobs",
    ):
        return "ready_for_readonly_diagnostic"
    return "ready_for_approval"


def preflight_status_label(status: str) -> str:
    labels = {
        "ready_for_approval": "Preflight ready",
        "ready_for_readonly_diagnostic": "Ready for read-only diagnostic",
        "needs_information": "Needs info",
        "blocked": "Blocked",
        "superseded": "Superseded",
        "execution_not_enabled": "Execution not enabled yet",
    }
    return labels.get(status, status.replace("_", " "))
