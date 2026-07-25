# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_cross_repository_product_evolution_intelligence(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("product_evolution_dashboard") or [{}])[0]
    priority = list(sections.get("evolution_priority_matrix") or [])

    lines = [
        "# Cross-Repository Product Evolution Intelligence",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 261')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Opportunities identified: **{payload.get('opportunity_count', 0)}**",
        f"- Human evolution approved: **{payload.get('human_evolution_decision_approve', False)}**",
        f"- Feeds governed delivery: **{dashboard.get('feeds_governed_delivery_pipeline', False)}**",
        "",
        "## Top opportunities",
        "",
    ]

    for row in (dashboard.get("top_opportunities") or priority[:5]):
        lines.append(
            f"- **{row.get('priority_tier', '—')}** [{row.get('domain', '—')}] "
            f"{row.get('title', row.get('opportunity_id', '—'))} "
            f"(score {row.get('composite_score', '—')})"
        )

    lines.extend(["", "## Evolution domains", ""])
    for domain in payload.get("evolution_domains") or []:
        report_key = f"{domain}_evolution_report"
        report = (sections.get(report_key) or [{}])[0]
        lines.append(
            f"- **{domain.title()}**: {report.get('recommendation_count', 0)} recommendations"
        )

    lines.extend(["", "## Portfolio evolution backlog", ""])
    backlog = (sections.get("portfolio_evolution_backlog") or [{}])[0]
    for epic in (backlog.get("epics") or [])[:5]:
        lines.append(
            f"- **{epic.get('priority_tier', '—')}** {epic.get('title')} "
            f"({epic.get('repository', 'portfolio')})"
        )

    lines.extend(
        [
            "",
            "## Human evolution decision",
            "",
            "Record with:",
            "- `evolution decision approve: …`",
            "- `evolution decision hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Product evolution intelligence is advisory only. "
            "Execution authority, repository mutation, and automatic improvement remain **false**.",
        ]
    )
    return "\n".join(lines)
