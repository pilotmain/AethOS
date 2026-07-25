# SPDX-License-Identifier: Apache-2.0
"""Goal planner — convert conversation intent into goals, sub-goals, and tool requirements."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Literal

from aethos_core.operational_session.operational_readonly_goal import ReadonlyGoal, classify_readonly_goal
from aethos_core.operational_session.operational_session import OperationalSession
from aethos_core.operational_session.session_subject import SessionSubject

GoalKind = Literal[
    "readonly_execute",
    "deploy_planning",
    "continue_plan",
    "clarify",
]

SubGoalKind = Literal[
    "workspace_discovery",
    "git_discovery",
    "target_discovery",
    "credential_validation",
    "env_validation",
    "deployment_plan",
    "deploy_execution",
    "verify_deployment",
    "fetch_logs",
    "list_inventory",
    "health_check",
    "deployment_status",
]

_CONTINUE_RX = re.compile(r"^\s*(continue|resume|keep going|next step)\s*[.!?]?\s*$", re.I)
_DEPLOY_PLAN_RX = re.compile(
    r"\b(deploy(?:e|ment)?|redeploy)\b.*\b(?:aethos|railway|vercel)\b"
    r"|\b(?:aethos|railway)\b.*\b(deploy(?:e|ment)?|redeploy)\b"
    r"|\bdeploy\s+aethos\b",
    re.I,
)
_PLANNING_ONLY_RX = re.compile(r"\b(plan|prepare|what(?:'s| is) needed|next action|steps to)\b", re.I)


@dataclass
class SubGoal:
    kind: SubGoalKind
    label: str
    tool_ids: list[str] = field(default_factory=list)
    readonly: bool = True


@dataclass
class OperationalGoalPlan:
    kind: GoalKind
    headline: str
    provider: str = ""
    target_hint: str = "aethos"
    user_text: str = ""
    sub_goals: list[SubGoal] = field(default_factory=list)
    readonly_goal: ReadonlyGoal | None = None
    requires_context: list[str] = field(default_factory=list)
    is_continue: bool = False


def plan_operational_goal(
    text: str,
    *,
    subject: SessionSubject,
    session: OperationalSession,
) -> OperationalGoalPlan | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if _CONTINUE_RX.match(raw):
        return OperationalGoalPlan(
            kind="continue_plan",
            headline="Continue active operational plan",
            provider=subject.provider,
            user_text=raw,
            is_continue=True,
        )

    readonly = classify_readonly_goal(raw, subject=subject, session=session)
    if readonly is not None:
        provider = subject.provider or _infer_provider_from_subject(subject)
        sub = _readonly_sub_goal(readonly, provider=provider)
        return OperationalGoalPlan(
            kind="readonly_execute",
            headline=f"Readonly: {readonly.operation.replace('_', ' ')}",
            provider=provider,
            user_text=raw,
            sub_goals=[sub],
            readonly_goal=readonly,
        )

    if _DEPLOY_PLAN_RX.search(raw) and not _is_pure_readonly(raw) and not _is_mutation_execute_only(raw):
        provider = _infer_deploy_provider(raw, subject)
        return _build_deploy_planning_goal(raw, provider=provider, subject=subject)

    return None


def _is_pure_readonly(text: str) -> bool:
    if re.search(r"\b(logs?|health|inventory|projects?|status)\b", text, re.I):
        if not re.search(r"\b(deploy(?:e|ment)?|redeploy)\b", text, re.I):
            return True
    return False


def _is_mutation_execute_only(text: str) -> bool:
    """Bare redeploy/restart commands belong to governance lanes — not deploy planning."""
    if not re.search(r"\b(redeploy|restart)\b", text, re.I):
        return False
    if re.search(r"\b(deploy\s+aethos|aethos\s+to\s+(?:railway|vercel))\b", text, re.I):
        return False
    if _PLANNING_ONLY_RX.search(text):
        return False
    return True


def _infer_deploy_provider(text: str, subject: SessionSubject) -> str:
    if re.search(r"\bvercel\b", text, re.I):
        return "vercel"
    if re.search(r"\brailway\b", text, re.I):
        return "railway"
    if subject.provider:
        return subject.provider
    return "railway"


def _infer_provider_from_subject(subject: SessionSubject) -> str:
    if subject.provider:
        return subject.provider
    # §5 — never infer Vercel from a garbage/quantifier "project" (e.g. "both").
    # Only a real project hint may select Vercel; otherwise default to Railway.
    from aethos_core.operational_target_resolution.provider_intent_guard import is_valid_vercel_project_hint

    if subject.vercel_project and is_valid_vercel_project_hint(subject.vercel_project):
        return "vercel"
    return "railway"


def _build_deploy_planning_goal(text: str, *, provider: str, subject: SessionSubject) -> OperationalGoalPlan:
    target = subject.service or subject.vercel_project or "aethos"
    prefix = provider
    sub_goals = [
        SubGoal(
            kind="workspace_discovery",
            label="Discover workspace portfolio",
            tool_ids=["local_workspace.discover"],
        ),
        SubGoal(
            kind="git_discovery",
            label="Resolve git remote",
            tool_ids=["git.resolve_remote"],
        ),
        SubGoal(
            kind="credential_validation",
            label=f"Validate {provider.title()} credential",
            tool_ids=[f"{prefix}.validate_token"],
        ),
        SubGoal(
            kind="target_discovery",
            label=f"Discover {provider.title()} target",
            tool_ids=[f"{prefix}.discover_projects", f"{prefix}.discover_services"],
        ),
        SubGoal(
            kind="env_validation",
            label="Validate environment readiness",
            tool_ids=[f"{prefix}.check_env_readiness"],
        ),
        SubGoal(
            kind="deployment_plan",
            label="Create governed deployment plan",
            tool_ids=[f"{prefix}.create_deploy_preflight"],
            readonly=False,
        ),
        SubGoal(
            kind="verify_deployment",
            label="Verify deployment after approval",
            tool_ids=[f"{prefix}.verify_deployment"],
        ),
    ]
    return OperationalGoalPlan(
        kind="deploy_planning",
        headline=f"Deploy {target} to {provider.title()}",
        provider=provider,
        target_hint=target,
        user_text=text,
        sub_goals=sub_goals,
        requires_context=["session_id", "workspace_root", "git_remote", "target"],
    )


def _readonly_sub_goal(readonly: ReadonlyGoal, *, provider: str = "railway") -> SubGoal:
    if provider == "vercel":
        mapping: dict[str, tuple[SubGoalKind, list[str]]] = {
            "fetch_logs": ("fetch_logs", ["vercel.fetch_logs"]),
            "list_inventory": ("list_inventory", ["vercel.discover_projects"]),
            "list_deployments": ("deployment_status", ["vercel.verify_deployment"]),
            "health_check": ("health_check", ["vercel.verify_deployment"]),
            "deployment_status": ("deployment_status", ["vercel.verify_deployment"]),
            "validate_connection": ("credential_validation", ["vercel.validate_token"]),
        }
    else:
        mapping = {
            "fetch_logs": ("fetch_logs", ["railway.fetch_logs"]),
            "list_inventory": ("list_inventory", ["railway.discover_projects"]),
            "list_services": ("list_inventory", ["railway.discover_projects"]),
            "health_check": ("health_check", ["railway.verify_deployment"]),
            "deployment_status": ("deployment_status", ["railway.verify_deployment"]),
            "validate_connection": ("credential_validation", ["railway.validate_token"]),
        }
    kind, tools = mapping.get(readonly.operation, ("fetch_logs", [f"{provider}.fetch_logs"]))
    return SubGoal(
        kind=kind,
        label=readonly.operation.replace("_", " "),
        tool_ids=tools,
    )
