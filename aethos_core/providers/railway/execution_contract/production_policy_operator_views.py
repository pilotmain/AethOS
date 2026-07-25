# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 122B — static production policy views when no execution is enrolled."""

from __future__ import annotations

from typing import Any, Literal

from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
    load_canary_shadow_policy_config,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    AUTOMATIC_PROMOTION_PERMITTED,
    AUTOMATIC_TRAFFIC_MUTATION_PERMITTED,
    AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
    CANARY_TRAFFIC_POLICY,
    SHADOW_TRAFFIC_POLICY,
)
from aethos_core.providers.railway.execution_contract.production_rollout_orchestration_contract import (
    AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
    ROLLOUT_STAGES,
)

UnenrolledPolicyView = Literal[
    "canary_shadow_policy",
    "shadow_traffic",
    "canary_health",
    "percentage_governance",
    "rollback_recommendation",
    "traffic_segmentation",
    "rollout_status",
    "rollout_timeline",
    "rollout_health_checkpoint",
]

ENROLLMENT_NEXT_STEP = "simulate production railway deployment"


def build_static_production_policy_context() -> dict[str, Any]:
    cfg = load_canary_shadow_policy_config()
    return {
        "enrollment": "missing",
        "execution_id": "",
        "live_mutation_boundary": "blocked",
        "traffic_mutation_boundary": "synthetic_only",
        "max_canary_percent": int(cfg["max_canary_percent"]),
        "promotion_pause_error_rate_threshold": float(cfg["promotion_pause_error_rate_threshold"]),
        "shadow_traffic_policy": dict(SHADOW_TRAFFIC_POLICY),
        "canary_traffic_policy": dict(CANARY_TRAFFIC_POLICY),
        "autonomous_deployment_permitted": AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED,
        "automatic_traffic_mutation_permitted": AUTOMATIC_TRAFFIC_MUTATION_PERMITTED,
        "automatic_promotion_permitted": AUTOMATIC_PROMOTION_PERMITTED,
        "autonomous_rollout_promotion_permitted": AUTONOMOUS_ROLLOUT_PROMOTION_PERMITTED,
        "rollout_stages": list(ROLLOUT_STAGES),
        "next_step": ENROLLMENT_NEXT_STEP,
    }


def _enrollment_block(ctx: dict[str, Any]) -> list[str]:
    return [
        "## Enrollment",
        "- production execution: **not enrolled**",
        "- execution_id: **none**",
        "",
    ]


def _policy_block(ctx: dict[str, Any]) -> list[str]:
    shadow = ctx["shadow_traffic_policy"]
    return [
        "## Policy",
        f"- shadow traffic: **synthetic only** (real traffic {shadow.get('real_traffic_percent', '0')}%)",
        f"- canary max percent: **{ctx['max_canary_percent']}%**",
        f"- auto promotion: **disabled**",
        f"- live traffic mutation: **blocked**",
        f"- autonomous deployment: **{ctx['autonomous_deployment_permitted']}**",
        "",
    ]


def _next_step_footer(ctx: dict[str, Any]) -> list[str]:
    return [
        "## Next step",
        f"`{ctx['next_step']}`",
        "",
        "No production mutation has been performed.",
    ]


def render_unenrolled_policy_view(view: UnenrolledPolicyView) -> str:
    ctx = build_static_production_policy_context()
    lines: list[str] = []

    if view == "canary_shadow_policy":
        lines = [
            "# Railway Production Canary/Shadow Policy",
            "",
            *_enrollment_block(ctx),
            *_policy_block(ctx),
            "## Shadow vs canary distinction",
            "- **Shadow:** 0% real production traffic; rehearsal + synthetic verification only.",
            "- **Canary:** governed percentage cap with synthetic verification; no real infra mutation.",
            "",
        ]
    elif view == "shadow_traffic":
        shadow = ctx["shadow_traffic_policy"]
        lines = [
            "# Railway Production Shadow Traffic Policy",
            "",
            *_enrollment_block(ctx),
            "## Policy",
            f"- mode: **{shadow.get('mode', '')}**",
            f"- real_traffic_percent: **{shadow.get('real_traffic_percent', '0')}%**",
            f"- production_infra_mutation: **{shadow.get('production_infra_mutation', 'blocked')}**",
            "",
        ]
    elif view == "canary_health":
        lines = [
            "# Railway Production Canary Health Evidence",
            "",
            *_enrollment_block(ctx),
            "## Policy (static)",
            "- health evidence requires enrolled execution + synthetic verification traffic",
            f"- promotion pause threshold: **{ctx['promotion_pause_error_rate_threshold']:.2%}** simulated error rate",
            "",
        ]
    elif view == "percentage_governance":
        lines = [
            "# Railway Production Rollout Percentage Governance",
            "",
            *_enrollment_block(ctx),
            "## Policy",
            f"- max_canary_percent (ceiling): **{ctx['max_canary_percent']}%**",
            f"- automatic_promotion: **{ctx['automatic_promotion_permitted']}**",
            "- stage caps apply after enrollment (shadow 0% → canary up to ceiling)",
            "",
        ]
    elif view == "rollback_recommendation":
        lines = [
            "# Railway Production Canary Rollback Recommendation",
            "",
            *_enrollment_block(ctx),
            "## Policy (static)",
            "- recommendation: **none** (no execution enrolled)",
            "- blast-radius advisories require verification + rollout context",
            "",
        ]
    elif view == "traffic_segmentation":
        lines = [
            "# Railway Production Traffic Segmentation",
            "",
            *_enrollment_block(ctx),
            "## Default segments (after enrollment)",
            "- `synthetic_verification` — 100% synthetic probes, no real infra mutation",
            "- `shadow_mirror_simulated` — 0% real production traffic",
            "",
        ]
    elif view == "rollout_status":
        lines = [
            "# Railway Production Rollout Orchestration",
            "",
            *_enrollment_block(ctx),
            "## Policy",
            f"- orchestration_state: **not_enrolled**",
            f"- current_stage: **{ROLLOUT_STAGES[0]}** (pending enrollment)",
            f"- live_mutation_boundary: **{ctx['live_mutation_boundary']}**",
            f"- autonomous_promotion_permitted: **{ctx['autonomous_rollout_promotion_permitted']}**",
            "",
            "## Rollout stages (governed sequence)",
        ]
        for stage in ROLLOUT_STAGES:
            lines.append(f"- `{stage}`: pending")
        lines.append("")
    elif view == "rollout_timeline":
        lines = [
            "# Railway Production Rollout Timeline",
            "",
            *_enrollment_block(ctx),
            "_No rollout receipts — execution not enrolled._",
            "",
        ]
    elif view == "rollout_health_checkpoint":
        lines = [
            "# Railway Production Rollout Health Checkpoints",
            "",
            *_enrollment_block(ctx),
            "## Expected checkpoints (after enrollment)",
            "- shadow_forward_complete",
            "- verification_evidence",
            "- operator_quorum",
            "",
        ]

    lines.extend(_next_step_footer(ctx))
    return "\n".join(lines)


def is_readonly_canary_shadow_policy_query(text: str) -> bool:
    raw = (text or "").lower()
    if "record" in raw and "synthetic" in raw and "verification" in raw:
        return False
    return True


def is_readonly_rollout_query(text: str) -> bool:
    raw = (text or "").lower()
    if "advance" in raw and "rollout" in raw:
        return False
    if "pause" in raw and "rollout" in raw:
        return False
    if "resume" in raw and "rollout" in raw:
        return False
    return True
