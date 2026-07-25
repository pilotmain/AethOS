# SPDX-License-Identifier: Apache-2.0
"""KERNEL_004 — track kernel feature gaps and closure status."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

GapSeverity = Literal["high", "medium", "low"]
GapStatus = Literal["open", "closed", "workaround"]


@dataclass(frozen=True)
class KernelGap:
    gap_id: str
    title: str
    severity: GapSeverity
    owner: str
    workaround: str
    status: GapStatus
    replacement: str = ""
    notes: str = ""


KERNEL_GAPS: tuple[KernelGap, ...] = (
    KernelGap(
        gap_id="railway_deployment_lifecycle_diagnostics",
        title="Specialized Railway deployment lifecycle debug/repair",
        severity="medium",
        owner="operational_session",
        workaround="Legacy router handles lifecycle debug/repair/index-clear phrases only.",
        status="workaround",
        replacement="operational_session.railway_readonly_executor.deployment_status (generic status only)",
        notes="Generic deployment status is kernel-owned; lifecycle trace/repair remains legacy.",
    ),
    KernelGap(
        gap_id="response_composition_rerender",
        title="Cached wide-health rerender follow-ups",
        severity="low",
        owner="operational_session",
        workaround="Session subject + kernel readonly health supersedes most rerender traffic.",
        status="workaround",
        replacement="operational_session session context last_operation",
        notes="try_compose_rerender_reply retained for planner transform until Wave 3.",
    ),
    KernelGap(
        gap_id="railway_credential_diagnostics_chat",
        title="Inline Railway credential validation chat",
        severity="low",
        owner="execution_brain",
        workaround="Legacy credential diagnostics router + provider_tool_contract validate.",
        status="workaround",
        replacement="execution_brain.provider_tool_contract railway.validate_token",
    ),
)


def list_kernel_gaps(*, severity: GapSeverity | None = None, status: GapStatus | None = None) -> list[KernelGap]:
    rows = list(KERNEL_GAPS)
    if severity is not None:
        rows = [row for row in rows if row.severity == severity]
    if status is not None:
        rows = [row for row in rows if row.status == status]
    return rows


def high_severity_open_gaps() -> list[KernelGap]:
    return [row for row in KERNEL_GAPS if row.severity == "high" and row.status == "open"]


def gap_registry_summary() -> dict[str, int | bool]:
    return {
        "total": len(KERNEL_GAPS),
        "high_open": len(high_severity_open_gaps()),
        "medium": sum(1 for row in KERNEL_GAPS if row.severity == "medium"),
        "low": sum(1 for row in KERNEL_GAPS if row.severity == "low"),
        "closed": sum(1 for row in KERNEL_GAPS if row.status == "closed"),
        "meets_no_high_open_requirement": len(high_severity_open_gaps()) == 0,
    }
