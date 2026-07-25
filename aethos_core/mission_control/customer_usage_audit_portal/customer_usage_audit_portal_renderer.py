# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — customer usage & audit portal renderer."""

from __future__ import annotations

from typing import Any


def render_customer_usage_audit_portal(
    payload: dict[str, Any],
    *,
    focus: str = "customer_audit_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("customer_audit_dashboard") or [{}])[0]
    activity = (sections.get("activity_timeline") or [{}])[0]
    governance = (sections.get("governance_timeline") or [{}])[0]
    usage = (sections.get("usage_timeline") or [{}])[0]
    registry = (sections.get("audit_registry") or [{}])[0]
    evidence = (sections.get("evidence_explorer") or [{}])[0]
    billing_history = (sections.get("billing_usage_history_report") or [{}])[0]

    lines = [
        "# Customer Usage & Audit Portal",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 307')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Audit visibility ≠ audit authority. Records are immutable — no mutation or deletion.",
        "",
        f"Role: **{payload.get('requester_role', '—')}** · Audit access: **{dashboard.get('audit_access_allowed', False)}**",
        "",
        "## Customer audit dashboard",
        "",
        f"- Activity entries: **{dashboard.get('activity_entry_count', 0)}**",
        f"- Governance entries: **{dashboard.get('governance_entry_count', 0)}**",
        f"- Usage entries: **{dashboard.get('usage_entry_count', 0)}**",
        f"- Audit registry entries: **{dashboard.get('audit_registry_entry_count', 0)}**",
        f"- Billing plan: **{dashboard.get('billing_plan', '—')}**",
        f"- Audit health: **{dashboard.get('audit_health', '—')}**",
        "",
    ]

    if focus in {"customer_audit_dashboard", "activity_timeline"}:
        lines.extend(["## Activity timeline", ""])
        for entry in (activity.get("entries") or [])[:10]:
            lines.append(f"- **{entry.get('when', '—')}** · {entry.get('who', '—')}: {entry.get('what', entry.get('kind'))}")
        lines.append("")

    if focus in {"customer_audit_dashboard", "governance_timeline"}:
        lines.extend(["## Governance timeline", ""])
        for entry in (governance.get("entries") or [])[:10]:
            lines.append(f"- **{entry.get('when', '—')}** · {entry.get('kind', '—')}: {entry.get('what', '—')}")
        lines.append("")

    if focus in {"customer_audit_dashboard", "usage_timeline"}:
        lines.extend(["## Usage timeline", ""])
        snapshot = usage.get("usage_snapshot") or {}
        for key, value in snapshot.items():
            lines.append(f"- **{key}**: {value}")
        for entry in (usage.get("entries") or [])[:5]:
            lines.append(f"- {entry.get('kind', '—')}: {entry.get('what', '—')}")
        lines.append("")

    if focus == "customer_audit_dashboard":
        lines.extend(
            [
                "## Audit registry",
                "",
                f"Composed entries: **{registry.get('entry_count', 0)}**",
                "",
            ]
        )

    if focus in {"customer_audit_dashboard", "evidence_explorer"}:
        lines.extend(["## Evidence explorer", ""])
        for artifact in evidence.get("trust_freezes") or []:
            lines.append(f"- Trust freeze: **{artifact.get('kind', '—')}** ({artifact.get('recorded_at', '—')})")
        for artifact in evidence.get("governance_evidence") or []:
            lines.append(f"- Governance: **{artifact.get('kind', '—')}**")
        lines.append("")

    if focus in {"customer_audit_dashboard", "billing_usage_history_report"}:
        lines.extend(
            [
                "## Billing & usage history",
                "",
                f"Plan: **{billing_history.get('plan', '—')}**",
            ]
        )
        consumption = (billing_history.get("limit_consumption") or {}).get("limits") or []
        for row in consumption[:5]:
            lines.append(f"- {row.get('metric')}: {row.get('current')} / {row.get('maximum', 'unlimited')}")
        lines.append("")

    lines.extend(
        [
            "Cross-tenant audit access blocked. Use `audit note:` and "
            "`audit review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
