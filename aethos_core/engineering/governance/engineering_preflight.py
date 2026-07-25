# SPDX-License-Identifier: Apache-2.0
"""Engineering preflight — scope, blast radius, patch plan, approval gate."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

from aethos_core.engineering.governance.engineering_patch_plan import build_patch_plan, format_patch_plan_report
from aethos_core.engineering.governance.engineering_scope import EngineeringRiskTier, tier_label
from aethos_core.engineering.patch_engine import generate_patch_proposal
from aethos_core.engineering.task_intake import intake_engineering_task
from aethos_core.local_workspace.mutations.foundation import BLOCKED_AUTONOMOUS_ACTIONS


def run_engineering_preflight(
    *,
    user_request: str,
    repo: Path,
    workspace_hint: str | None = None,
    persist: bool = False,
    session_id: str = "default",
    source: str = "api",
) -> dict[str, Any]:
    """Full engineering preflight — readonly until explicit approval."""
    task = intake_engineering_task(user_request, repo=repo)
    patch = generate_patch_proposal(repo, user_request=user_request, task=task)
    task_tier = str(task.get("risk_tier") or EngineeringRiskTier.E1_PROPOSAL.value)
    patch_tier = patch.get("risk_tier") or EngineeringRiskTier.E1_PROPOSAL.value
    tier_value = task_tier if task_tier in (
        EngineeringRiskTier.E2_BRANCH_DIFF.value,
        EngineeringRiskTier.E3_PR_CREATION.value,
    ) else patch_tier
    tier = EngineeringRiskTier(tier_value)
    preflight_id = f"epf-{uuid4().hex[:12]}"
    plan = patch.get("patch_plan") or build_patch_plan(
        task=task,
        affected_files=patch.get("files_affected") or [],
        blast_radius=patch.get("blast_radius"),
    )
    result = {
        "ok": True,
        "preflight_id": preflight_id,
        "status": "engineering_preflight",
        "approval_status": "pending",
        "execution_enabled": False,
        "mutation_execution_enabled": False,
        "risk_tier": tier.value,
        "risk_label": tier_label(tier),
        "task": task,
        "patch_proposal": patch,
        "patch_plan": plan,
        "required_lifecycle": [
            "engineering_preflight",
            "approval",
            "engineering_execution",
            "validation",
            "PR_proposal",
            "verification",
            "audit",
        ],
        "blocked_actions": sorted(BLOCKED_AUTONOMOUS_ACTIONS),
        "report": format_engineering_preflight_report(
            preflight_id=preflight_id,
            task=task,
            patch=patch,
            tier=tier.value,
        ),
    }
    if persist:
        from aethos_core.engineering.governance.engineering_preflight_store import record_engineering_preflight

        record_engineering_preflight(
            preflight=result,
            user_request=user_request,
            workspace_hint=workspace_hint,
            source=source,
            session_id=session_id,
        )
    return result


def run_and_record_engineering_preflight(
    *,
    user_request: str,
    repo: Path,
    workspace_hint: str | None = None,
    session_id: str = "default",
    source: str = "chat",
) -> dict[str, Any]:
    return run_engineering_preflight(
        user_request=user_request,
        repo=repo,
        workspace_hint=workspace_hint,
        persist=True,
        session_id=session_id,
        source=source,
    )


def format_engineering_preflight_report(
    *,
    preflight_id: str,
    task: dict[str, Any],
    patch: dict[str, Any],
    tier: str,
) -> str:
    plan_report = format_patch_plan_report(patch.get("patch_plan") or {})
    lines = [
        "# Engineering preflight (governed — approval required)",
        "",
        f"**Preflight ID:** `{preflight_id}`",
        f"**Risk tier:** {tier}",
        f"**Approval:** pending — no writes performed",
        "",
        f"**Problem:** {task.get('problem_summary') or '—'}",
        f"**Likely cause:** {task.get('likely_cause') or '—'}",
        "",
        plan_report,
        "",
        "**Next step:** Approve engineering execution in Mission Control → Engineering Execution.",
    ]
    return "\n".join(lines)
