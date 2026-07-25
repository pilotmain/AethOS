# SPDX-License-Identifier: Apache-2.0
"""FIX 125A — software delivery issue plan renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.issue_plan_contract import (
    BLOCKED_ACTIONS_FIX_125A,
    CODE_GENERATION_ENABLED_FIX_125A,
    PLANNING_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.issue_plan_service import get_lane_invariants


def render_issue_plan_summary(plan: dict[str, Any]) -> str:
    gp = plan.get("governed_plan") or {}
    invariants = get_lane_invariants()
    lines = [
        "# Software Delivery — Governed Issue Plan",
        "",
        f"- plan_id: `{plan.get('plan_id', '')}`",
        f"- lane: **{plan.get('lane_id', '')}** (≠ infrastructure orchestration)",
        f"- repository: **{plan.get('repository', '')}**",
        f"- issue: **#{plan.get('issue_number', '')}**",
        f"- status: **{plan.get('status', '')}**",
        f"- planning_approved: **{plan.get('planning_approved', False)}**",
        f"- code_generation_enabled: **{CODE_GENERATION_ENABLED_FIX_125A}**",
        f"- mutation_performed: **{plan.get('mutation_performed', False)}**",
        "",
        "## Goal",
        str(gp.get("goal") or ""),
        "",
        "## Problem",
        str(gp.get("problem_summary") or ""),
        "",
        "## Bounded steps (planning only)",
    ]
    for step in gp.get("bounded_steps") or []:
        lines.append(f"- {step}")
    lines.extend(["", "## Blocked actions (always)"])
    for action in BLOCKED_ACTIONS_FIX_125A:
        lines.append(f"- `{action}`")
    lines.extend(
        [
            "",
            "## Lane invariants",
            f"- infra_mutation_permitted: **{invariants['infra_mutation_permitted']}**",
            f"- lanes_must_not_merge: **{invariants['lanes_must_not_merge']}**",
            "",
            "No production mutation has been performed.",
        ]
    )
    return "\n".join(lines)


def render_implementation_scope(plan: dict[str, Any]) -> str:
    lines = [
        "# Software Delivery — Implementation Scope",
        "",
        f"- blast_radius: **{plan.get('blast_radius', '')}**",
        "",
        "## Affected files (estimated)",
    ]
    files = plan.get("affected_files") or []
    if not files:
        lines.append("_Scope will narrow after research (FIX 125C+)._")
    else:
        for fpath in files:
            lines.append(f"- `{fpath}`")
    lines.extend(
        [
            "",
            "## Test expectations",
        ]
    )
    for test in plan.get("test_expectations") or []:
        lines.append(f"- {test}")
    lines.append("\nHuman approval required before branch or code work.")
    return "\n".join(lines)


def render_risk_assessment(plan: dict[str, Any]) -> str:
    risk = plan.get("risk_assessment") or {}
    lines = [
        "# Software Delivery — Risk Assessment",
        "",
        f"- risk_tier: **{risk.get('risk_tier', 'unknown')}**",
        f"- task_kind: **{risk.get('kind', 'unknown')}**",
        "",
        "## Rollback notes",
    ]
    for note in plan.get("rollback_notes") or []:
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## Governance",
            "- Software delivery lane cannot trigger Railway deploy or production rollback.",
            "- Planning approval does not authorize code generation (FIX 125A).",
            "",
            f"Approve with: {PLANNING_APPROVAL_PHRASE}",
        ]
    )
    return "\n".join(lines)
