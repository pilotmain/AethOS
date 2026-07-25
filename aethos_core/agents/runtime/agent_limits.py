# SPDX-License-Identifier: Apache-2.0
"""Hard limits — bounded multi-agent execution."""

from __future__ import annotations

MAX_AGENTS_PER_TASK = 5
MAX_RECURSION_DEPTH = 2
MAX_BACKGROUND_RUNTIME_SEC = 120.0

BLOCKED_AGENT_ACTIONS = frozenset(
    {
        "self_spawn",
        "recursive_orchestration",
        "autonomous_mutation_chain",
        "autonomous_code_merge",
        "silent_background_agent",
        "credential_sharing",
        "unrestricted_shell",
        "direct_mutation_execution",
        "approval_bypass",
        "auto_merge",
        "force_push",
    }
)

ARTIFACT_TYPES = frozenset(
    {
        "agent_execution",
        "agent_evidence",
        "agent_failure",
        "agent_coordination",
        "agent_summary",
        "agent_operational_report",
        "agent_root_cause_analysis",
        "agent_runtime_correlation",
        "agent_confidence_summary",
        "agent_browser_evidence",
        "agent_provider_diagnostics",
        "engineering_architecture_graph",
        "engineering_dependency_risk",
        "engineering_git_hotspots",
        "engineering_ci_analysis",
        "engineering_pr_proposal",
        "engineering_preflight",
        "engineering_patch_plan",
        "engineering_execution",
        "engineering_pr_draft",
        # ── Arbiter artifact types (multi-model dispatch + consensus) ─────────
        "arbiter_session",      # Full arbiter session with consensus result
        "arbiter_critique",     # Individual critique round output
        "arbiter_consensus",    # Standalone consensus summary
    }
)
