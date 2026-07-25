# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
    DeploymentStrategyPolicyAssessment,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_contract import (
    SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
)


def render_deployment_strategy_policy(assessment: DeploymentStrategyPolicyAssessment) -> str:
    h = assessment.canary_health
    lines = [
        "# Railway Production Canary + Shadow Deployment Policy",
        "",
        f"- execution_id: `{assessment.execution_id}`",
        f"- deployment_strategy: **{assessment.deployment_strategy}**",
        f"- current_rollout_stage: **{assessment.current_rollout_stage}**",
        f"- traffic_mutation_boundary: **{assessment.traffic_mutation_boundary}**",
        f"- max_canary_percent: **{assessment.max_canary_percent}%**",
        f"- governed_canary_percent: **{assessment.governed_canary_percent}%** (simulated cap)",
        f"- autonomous_deployment_permitted: **{assessment.autonomous_deployment_permitted}**",
        f"- automatic_promotion_permitted: **{assessment.automatic_promotion_permitted}**",
        f"- synthetic_verification_recorded: **{assessment.synthetic_verification_recorded}**",
        f"- blast_radius_rollback_recommendation: **{assessment.blast_radius_rollback_recommendation}**",
        "",
        "## Shadow vs canary distinction",
        "- **Shadow:** 0% real production traffic; rehearsal + synthetic verification only.",
        "- **Canary:** governed percentage cap with synthetic verification; no real infra mutation.",
        "",
        "## Canary health (synthetic evidence)",
        f"- error_rate: **{h.error_rate:.2%}**",
        f"- synthetic_requests_recorded: **{h.synthetic_requests_recorded}**",
        f"- health_passed: **{h.health_passed}**",
        f"- promotion_pause_triggered: **{h.promotion_pause_triggered}**",
    ]
    if assessment.blockers:
        lines.extend(["", "## Policy blockers"])
        for b in assessment.blockers:
            lines.append(f"- `{b}`")
    if assessment.messages:
        lines.extend(["", "## Notes"])
        for m in assessment.messages:
            lines.append(f"- {m}")
    lines.extend(
        [
            "",
            "## Synthetic verification phrase",
            SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE,
        ]
    )
    return "\n".join(lines)


def render_shadow_traffic_policy(assessment: DeploymentStrategyPolicyAssessment) -> str:
    policy = assessment.shadow_traffic_policy
    lines = [
        "# Railway Production Shadow Traffic Policy",
        "",
        f"- mode: **{policy.get('mode', '')}**",
        f"- real_traffic_percent: **{policy.get('real_traffic_percent', '0')}%**",
        f"- synthetic_verification_required: **{policy.get('synthetic_verification_required', '')}**",
        f"- production_infra_mutation: **{policy.get('production_infra_mutation', 'blocked')}**",
        "",
        "Shadow traffic is **simulated mirror only** — no mutation against real production infrastructure.",
    ]
    return "\n".join(lines)


def render_canary_health_evidence(assessment: DeploymentStrategyPolicyAssessment) -> str:
    h = assessment.canary_health
    return "\n".join(
        [
            "# Railway Production Canary Health Evidence",
            "",
            f"- governed_canary_percent: **{assessment.governed_canary_percent}%**",
            f"- synthetic_requests_recorded: **{h.synthetic_requests_recorded}**",
            f"- simulated_error_rate: **{h.error_rate:.2%}**",
            f"- health_passed: **{h.health_passed}**",
            f"- promotion_pause_triggered: **{h.promotion_pause_triggered}**",
            f"- detail: {h.detail}",
        ]
    )


def render_rollout_percentage_governance(assessment: DeploymentStrategyPolicyAssessment) -> str:
    return "\n".join(
        [
            "# Railway Production Rollout Percentage Governance",
            "",
            f"- max_canary_percent (policy ceiling): **{assessment.max_canary_percent}%**",
            f"- governed_canary_percent (current stage): **{assessment.governed_canary_percent}%**",
            f"- automatic_promotion: **{assessment.automatic_promotion_permitted}**",
            "",
            "Percentage increases are **stage-gated** by FIX 121 and **policy-capped** by FIX 122.",
        ]
    )


def render_traffic_segmentation(record: dict[str, Any]) -> str:
    segments = record.get("traffic_segments") or []
    lines = ["# Railway Production Traffic Segmentation", ""]
    if not segments:
        lines.append("_No traffic segments configured._")
        return "\n".join(lines)
    for seg in segments:
        lines.extend(
            [
                f"## {seg.get('kind', '')}",
                f"- percent: **{seg.get('percent', 0)}%**",
                f"- real_infra_mutation: **{seg.get('real_infra_mutation', False)}**",
                f"- detail: {seg.get('detail', '')}",
                "",
            ]
        )
    return "\n".join(lines)


def render_canary_rollback_recommendation(assessment: DeploymentStrategyPolicyAssessment) -> str:
    return "\n".join(
        [
            "# Railway Production Canary Rollback Recommendation",
            "",
            f"- recommendation: **{assessment.blast_radius_rollback_recommendation}**",
            f"- blast_radius stage context: **{assessment.current_rollout_stage}**",
            f"- promotion_pause: **{assessment.canary_health.promotion_pause_triggered}**",
            "",
            "Recommendations are **advisory only** — FIX 120 escalation remains manual.",
        ]
    )
