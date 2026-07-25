# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline renderer."""

from __future__ import annotations

from typing import Any


def render_post_launch_operations_baseline(
    payload: dict[str, Any],
    *,
    focus: str = "post_launch_operations_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("post_launch_operations_dashboard") or [{}])[0]
    platform = (sections.get("platform_health_baseline") or [{}])[0]
    customer = (sections.get("customer_health_baseline") or [{}])[0]
    governance = (sections.get("governance_health_baseline") or [{}])[0]
    incident = (sections.get("incident_baseline") or [{}])[0]

    lines = [
        "# Post-Launch Operations Baseline",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 316')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Post-launch operations baseline ≠ operational authority. Observation only — no execution.",
        "",
        f"Platform health: **{platform.get('health_status', dashboard.get('platform_health_status', '—'))}**",
        f"Customer health: **{customer.get('health_status', dashboard.get('customer_health_status', '—'))}**",
        "",
    ]

    if focus in {"post_launch_operations_dashboard", "platform_health_baseline"}:
        lines.extend(
            [
                "## Platform health baseline",
                "",
                f"Deployment health: {platform.get('deployment_health', '—')}",
                f"Monitoring health: {platform.get('monitoring_health', '—')}",
                f"Operational stability: {platform.get('operational_stability', '—')}",
                "",
            ]
        )

    if focus in {"post_launch_operations_dashboard", "customer_health_baseline"}:
        lines.extend(
            [
                "## Customer health baseline",
                "",
                f"Adoption: healthy {customer.get('healthy_count', 0)}, at-risk {customer.get('at_risk_count', 0)}",
                f"Beta participants: {customer.get('beta_participants', 0)}",
                f"Health status: {customer.get('health_status', '—')}",
                "",
            ]
        )

    if focus in {"post_launch_operations_dashboard", "governance_health_baseline"}:
        lines.extend(
            [
                "## Governance health baseline",
                "",
                f"Authorization effective: {governance.get('authorization_effective', '—')}",
                f"Audit integrity: {governance.get('audit_integrity', '—')}",
                f"Review count: {governance.get('review_count', 0)}",
                "",
            ]
        )

    if focus in {"post_launch_operations_dashboard", "incident_baseline"}:
        lines.extend(
            [
                "## Incident baseline",
                "",
                f"Incident count: {incident.get('incident_count', 0)}",
                f"Escalation frequency: {incident.get('escalation_frequency', '—')}",
                f"Recovery trend: {incident.get('recovery_trend', '—')}",
                "",
            ]
        )

    if focus == "post_launch_operations_dashboard":
        trust = (sections.get("trust_baseline") or [{}])[0]
        commercial = (sections.get("commercial_baseline") or [{}])[0]
        lines.extend(
            [
                "## Unified operations baseline",
                "",
                f"Trust baselines: {trust.get('baseline_count', 0)}",
                f"Proven capabilities: {dashboard.get('proven_capability_count', 0)}",
                f"Commercial plans tracked: {commercial.get('plan_count', 0)}",
                f"Governance health: {governance.get('health_status', '—')}",
                "",
            ]
        )

    if focus == "operations_baseline_registry":
        registry = (sections.get("operations_baseline_registry") or [{}])[0]
        lines.extend(["## Baseline registry", ""])
        for row in (registry.get("records") or [])[:8]:
            lines.append(f"- [{row.get('kind')}] {row.get('content')}")
        lines.append("")

    lines.extend(
        [
            "",
            "No incident execution, customer outreach, deployment, or rollback actions. "
            "Use `operations baseline note:` and `operations baseline review approve:` for human review only.",
        ]
    )
    return "\n".join(lines)
