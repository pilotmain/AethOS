# SPDX-License-Identifier: Apache-2.0
"""FIX 144 — governance scenario definitions for sandbox simulation."""

from __future__ import annotations

from typing import Any

from aethos_core.software_delivery.software_delivery_phase_2_contract import SOFTWARE_DELIVERY_LOOP_ORDER

# Baseline gate weights for friction/latency estimation (heuristic).
_BASELINE_GATE_WEIGHTS: dict[str, float] = {
    "planning_approved": 1.0,
    "branch_create": 1.2,
    "patch_proposal_approved": 1.5,
    "workspace_apply": 2.0,
    "workspace_verification": 2.5,
    "github_preflight_approved": 2.0,
    "branch_push_completed": 2.5,
    "github_pr_opened": 3.0,
}


def scenario_catalog() -> list[dict[str, Any]]:
    return [
        {
            "scenario_id": "alternate_approval_chain",
            "title": "Alternate approval chain",
            "description": "Simulate workspace_verify before github_pr_preflight (verification-first sequencing).",
            "configuration": {
                "gate_order_override": [
                    "issue_intake",
                    "implementation_plan",
                    "implementation_branch",
                    "patch_proposal",
                    "workspace_apply",
                    "workspace_verify",
                    "pr_draft",
                    "github_pr_preflight",
                    "branch_push",
                    "pr_open",
                    "human_review",
                ],
            },
            "risk_bias": -0.05,
            "friction_bias": 0.08,
            "latency_bias_hours": 0.5,
        },
        {
            "scenario_id": "reduced_quorum",
            "title": "Reduced approval quorum",
            "description": "Hypothetical: skip view-only gates in friction model (fewer operator touches).",
            "configuration": {"quorum_multiplier": 0.75, "skipped_gates": ["branch_push_completed", "github_pr_opened"]},
            "risk_bias": 0.15,
            "friction_bias": -0.2,
            "latency_bias_hours": -1.5,
        },
        {
            "scenario_id": "increased_quorum",
            "title": "Increased approval quorum",
            "description": "Hypothetical: dual approval on branch_push and pr_open gates.",
            "configuration": {"quorum_multiplier": 1.5, "extra_approvals": ["branch_push_completed", "github_pr_opened"]},
            "risk_bias": -0.12,
            "friction_bias": 0.25,
            "latency_bias_hours": 2.0,
        },
        {
            "scenario_id": "strict_rollout_policy",
            "title": "Strict rollout policy",
            "description": "Simulate zero open incidents required before production rollout promotion thinking.",
            "configuration": {"require_zero_open_incidents": True, "rollout_caution_floor": "elevated_caution"},
            "risk_bias": -0.18,
            "friction_bias": 0.1,
            "latency_bias_hours": 1.0,
        },
        {
            "scenario_id": "stricter_verification",
            "title": "Stricter verification requirements",
            "description": "Double weight on workspace_verify + mandatory verification evidence node.",
            "configuration": {"verification_weight_multiplier": 2.0, "mandatory_verification": True},
            "risk_bias": -0.1,
            "friction_bias": 0.15,
            "latency_bias_hours": 1.25,
        },
        {
            "scenario_id": "alternate_gate_sequencing",
            "title": "Alternate gate sequencing",
            "description": "Simulate patch_proposal after workspace_apply (reversed patch/apply order).",
            "configuration": {
                "gate_order_override": [
                    "issue_intake",
                    "implementation_plan",
                    "implementation_branch",
                    "workspace_apply",
                    "patch_proposal",
                    "workspace_verify",
                    "pr_draft",
                    "github_pr_preflight",
                    "branch_push",
                    "pr_open",
                    "human_review",
                ],
            },
            "risk_bias": 0.08,
            "friction_bias": 0.05,
            "latency_bias_hours": 0.75,
        },
    ]


def baseline_configuration(*, signals: dict[str, Any]) -> dict[str, Any]:
    inbox = signals.get("approval_inbox") or {}
    pending = len(inbox.get("items") or [])
    return {
        "gate_order": list(SOFTWARE_DELIVERY_LOOP_ORDER),
        "quorum_multiplier": 1.0,
        "pending_approvals": pending,
        "verification_weight_multiplier": 1.0,
        "require_zero_open_incidents": False,
        "read_only": True,
        "source": "live_governance_state_observed_not_applied",
    }


def scenario_by_id(scenario_id: str) -> dict[str, Any] | None:
    for row in scenario_catalog():
        if row.get("scenario_id") == scenario_id:
            return row
    return None
