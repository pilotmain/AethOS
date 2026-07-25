# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship renderer."""

from __future__ import annotations

from typing import Any


def render_autonomous_product_stewardship(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("product_stewardship_dashboard") or [{}])[0]
    priority = list(sections.get("stewardship_priority_matrix") or [])

    lines = [
        "# Autonomous Product Stewardship",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 270')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Candidates observed: **{payload.get('candidate_count', 0)}**",
        f"- Human stewardship approved: **{payload.get('human_stewardship_decision_approve', False)}**",
        f"- Feeds governed delivery planning: **{dashboard.get('feeds_governed_delivery_planning', False)}**",
        "",
        "## Top opportunities",
        "",
    ]

    for row in dashboard.get("top_opportunities") or priority[:5]:
        lines.append(
            f"- **{row.get('priority_tier', '—')}** [{row.get('stewardship_domain', '—')}] "
            f"{row.get('title', row.get('candidate_id', '—'))} "
            f"(score {row.get('composite_score', '—')})"
        )

    lines.extend(["", "## Stewardship domains", ""])
    for domain in payload.get("stewardship_domains") or []:
        key = {
            "product_health": "product_health_report",
            "engineering": "engineering_stewardship_report",
            "operational": "operational_stewardship_report",
            "governance": "governance_stewardship_report",
            "portfolio": "portfolio_stewardship_report",
        }.get(domain, "")
        report = (sections.get(key) or [{}])[0]
        lines.append(
            f"- **{domain.replace('_', ' ').title()}**: {report.get('recommendation_count', 0)} recommendations"
        )

    lines.extend(["", "## Stewardship backlog", ""])
    backlog = (sections.get("stewardship_backlog") or [{}])[0]
    for epic in (backlog.get("epics") or [])[:5]:
        lines.append(
            f"- **{epic.get('priority_tier', '—')}** {epic.get('title')} "
            f"({epic.get('repository', 'portfolio')})"
        )

    memory = (sections.get("product_stewardship_memory") or [{}])[0]
    lines.extend(
        [
            "",
            "## Stewardship memory",
            "",
            f"- Observations: {memory.get('observation_count', 0)}",
            f"- Decision history: {memory.get('decision_history_count', 0)}",
            "",
            "## Human stewardship decision",
            "",
            "Record with:",
            "- `stewardship decision approve: …`",
            "- `stewardship decision hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Product stewardship observes and recommends only. "
            "Execution authority, repository mutation, and deployment remain **false**.",
        ]
    )
    return "\n".join(lines)
