# SPDX-License-Identifier: Apache-2.0
"""Phase-aware preflight execution status — read-only vs mutating."""

from __future__ import annotations

from aethos_core.operations.operation_models import OperationPreflight

OPERATIONAL_PHASE = "9.3B"

READONLY_EXECUTABLE_OPERATIONS = frozenset(
    {
        "why_down",
        "inspect_failed_deployment",
        "check_logs",
        "list_deployments",
        "list_domains",
        "project_details",
        "workflow_runs",
        "workflow_diagnostic",
        "workflow_jobs",
    }
)

APPROVABLE_PREFLIGHT_STATUSES = frozenset(
    {
        "ready_for_approval",
        "ready_for_readonly_diagnostic",
    }
)


def is_readonly_execution_available(preflight: OperationPreflight) -> bool:
    from aethos_core.operations.execution.execution_permissions import is_mutating_operation

    if is_mutating_operation(preflight.operation_type):
        return False
    if preflight.provider == "local":
        return False
    if preflight.provider == "vercel":
        if preflight.operation_type not in READONLY_EXECUTABLE_OPERATIONS:
            return False
    elif preflight.provider == "railway":
        if preflight.operation_type not in READONLY_EXECUTABLE_OPERATIONS:
            return False
    elif preflight.provider == "github":
        if preflight.operation_type not in READONLY_EXECUTABLE_OPERATIONS:
            return False
    elif preflight.operation_type not in READONLY_EXECUTABLE_OPERATIONS:
        return False
    if preflight.target_status != "resolved":
        return False
    if preflight.preflight_status not in APPROVABLE_PREFLIGHT_STATUSES:
        return False
    return True


def enrich_preflight_execution_metadata(preflight: OperationPreflight) -> None:
    readonly = is_readonly_execution_available(preflight)
    preflight.read_only_execution_enabled = readonly
    preflight.mutation_execution_enabled = False
    preflight.approval_required = preflight.required_approval
    preflight.phase = OPERATIONAL_PHASE
    preflight.execution_enabled = readonly


def execution_status_lines(preflight: OperationPreflight) -> list[str]:
    lines = [f"- **Phase:** {preflight.phase or OPERATIONAL_PHASE}"]
    if preflight.execution_approved:
        lines.append("- **Execution approved:** yes")
        if preflight.execution_job_id:
            lines.append(f"- **Execution job:** `{preflight.execution_job_id}`")
    if preflight.read_only_execution_enabled:
        if preflight.execution_approved:
            lines.append("- **Read-only execution:** approved")
        else:
            lines.append("- **Read-only execution:** available after approval")
    else:
        lines.append("- **Read-only execution:** not available")
    lines.append("- **Mutating execution:** disabled")
    lines.append(f"- **Approval required:** {'yes' if preflight.approval_required else 'no'}")
    return lines


def safety_footer(preflight: OperationPreflight) -> str:
    if preflight.read_only_execution_enabled:
        if preflight.execution_approved:
            return (
                "No mutation was executed during preflight. Read-only execution was approved — "
                "see the execution job for structured results."
            )
        return (
            "No mutation was executed during preflight. Read-only execution is available after "
            "approval in Mission Control."
        )
    if preflight.mutation_required:
        return "No mutation was executed. Mutating execution remains disabled in Phase 9.3B."
    return "No mutation was executed during preflight."
