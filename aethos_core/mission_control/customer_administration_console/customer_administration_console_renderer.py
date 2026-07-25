# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — customer administration console renderer."""

from __future__ import annotations

from typing import Any


def render_customer_administration_console(
    payload: dict[str, Any],
    *,
    focus: str = "customer_administration_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("customer_administration_dashboard") or [{}])[0]
    organization = (sections.get("organization_administration_report") or [{}])[0]
    users = (sections.get("user_administration_report") or [{}])[0]
    roles = (sections.get("role_administration_report") or [{}])[0]
    workspaces = (sections.get("workspace_administration_report") or [{}])[0]
    projects = (sections.get("project_administration_report") or [{}])[0]
    providers = (sections.get("provider_administration_report") or [{}])[0]
    channels = (sections.get("channel_administration_report") or [{}])[0]
    billing = (sections.get("billing_administration_report") or [{}])[0]
    governance = (sections.get("governance_administration_report") or [{}])[0]

    lines = [
        "# Customer Administration Console",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 306')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Administration visibility ≠ administrative authority. No governance bypass.",
        "",
        f"Requester role: **{payload.get('requester_role', '—')}** · "
        f"Admin access: **{dashboard.get('admin_access_allowed', False)}**",
        "",
        "## Customer administration dashboard",
        "",
        f"- Organization health: **{dashboard.get('organization_health', '—')}**",
        f"- User health: **{dashboard.get('user_health', '—')}**",
        f"- Provider health: **{dashboard.get('provider_health', '—')}**",
        f"- Channel health: **{dashboard.get('channel_health', '—')}**",
        f"- Billing health: **{dashboard.get('billing_health', '—')}**",
        f"- Governance health: **{dashboard.get('governance_health', '—')}**",
        "",
    ]

    if focus in {"customer_administration_dashboard", "organization_administration_report"}:
        lines.extend(
            [
                "## Organization administration",
                "",
                f"- **{organization.get('organization_name', '—')}** ({organization.get('organization_id', '—')})",
                f"- Trust status: **{organization.get('trust_status', '—')}**",
                f"- Subscription: **{organization.get('subscription_status', '—')}**",
                f"- Workspaces: **{organization.get('workspace_count', 0)}** · Projects: **{organization.get('project_count', 0)}**",
                "",
            ]
        )

    if focus in {"customer_administration_dashboard", "user_administration_report"}:
        lines.extend(["## User administration", ""])
        if not users.get("admin_access_allowed"):
            lines.append("- Admin access required — viewer cannot access admin-only user administration.")
        for user in users.get("users") or []:
            lines.append(f"- **{user.get('user_id')}**: {user.get('role')} ({user.get('status')})")
        lines.append("")

    if focus in {"customer_administration_dashboard", "role_administration_report"}:
        lines.extend(["## Role administration", ""])
        for row in roles.get("roles") or []:
            lines.append(f"**{row.get('role')}**")
            findings = row.get("least_privilege_findings") or []
            if findings:
                lines.append(f"- Findings: {', '.join(findings)}")
            lines.append("")

    if focus == "customer_administration_dashboard":
        lines.extend(
            [
                "## Workspace administration",
                "",
                f"Workspaces: **{workspaces.get('workspace_count', 0)}**",
                "",
                "## Project administration",
                "",
                f"Projects: **{projects.get('project_count', 0)}**",
                "",
            ]
        )

    if focus in {"customer_administration_dashboard", "provider_administration_report"}:
        lines.extend(
            [
                "## Provider administration",
                "",
                f"Connected providers: **{providers.get('connected_providers', 0)}**",
            ]
        )
        for row in providers.get("readiness_summary") or []:
            lines.append(f"- **{row.get('provider')}**: {row.get('readiness')} ({row.get('status')})")
        for gap in providers.get("permission_gaps") or []:
            lines.append(f"- Gap: **{gap.get('provider')}** — {gap.get('gap')}")
        lines.append("")

    if focus == "customer_administration_dashboard":
        lines.extend(
            [
                "## Channel administration",
                "",
                f"Connected channels: **{channels.get('connected_channels', 0)}** / **{channels.get('total_channels', 0)}**",
                f"Identity health: **{channels.get('identity_mapping_health', '—')}**",
                f"Authorization health: **{channels.get('authorization_health', '—')}**",
                "",
            ]
        )

    if focus in {"customer_administration_dashboard", "billing_administration_report"}:
        lines.extend(
            [
                "## Billing administration",
                "",
                f"Plan: **{billing.get('plan', '—')}**",
            ]
        )
        for feature in billing.get("entitlements") or []:
            lines.append(f"- {feature}")
        lines.append("")

    if focus in {"customer_administration_dashboard", "governance_administration_report"}:
        lines.extend(["## Governance administration", ""])
        for row in governance.get("governance_actions") or []:
            lines.append(
                f"- **{row.get('action')}**: allowed={row.get('allowed')} (mutation blocked)"
            )
        lines.append("")

    lines.extend(
        [
            "No automatic user creation, permission grants, or billing mutation. "
            "Use `administration note:` and `administration review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
