# SPDX-License-Identifier: Apache-2.0
"""FIX 310 — customer support & success foundation renderer."""

from __future__ import annotations

from typing import Any


def render_customer_support_success_foundation(
    payload: dict[str, Any],
    *,
    focus: str = "customer_support_success_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("customer_support_success_dashboard") or [{}])[0]
    success = (sections.get("customer_success_dashboard") or [{}])[0]
    risks = (sections.get("customer_risk_registry") or [{}])[0]
    analytics = (sections.get("support_analytics_dashboard") or [{}])[0]

    lines = [
        "# Customer Support & Success Foundation",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 310')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Customer support visibility ≠ customer support authority. Humans remain responsible.",
        "",
        f"Customer support authority: **{payload.get('customer_support_authority', False)}**",
        "",
    ]

    if focus in {"customer_support_success_dashboard", "customer_success_dashboard", "customer_health_registry"}:
        lines.extend(
            [
                "## Customer health summary",
                "",
                f"Healthy: **{dashboard.get('healthy_count', success.get('healthy_count', 0))}**",
                f"At risk: **{dashboard.get('at_risk_count', success.get('at_risk_count', 0))}**",
                f"New: **{dashboard.get('new_customer_count', success.get('new_count', 0))}**",
                f"High value: **{dashboard.get('high_value_count', success.get('high_value_count', 0))}**",
                "",
            ]
        )

    if focus == "customer_health_registry":
        health = (sections.get("customer_health_registry") or [{}])[0]
        for row in (health.get("organizations") or [])[:8]:
            lines.append(
                f"- **{row.get('org_name')}** ({row.get('health_status')}): "
                f"{row.get('workspace_count', 0)} workspaces"
            )
        lines.append("")

    if focus == "customer_adoption_report":
        adoption = (sections.get("customer_adoption_report") or [{}])[0]
        lines.extend(["## Adoption checks", ""])
        for check in adoption.get("checks") or []:
            status = "ready" if check.get("ready") else "gap"
            lines.append(f"- {check.get('label')}: **{status}**")
        lines.append("")

    if focus in {"customer_escalation_registry", "customer_support_success_dashboard"}:
        escalations = (sections.get("customer_escalation_registry") or [{}])[0]
        lines.extend(["## Escalations", ""])
        for row in (escalations.get("escalations") or [])[:5]:
            lines.append(f"- [{row.get('severity')}] {row.get('org_name')}: {row.get('detail')}")
        if not escalations.get("escalations"):
            lines.append("- No open escalations from composed evidence.")
        lines.append("")

    if focus in {"customer_support_success_dashboard", "customer_risk_registry"}:
        lines.extend(["## Support risks", ""])
        for row in (risks.get("risks") or [])[:6]:
            lines.append(f"- [{row.get('level')}] {row.get('org_name')}: {row.get('detail')}")
        lines.append("")

    if focus == "support_analytics_dashboard":
        lines.extend(
            [
                "## Support analytics",
                "",
                f"Customers tracked: **{analytics.get('customer_count', 0)}**",
                f"Open escalations: **{analytics.get('open_escalation_count', 0)}**",
                f"Support notes: **{analytics.get('support_note_count', 0)}**",
                f"Success notes: **{analytics.get('customer_success_note_count', 0)}**",
                "",
            ]
        )

    if focus == "customer_support_success_dashboard":
        coverage = dashboard.get("evidence_coverage") or {}
        lines.extend(
            [
                "## Evidence coverage",
                "",
                f"FIX 300–309 composed: **{coverage.get('fix_300_309_composed', 0)}** / **{coverage.get('fix_300_309_total', 10)}**",
                "",
                "## Recommendations",
                "",
            ]
        )
        for item in dashboard.get("recommendations") or []:
            lines.append(f"- {item}")

    lines.extend(
        [
            "",
            "No customer messaging, ticket execution, or automatic intervention. "
            "Use `support note:` and `support review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
