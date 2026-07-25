# SPDX-License-Identifier: Apache-2.0
"""FIX 290 — autonomous business operating system renderer."""

from __future__ import annotations

from typing import Any


def render_autonomous_business_operating_system(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("business_operating_dashboard") or [{}])[0]
    health = (sections.get("business_health_dashboard") or [{}])[0]
    risk = (sections.get("business_risk_dashboard") or [{}])[0]
    goals = (sections.get("business_goal_registry") or [{}])[0]
    alignment = (sections.get("strategic_alignment_graph") or [{}])[0]
    opportunities = (sections.get("business_opportunity_portfolio") or [{}])[0]

    lines = [
        "# Autonomous Business Operating System",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 290')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Overall health: **{health.get('overall_health_tier', '—')}** ({health.get('overall_health_score', '—')})",
        f"- Overall risk: **{risk.get('overall_risk_tier', '—')}**",
        f"- Business goals: **{goals.get('objective_count', 0)}**",
        f"- Open opportunities: **{dashboard.get('open_opportunity_count', 0)}**",
        f"- Lifecycle stage: **{dashboard.get('current_lifecycle_stage', '—')}**",
        f"- Human business approved: **{payload.get('human_business_decision_approve', False)}**",
        "",
        "## Business domains",
        "",
    ]

    for domain in sections.get("business_domain_registries") or []:
        lines.append(
            f"- **{domain.get('domain')}**: {domain.get('registry_id')} "
            f"({domain.get('operator_note_count', 0)} notes)"
        )

    lines.extend(["", "## Strategic alignment", ""])
    lines.append(
        f"- Graph nodes: **{alignment.get('node_count', 0)}**, edges: **{alignment.get('edge_count', 0)}**"
    )
    for edge in (alignment.get("edges") or [])[:5]:
        lines.append(f"- {edge.get('from')} → {edge.get('to')} ({edge.get('relation')})")

    lines.extend(["", "## Business goals", ""])
    for objective in (goals.get("objectives") or [])[:5]:
        lines.append(f"- **{objective.get('objective_id')}**: {objective.get('title')}")

    lines.extend(["", "## Business opportunities", ""])
    for opp in (opportunities.get("opportunities") or [])[:5]:
        source = opp.get("source_fix") or opp.get("source") or "—"
        lines.append(f"- **{source}** [{opp.get('business_domain', '—')}] {opp.get('title')}")

    lines.extend(
        [
            "",
            "## Human business decision",
            "",
            "Record with:",
            "- `business decision approve: …`",
            "- `business decision hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Business operating system understands the business only. "
            "Financial transactions, customer mutation, billing, and repository mutation remain **false**.",
        ]
    )
    return "\n".join(lines)
