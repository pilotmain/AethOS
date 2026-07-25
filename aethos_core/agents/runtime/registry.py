# SPDX-License-Identifier: Apache-2.0
"""On-demand agent spec factory — no static specialist roster.

AethOS is the single standing orchestrator. There are **no predefined specialist
agents**. The orchestrator spawns task-scoped agents on demand, attaches the
relevant skills to each, and narrows a single default permission profile down to
the *capability* required for that spawn. Specs are therefore built per-spawn
from the task + chosen skills — never read from a fixed dictionary of named
roles.

`_CAPABILITY_PROFILES` is **not** a roster of standing agents: it is a narrowing
table the factory uses to bound a freshly-spawned task agent to exactly the
read-only / preflight capability it needs. Every spawn gets a fresh AgentSpec.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    label: str
    purpose: str
    allowed: tuple[str, ...]
    blocked: tuple[str, ...]
    max_runtime_sec: float = 30.0
    capability: str = ""
    skills: tuple[str, ...] = ()
    spawn_id: str = ""


# Global hard blocks — apply to every spawned agent regardless of capability.
BLOCKED_GLOBAL = frozenset(
    {
        "merge",
        "push",
        "rebase",
        "unrestricted_shell",
        "direct_mutation_execution",
        "auto_merge",
        "force_push",
        "self_spawn",
    }
)


# Single default permission profile. The orchestrator NARROWS this per spawn.
# It is intentionally read-only / preflight-only — nothing here may mutate.
DEFAULT_PERMISSION_PROFILE: dict[str, Any] = {
    "label": "Task-scoped agent",
    "purpose": "On-demand task agent (default read-only profile)",
    "allowed": (
        "read",
        "analyze",
        "summarize",
        "preflight",
        "evidence_capture",
        "code_reasoning_readonly",
    ),
    "blocked": ("filesystem_mutation", "credential_submission"),
}


# Capability narrowing table. Each entry bounds a freshly-spawned task agent to a
# read-only / preflight capability. These are capabilities the orchestrator
# *composes on demand* — not a standing list of agents.
_CAPABILITY_PROFILES: dict[str, dict[str, Any]] = {
    "code_intelligence": {
        "label": "Code reasoning",
        "purpose": "Local workspace + code intelligence (read-only)",
        "allowed": (
            "architecture_analysis",
            "git_analysis",
            "dependency_audit",
            "ci_analysis",
            "pr_proposal_generation",
            "patch_planning",
            "engineering_preflight",
            "code_reasoning_readonly",
        ),
        "blocked": ("merge", "push", "rebase", "filesystem_mutation", "unrestricted_shell"),
    },
    "web_evidence": {
        "label": "Web evidence",
        "purpose": "Governed web/browser evidence collection",
        "allowed": ("screenshot", "metadata", "dom_snapshot", "console_network_evidence"),
        "blocked": ("hidden_interaction", "autonomous_clicks", "credential_submission", "mutation"),
    },
    "provider_ops": {
        "label": "Provider diagnostics",
        "purpose": "Railway / GitHub / Vercel operational intelligence (read-only)",
        "allowed": ("inventory", "deployment_diagnostics", "workflow_analysis", "mutation_preflight_generation"),
        "blocked": ("direct_mutation_bypass", "autonomous_redeploy", "approval_skipping"),
    },
    "research": {
        "label": "Research",
        "purpose": "Evidence-first research and documentation discovery",
        "allowed": ("citations", "summarization", "source_aggregation", "documentation_discovery"),
        "blocked": ("hallucinated_facts", "uncited_claims", "hidden_browsing"),
    },
    "operations_analyst": {
        "label": "Ops correlation",
        "purpose": "Operational summarization + incident correlation",
        "allowed": ("summarize_failures", "correlate_evidence", "operational_timeline", "severity_classification"),
        "blocked": ("operational_execution", "mutation_approval", "direct_mutation"),
    },
    "dev_workspace": {
        "label": "Development workspace",
        "purpose": "Workspace diagnostics, CI analysis, governed dev preflights (advisory)",
        "allowed": (
            "workspace_diagnostics",
            "engineering_preflight",
            "architecture_analysis",
            "dependency_audit",
            "ci_analysis",
        ),
        "blocked": ("autonomous_mutation", "unrestricted_shell", "auto_merge", "direct_mutation_execution"),
    },
    "qa_verification": {
        "label": "QA verification",
        "purpose": "Test planning, verification gates, and quality evidence (read-only)",
        "allowed": (
            "test_planning",
            "evidence_capture",
            "summarize_failures",
            "correlate_evidence",
            "severity_classification",
            "ci_analysis",
        ),
        "blocked": ("operational_execution", "mutation_approval", "direct_mutation"),
    },
    "arbiter_panel": {
        "label": "Multi-model arbiter",
        "purpose": "Parallel multi-model dispatch with critique-based consensus (read-only analysis)",
        "allowed": (
            "parallel_model_dispatch",
            "blind_critique_evaluation",
            "consensus_scoring",
            "arbiter_artifact_generation",
            "response_comparison",
        ),
        "blocked": (
            "mutation",
            "direct_mutation_execution",
            "approval_bypass",
            "credential_submission",
            "autonomous_mutation_chain",
        ),
    },
}


def available_capabilities() -> list[str]:
    """Capabilities the orchestrator may compose into on-demand task agents."""
    return list(_CAPABILITY_PROFILES.keys())


def build_agent_spec(
    capability: str,
    *,
    task: str = "",
    skills: tuple[str, ...] | list[str] | None = None,
    max_runtime_sec: float = 30.0,
    task_scoped: bool = False,
) -> AgentSpec:
    """Build a bounded AgentSpec on demand for one spawn.

    The default permission profile is narrowed to ``capability``; the chosen
    ``skills`` are recorded on the spec so the orchestrator can attach them to
    the spawned task agent. When ``task_scoped`` is True the spec carries a
    unique spawn id (used for live Mission Control display).
    """
    profile = _CAPABILITY_PROFILES.get(capability, DEFAULT_PERMISSION_PROFILE)
    spawn_id = f"agent-{uuid4().hex[:10]}" if task_scoped else ""
    # agent_id stays the capability token so the runtime can route to the right
    # substrate; the spawn is still task-scoped (fresh spec + context per task).
    return AgentSpec(
        agent_id=capability,
        label=str(profile.get("label") or capability.replace("_", " ").title()),
        purpose=str(profile.get("purpose") or "On-demand task agent"),
        allowed=tuple(profile.get("allowed") or DEFAULT_PERMISSION_PROFILE["allowed"]),
        blocked=tuple(profile.get("blocked") or ()),
        max_runtime_sec=max_runtime_sec,
        capability=capability,
        skills=tuple(skills or ()),
        spawn_id=spawn_id,
    )


def get_agent(capability: str) -> AgentSpec | None:
    """Return a freshly-built spec for a known capability, else None."""
    if capability not in _CAPABILITY_PROFILES:
        return None
    return build_agent_spec(capability)


def list_agents() -> list[dict[str, Any]]:
    """No standing roster — agents exist only when spawned on demand."""
    return []


def validate_agent_action(capability: str, action: str) -> dict[str, Any]:
    spec = get_agent(capability)
    if not spec:
        return {"allowed": False, "reason": "unknown_capability"}
    if action in spec.blocked or action in BLOCKED_GLOBAL:
        return {"allowed": False, "reason": "blocked_action", "agent_id": capability, "action": action}
    return {"allowed": True, "agent_id": capability, "action": action}
