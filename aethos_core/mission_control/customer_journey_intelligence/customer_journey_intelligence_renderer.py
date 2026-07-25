# SPDX-License-Identifier: Apache-2.0
"""FIX 321 — customer journey intelligence renderer."""

from __future__ import annotations

from typing import Any


def render_customer_journey_intelligence(
    payload: dict[str, Any],
    *,
    focus: str = "customer_journey_dashboard",
) -> str:
    sections = payload.get("sections") or {}

    if focus == "customer_journey_registry":
        registry = (sections.get("customer_journey_registry") or [{}])[0]
        lines = [
            "## Customer journey registry",
            "",
            f"- Current stage: **{registry.get('current_stage', '—')}**",
            "",
        ]
        for entry in registry.get("entries") or []:
            lines.append(
                f"- **{entry.get('stage')}**: {entry.get('progression_state')} "
                f"(confidence {entry.get('confidence')})"
            )
        return "\n".join(lines)

    if focus == "journey_funnel_report":
        report = (sections.get("journey_funnel_report") or [{}])[0]
        lines = ["## Journey funnel", ""]
        for row in report.get("transitions") or []:
            lines.append(
                f"- **{row.get('from_stage')} → {row.get('to_stage')}**: "
                f"{row.get('conversion_rate_percent')}%"
            )
        return "\n".join(lines)

    if focus == "journey_dropoff_report":
        report = (sections.get("journey_dropoff_report") or [{}])[0]
        lines = ["## Journey drop-off", "", "### Abandonment points", ""]
        for item in report.get("abandonment_points") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Stalled journeys", ""])
        for item in report.get("stalled_journeys") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Friction hotspots", ""])
        for item in report.get("friction_hotspots") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "journey_success_report":
        report = (sections.get("journey_success_report") or [{}])[0]
        lines = ["## Journey success", "", "### Successful paths", ""]
        for item in report.get("successful_paths") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### High-retention paths", ""])
        for item in report.get("high_retention_paths") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Expansion paths", ""])
        for item in report.get("expansion_paths") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "journey_friction_report":
        report = (sections.get("journey_friction_report") or [{}])[0]
        lines = ["## Journey friction", "", "### Onboarding friction", ""]
        for item in report.get("onboarding_friction") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Provider connection friction", ""])
        for item in report.get("provider_connection_friction") or []:
            lines.append(f"- {item}")
        lines.extend(["", "### Capability discovery friction", ""])
        for item in report.get("capability_discovery_friction") or []:
            lines.append(f"- {item}")
        return "\n".join(lines)

    if focus == "journey_cohort_report":
        report = (sections.get("journey_cohort_report") or [{}])[0]
        lines = ["## Journey cohorts", ""]
        for cohort in report.get("cohorts") or []:
            lines.append(
                f"- **{cohort.get('cohort')}**: size {cohort.get('size', 0)}, "
                f"retention {cohort.get('retention_signal')}"
            )
        return "\n".join(lines)

    if focus == "journey_opportunity_registry":
        registry = (sections.get("journey_opportunity_registry") or [{}])[0]
        lines = ["## Journey opportunities", ""]
        for opp in registry.get("opportunities") or []:
            lines.append(f"- **{opp.get('title')}** ({opp.get('opportunity_type')})")
        lines.append("", "Recommendations only — no automatic customer intervention.")
        return "\n".join(lines)

    if focus == "journey_priority_matrix":
        matrix = (sections.get("journey_priority_matrix") or [{}])[0]
        lines = ["## Journey priority matrix", ""]
        for opp in matrix.get("ranked_opportunities") or []:
            lines.append(f"- **{opp.get('title')}** — score {opp.get('priority_score')}")
        return "\n".join(lines) if len(lines) > 2 else "## Journey priority matrix\n\n(no ranked opportunities)"

    dashboard = (sections.get("customer_journey_dashboard") or [{}])[0]
    lines = [
        "## Customer journey dashboard",
        "",
        f"- Current stage: **{dashboard.get('current_stage', '—')}**",
        f"- Completed stages: **{dashboard.get('completed_stages', 0)}** / **{dashboard.get('journey_stage_count', 8)}**",
        f"- Drop-off points: **{dashboard.get('dropoff_point_count', 0)}**",
        f"- Stalled journeys: **{dashboard.get('stalled_journey_count', 0)}**",
        f"- Successful paths: **{dashboard.get('successful_path_count', 0)}**",
        f"- Friction hotspots: **{dashboard.get('friction_hotspot_count', 0)}**",
        f"- Cohorts tracked: **{dashboard.get('cohort_count', 0)}**",
        f"- Journey opportunities: **{dashboard.get('journey_opportunity_count', 0)}**",
        "",
        "## Privacy",
        "",
        "Journey intelligence ≠ customer manipulation. Tenant isolation preserved.",
    ]
    return "\n".join(lines)
