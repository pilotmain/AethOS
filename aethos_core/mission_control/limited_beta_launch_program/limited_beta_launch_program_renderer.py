# SPDX-License-Identifier: Apache-2.0
"""FIX 312 — limited beta launch program renderer."""

from __future__ import annotations

from typing import Any


def render_limited_beta_launch_program(
    payload: dict[str, Any],
    *,
    focus: str = "beta_operations_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("beta_operations_dashboard") or [{}])[0]
    recommendation = (sections.get("beta_launch_recommendation") or [{}])[0]

    lines = [
        "# Limited Beta Launch Program",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 312')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Beta program management ≠ customer provisioning authority. Humans decide admissions.",
        "",
        f"Beta authority: **{payload.get('beta_authority', False)}**",
        f"Recommendation: **{recommendation.get('recommendation', payload.get('beta_launch_recommendation', '—'))}**",
        "",
    ]

    if focus in {"beta_operations_dashboard", "beta_cohort_registry"}:
        cohorts = (sections.get("beta_cohort_registry") or [{}])[0]
        lines.extend(["## Beta cohorts", ""])
        for cohort in cohorts.get("cohorts") or []:
            lines.append(
                f"- **{cohort.get('cohort_name')}** ({cohort.get('status')}): "
                f"{cohort.get('current_size', 0)}/{cohort.get('target_size', 0)}"
            )
        lines.append("")

    if focus == "beta_readiness_report":
        readiness = (sections.get("beta_readiness_report") or [{}])[0]
        lines.extend(["## Beta readiness", ""])
        for check in readiness.get("checks") or []:
            status = "ready" if check.get("ready") else "gap"
            lines.append(f"- {check.get('label')}: **{status}**")
        lines.append("")

    if focus == "beta_feedback_registry":
        feedback = (sections.get("beta_feedback_registry") or [{}])[0]
        lines.extend(["## Beta feedback", ""])
        for row in (feedback.get("feedback_items") or [])[:6]:
            lines.append(f"- [{row.get('category')}] {row.get('content')}")
        lines.append("")

    if focus == "beta_success_metrics":
        metrics = (sections.get("beta_success_metrics") or [{}])[0]
        lines.extend(
            [
                "## Success metrics",
                "",
                f"Activation rate: **{metrics.get('activation_rate', 0)}%**",
                f"Onboarding completion: **{metrics.get('onboarding_completion', 0)}%**",
                f"Provider connection completion: **{metrics.get('provider_connection_completion', 0)}%**",
                f"Customer health score: **{metrics.get('customer_health_score', 0)}**",
                "",
            ]
        )

    if focus == "beta_operations_dashboard":
        risks = (sections.get("beta_risk_registry") or [{}])[0]
        lines.extend(
            [
                "## Operations summary",
                "",
                f"Active cohorts: **{dashboard.get('active_cohort_count', 0)}**",
                f"Active participants: **{dashboard.get('active_participant_count', 0)}**",
                f"Open risks: **{dashboard.get('open_risk_count', 0)}**",
                "",
                "## Top risks",
                "",
            ]
        )
        for row in (risks.get("risks") or [])[:5]:
            lines.append(f"- [{row.get('level')}] {row.get('detail')}")
        lines.extend(
            [
                "",
                recommendation.get("rationale", "Recommendation derived from evidence only."),
            ]
        )

    lines.extend(
        [
            "",
            "No user provisioning, plan assignment, or automatic beta expansion. "
            "Use `beta candidate note:` and `beta admission review approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
