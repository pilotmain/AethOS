# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management renderer."""

from __future__ import annotations

from typing import Any


def render_autonomous_application_lifecycle_management(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("lifecycle_management_dashboard") or [{}])[0]
    health = (sections.get("lifecycle_health_dashboard") or [{}])[0]
    risk = (sections.get("lifecycle_risk_dashboard") or [{}])[0]
    timeline = (sections.get("application_lifecycle_timeline") or [{}])[0]

    lines = [
        "# Autonomous Application Lifecycle Management",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 280')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Current stage: **{payload.get('current_lifecycle_stage', 'unknown')}**",
        f"- Overall health: **{health.get('overall_health_tier', '—')}** ({health.get('overall_health_score', '—')})",
        f"- Overall risk: **{risk.get('overall_risk_tier', '—')}**",
        f"- Open opportunities: **{dashboard.get('open_opportunity_count', 0)}**",
        f"- Human lifecycle approved: **{payload.get('human_lifecycle_decision_approve', False)}**",
        "",
        "## Lifecycle stages",
        "",
    ]

    for stage in sections.get("lifecycle_stage_registry") or []:
        lines.append(
            f"- **{stage.get('stage')}**: {stage.get('status')} "
            f"({stage.get('artifact_count', 0)} artifacts)"
        )

    lines.extend(["", "## Timeline highlights", ""])
    for event in (timeline.get("events") or [])[:8]:
        lines.append(f"- [{event.get('stage')}] {event.get('label')}")

    registry = (sections.get("lifecycle_opportunity_registry") or [{}])[0]
    lines.extend(["", "## Unified opportunities", ""])
    for opp in (registry.get("opportunities") or [])[:5]:
        lines.append(
            f"- **{opp.get('source_fix', '—')}** [{opp.get('lifecycle_stage', '—')}] {opp.get('title')}"
        )

    lines.extend(
        [
            "",
            "## Human lifecycle decision",
            "",
            "Record with:",
            "- `lifecycle decision approve: …`",
            "- `lifecycle decision hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Lifecycle management tracks state only. "
            "Execution, deployment, rollback, and repository mutation remain **false**.",
        ]
    )
    return "\n".join(lines)
