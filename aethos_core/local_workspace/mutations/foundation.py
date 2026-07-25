# SPDX-License-Identifier: Apache-2.0
"""Governed code mutation foundation — preflight-only, no autonomous writes."""

from __future__ import annotations

from typing import Any

GOVERNED_CODE_MUTATION_OPS = frozenset(
    {
        "code_mutation_preflight",
        "code_mutation_execution",
        "pr_generation",
        "verification_execution",
        "create_branch",
        "generate_patch",
        "create_pr",
    }
)

BLOCKED_AUTONOMOUS_ACTIONS = frozenset(
    {
        "unrestricted_shell",
        "filesystem_wide_access",
        "auto_merge_main",
        "force_push",
        "delete_repo",
        "delete_env_var",
        "silent_background_coding",
        "hidden_browser_automation",
        "autonomous_production_write",
    }
)


def build_pr_proposal_stub(*, provider: str, target: str, user_request: str) -> dict[str, Any]:
    """Readonly PR proposal scaffold — execution requires governed mutation approval."""
    return {
        "ok": True,
        "status": "proposal_only",
        "provider": provider,
        "target": target,
        "user_request": user_request[:500],
        "root_cause_analysis": "Pending governed analysis — connect workspace scan + workflow evidence.",
        "proposed_changes": [],
        "patch_preview": None,
        "verification_plan": [
            "Run readonly test analysis",
            "Run mutation preflight",
            "Human approval required",
            "Governed execution + verification job",
        ],
        "rollback_plan": "Revert branch / discard patch — no auto-merge.",
        "blocked_actions": sorted(BLOCKED_AUTONOMOUS_ACTIONS),
        "required_lifecycle": [
            "code_mutation_preflight",
            "approval",
            "code_mutation_execution",
            "verification_execution",
            "audit",
        ],
    }
