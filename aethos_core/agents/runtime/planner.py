# SPDX-License-Identifier: Apache-2.0
"""Task planner — decompose intent into bounded agent assignments."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.agent_limits import MAX_AGENTS_PER_TASK
from aethos_core.agents.runtime.registry import AgentSpec, available_capabilities, build_agent_spec
from aethos_core.agents.runtime.role_planning import extract_requested_roles


@dataclass
class AgentAssignment:
    agent_id: str
    task: str
    action: str
    priority: int = 0
    spec: AgentSpec | None = None


@dataclass
class TaskPlan:
    plan_id: str
    goal: str
    assignments: list[AgentAssignment] = field(default_factory=list)
    recursion_depth: int = 0
    execution_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "assignments": [
                {"agent_id": a.agent_id, "task": a.task, "action": a.action, "priority": a.priority}
                for a in self.assignments
            ],
            "recursion_depth": self.recursion_depth,
            "execution_enabled": self.execution_enabled,
            "agent_count": len(self.assignments),
        }


_DEPLOYMENT_FAIL_RX = re.compile(
    r"\banaly(?:z|s)e\s+why\b.*\b(?:railway|vercel|deployment)\b|"
    r"\b(?:railway|vercel)\b.*\b(?:deployment|deploy)\b.*\bfail",
    re.I,
)
_ARCH_RISK_RX = re.compile(r"\barchitecture\s+risks?\b|\banaly(?:z|s)e\s+architecture\s+risks?", re.I)
_PR_MODERN_RX = re.compile(r"\bpr\s+proposal\b.*\bdependenc|\bprepare\s+a\s+pr\s+proposal\b", re.I)
_ENGINEERING_FIX_RX = re.compile(
    r"\bfix\b.*\b(?:github\s+)?workflow\b|\bgoverned\s+patch\b|"
    r"\bprepare\s+and\s+validate\b.*\bmoderni|\bcreate\s+a\s+governed\s+patch\b",
    re.I,
)
_DEVELOPER_RX = re.compile(
    r"\bdeveloper\s+agent\b|\bworkspace\s+diagnostics\b|\bcursor\b.*\b(?:agent|autonom)",
    re.I,
)
_MULTI_AGENT_RX = re.compile(
    r"\bcorrelat|\boperational\s+report\b|\bmulti.?agent\b|\bdelegat|\bincident\s+timeline\b",
    re.I,
)
# Explicit "command center / orchestrate a team of agents" intent. This is a
# *fresh* multi-agent orchestration ask — it must reach the agent-runtime
# orchestration lane (spawn + coordinate), never the single-service world-model
# follow-up router. Kept deliberately narrow so genuine world-model recall
# follow-ups ("why is nexora-search still failing?") are unaffected.
_COMMAND_CENTER_RX = re.compile(
    r"\bcommand\s*cent(?:er|re)\b|"
    r"\borchestrate\b[^.\n]{0,40}\bagents?\b|"
    r"\borchestrate\s+a\s+team\b|"
    r"\b(?:spin\s*up|spawn|stand\s*up|assemble|coordinate|deploy)\b[^.\n]{0,40}\bagents?\b|"
    r"\b(?:spin\s*up|assemble|stand\s*up|put\s+together|coordinate|orchestrate)\s+a\s+team\b|"
    r"\bteam\s+of\s+(?:agents|specialists|experts|roles)\b|"
    r"\bagent\s+(?:team|swarm|fleet)\b|"
    r"\bwhich\s+agent\s+is\s+doing\s+what\b|"
    r"\bassemble\b[^.\n]{0,40}\bplan\b",
    re.I,
)

# Explicit "multi-model arbiter / compare models / consensus" intent. Gated by
# ARBITER_ENABLED via is_arbiter_request(); the plan branch below also matches
# the regex so a planning preview reflects the arbiter lane when phrased this way.
_ARBITER_RX = re.compile(
    r"\barbiter\b|"
    r"\bcompare\s+models?\b|"
    r"\bmulti.?model\s+(?:compare|consensus|critique|review)\b|"
    r"\brun\s+(?:this\s+)?(?:through\s+)?multiple\s+models?\b|"
    r"\bget\s+(?:a\s+)?(?:second|third|multiple)\s+(?:model\s+)?opini(?:on|ons)\b|"
    r"\bcritique\s+(?:each\s+other|each\s+other.s\s+work|across\s+models)\b|"
    r"\bconsensus\s+(?:from|across)\s+(?:multiple\s+)?models?\b|"
    r"\bwhich\s+model\s+(?:is|was)\s+(?:best|right|correct|most\s+accurate)\b",
    re.I,
)


def is_arbiter_request(text: str) -> bool:
    """True when the user explicitly wants multi-model arbiter comparison.

    Returns False when ARBITER_ENABLED is off so the feature stays fully opt-in.
    """
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "arbiter_enabled", False):
        return False
    return bool(_ARBITER_RX.search(text or ""))


def is_command_center_orchestration_request(text: str, *, session_id: str = "default") -> bool:
    """True for explicit multi-agent command-center / orchestration asks.

    This is the single source of truth used to (a) route the turn to the agent
    runtime orchestration lane and (b) make the world-model follow-up router
    decline the turn, so an orchestration request is never treated as a
    single-service investigation recall.
    """
    raw = (text or "").strip()
    if not raw:
        return False
    return bool(_COMMAND_CENTER_RX.search(raw))


def is_multi_agent_request(text: str, *, session_id: str = "default") -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if (
        _DEPLOYMENT_FAIL_RX.search(raw)
        or _ARCH_RISK_RX.search(raw)
        or _PR_MODERN_RX.search(raw)
        or _ENGINEERING_FIX_RX.search(raw)
        or _DEVELOPER_RX.search(raw)
        or _MULTI_AGENT_RX.search(raw)
        or _COMMAND_CENTER_RX.search(raw)
    ):
        return True
    from aethos_core.chat.operational_master_router import master_router_has_priority_route

    if master_router_has_priority_route(raw, session_id=session_id):
        return False
    # Operational why_down preflights take precedence over multi-agent coordination
    try:
        from aethos_core.operations.intents import infer_operation_preflight_intent

        inferred = infer_operation_preflight_intent(raw, session_id=session_id)
        if inferred is not None:
            _title, _job_type, params = inferred
            if params.get("operation_type") == "why_down" and not _MULTI_AGENT_RX.search(raw):
                if not _DEPLOYMENT_FAIL_RX.search(raw) and not _ARCH_RISK_RX.search(raw) and not _PR_MODERN_RX.search(raw):
                    return False
    except Exception:
        pass
    return bool(
        _DEPLOYMENT_FAIL_RX.search(raw)
        or _ARCH_RISK_RX.search(raw)
        or _PR_MODERN_RX.search(raw)
        or _MULTI_AGENT_RX.search(raw)
    )


# Explicitly-requested roles → their (capability, action, task-label) for orchestration.
# Each action is in its capability's allowed profile (registry _CAPABILITY_PROFILES), so the
# agent runs rather than failing the policy gate. Agents are read-only: they produce each
# role's slice of a coordinated PLAN (design / implementation approach / test strategy /
# deploy plan), not built code — governance blocks mutations.
_ROLE_ORCHESTRATION: dict[str, tuple[str, str, str]] = {
    "Architect": ("code_intelligence", "architecture_analysis", "architecture & design plan"),
    "Development": ("dev_workspace", "workspace_diagnostics", "implementation plan"),
    "QA": ("qa_verification", "test_planning", "test strategy"),
    "DevOps": ("operations_analyst", "operational_timeline", "deployment & ops plan"),
    "Security": ("code_intelligence", "dependency_audit", "security review"),
    "Research": ("research", "source_aggregation", "research findings"),
    "Writer": ("research", "summarization", "written summary"),
    "Marketing": ("research", "summarization", "marketing plan"),
    "Analyst": ("operations_analyst", "correlate_evidence", "analysis"),
    "Operations": ("operations_analyst", "operational_timeline", "operations review"),
}


def plan_task(goal: str, *, depth: int = 0) -> TaskPlan:
    raw = (goal or "").strip()
    plan_id = f"plan-{uuid4().hex[:12]}"
    assignments: list[AgentAssignment] = []

    requested_roles = extract_requested_roles(raw)
    if len(requested_roles) >= 2:
        # The user named a team (architect/developer/tester/devops/…): build that team
        # instead of the generic operational template, so the run reflects the specialists
        # asked for, each producing their slice of a governed (read-only) plan.
        for i, role in enumerate(requested_roles, start=1):
            cap, _action, label = _ROLE_ORCHESTRATION.get(
                role, ("operations_analyst", "correlate_evidence", "analysis")
            )
            # Generative planning: each role agent produces its slice of the plan via the LLM
            # (delegation._run_planning), not a diagnostic scan of a (nonexistent) system.
            assignments.append(AgentAssignment(cap, f"{role.lower()}: {label}", "team_planning", i))
    elif _DEPLOYMENT_FAIL_RX.search(raw):
        assignments = [
            AgentAssignment("provider_ops", "deployment_diagnostics", "deployment_diagnostics", 1),
            AgentAssignment("web_evidence", "deployment_evidence", "deployment_capture", 2),
            AgentAssignment("code_intelligence", "recent_changes", "git_correlation", 3),
            AgentAssignment("operations_analyst", "correlate_failure", "correlate_evidence", 4),
        ]
    elif _ARCH_RISK_RX.search(raw):
        assignments = [
            AgentAssignment("code_intelligence", "architecture_scan", "architecture_analysis", 1),
            AgentAssignment("code_intelligence", "dependency_audit", "dependency_audit", 2),
            AgentAssignment("operations_analyst", "operational_impact", "severity_classification", 3),
        ]
    elif _PR_MODERN_RX.search(raw):
        assignments = [
            AgentAssignment("code_intelligence", "dependency_audit", "dependency_audit", 1),
            AgentAssignment("code_intelligence", "pr_proposal", "pr_proposal_generation", 2),
            AgentAssignment("operations_analyst", "risk_summary", "summarize_failures", 3),
        ]
    elif _ENGINEERING_FIX_RX.search(raw):
        assignments = [
            AgentAssignment("provider_ops", "workflow_analysis", "workflow_analysis", 1),
            AgentAssignment("dev_workspace", "workspace_diagnostics", "workspace_diagnostics", 2),
            AgentAssignment("code_intelligence", "engineering_preflight", "engineering_preflight", 3),
            AgentAssignment("operations_analyst", "rollout_risk", "correlate_evidence", 4),
        ]
    elif _DEVELOPER_RX.search(raw):
        assignments = [
            AgentAssignment("dev_workspace", "workspace_diagnostics", "workspace_diagnostics", 1),
            AgentAssignment("code_intelligence", "architecture_scan", "architecture_analysis", 2),
            AgentAssignment("operations_analyst", "dev_summary", "summarize_failures", 3),
        ]
    elif _COMMAND_CENTER_RX.search(raw):
        assignments = [
            AgentAssignment("code_intelligence", "workspace_analysis", "architecture_analysis", 1),
            AgentAssignment("provider_ops", "provider_diagnostics", "inventory", 2),
            AgentAssignment("operations_analyst", "consolidated_plan", "operational_timeline", 3),
        ]
    elif is_arbiter_request(raw):
        assignments = [
            AgentAssignment("arbiter_panel", "multi_model_dispatch", "parallel_model_dispatch", 1),
            AgentAssignment("operations_analyst", "arbiter_summary", "summarize_failures", 2),
        ]
    elif _MULTI_AGENT_RX.search(raw):
        assignments = [
            AgentAssignment("code_intelligence", "workspace_analysis", "architecture_analysis", 1),
            AgentAssignment("provider_ops", "provider_diagnostics", "inventory", 2),
            AgentAssignment("operations_analyst", "unified_report", "operational_timeline", 3),
        ]
    else:
        assignments = [
            AgentAssignment("operations_analyst", "assess_goal", "summarize_failures", 1),
        ]

    # Cap and dedupe by capability keeping highest priority task. Each surviving
    # assignment requests a bounded spec from the on-demand factory — there is no
    # static roster to look up.
    # For an explicitly named team, each requested role is its own agent even when two roles
    # share an underlying capability (e.g. marketing/writer/research → research) — so dedupe
    # by the role task, not the capability, and allow a larger team. Other plans dedupe by
    # capability and stay at the default cap.
    named_team = len(requested_roles) >= 2
    max_agents = 8 if named_team else MAX_AGENTS_PER_TASK
    known = set(available_capabilities())
    seen: set[str] = set()
    capped: list[AgentAssignment] = []
    for a in sorted(assignments, key=lambda x: x.priority):
        key = a.task if named_team else a.agent_id
        if key in seen:
            continue
        if a.agent_id not in known:
            continue
        seen.add(key)
        a.spec = build_agent_spec(a.agent_id, task=a.task, task_scoped=True)
        capped.append(a)
        if len(capped) >= max_agents:
            break

    return TaskPlan(
        plan_id=plan_id,
        goal=raw,
        assignments=capped,
        recursion_depth=depth,
        execution_enabled=False,
    )
