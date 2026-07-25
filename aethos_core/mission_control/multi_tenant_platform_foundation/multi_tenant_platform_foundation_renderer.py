# SPDX-License-Identifier: Apache-2.0
"""FIX 300 — multi-tenant platform foundation renderer."""

from __future__ import annotations

from typing import Any


def render_multi_tenant_platform_foundation(payload: dict[str, Any]) -> str:
    sections = dict(payload.get("sections") or {})
    dashboard = (sections.get("tenant_dashboard") or [{}])[0]
    organizations = (sections.get("organization_registry") or [{}])[0]
    workspaces = (sections.get("workspace_registry") or [{}])[0]
    projects = (sections.get("project_registry") or [{}])[0]
    identity = (sections.get("identity_registry") or [{}])[0]
    trust = (sections.get("tenant_trust_registry") or [{}])[0]
    channels = (sections.get("channel_registry") or [{}])[0]
    onboarding = (sections.get("tenant_onboarding_registry") or [{}])[0]

    lines = [
        "# Multi-Tenant Platform Foundation",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 300')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        f"- Organizations: **{dashboard.get('organization_count', 0)}**",
        f"- Workspaces: **{dashboard.get('workspace_count', 0)}**",
        f"- Projects: **{dashboard.get('project_count', 0)}**",
        f"- Users: **{dashboard.get('user_count', 0)}**",
        f"- Trust baselines: **{dashboard.get('trusted_repository_count', 0)}**",
        f"- Connected providers: **{dashboard.get('connected_provider_count', 0)}**",
        f"- Operational channels: **{dashboard.get('operational_channel_count', 0)}**",
        f"- Cross-tenant access: **{payload.get('cross_tenant_access_enabled', False)}**",
        f"- Human tenant approved: **{payload.get('human_tenant_decision_approve', False)}**",
        "",
        "## Organizations",
        "",
    ]

    for org in organizations.get("organizations") or []:
        lines.append(f"- **{org.get('name')}** ({org.get('organization_id')}) — plan {org.get('plan')}")

    lines.extend(["", "## Workspaces", ""])
    for ws in workspaces.get("workspaces") or []:
        lines.append(f"- **{ws.get('name')}** ({ws.get('workspace_id')}) — {ws.get('repo_hint')}")

    lines.extend(["", "## Projects", ""])
    for project in (projects.get("projects") or [])[:6]:
        lines.append(f"- **{project.get('display_name')}** — {project.get('product_signal', '—')}")

    lines.extend(["", "## Identity", ""])
    for member in identity.get("memberships") or []:
        lines.append(f"- **{member.get('user_id')}** — {member.get('role')}")

    lines.extend(["", "## Trust boundaries", ""])
    for repo in (trust.get("trust_reports") or [])[:5]:
        lines.append(
            f"- **{repo.get('display_name') or repo.get('repository')}**: {repo.get('trust_state', '—')}"
        )

    lines.extend(["", "## Channels", ""])
    for channel in channels.get("channels") or []:
        lines.append(f"- **{channel.get('channel')}**: {channel.get('status')}")

    lines.extend(["", "## Onboarding", ""])
    for step in onboarding.get("onboarding_steps") or []:
        lines.append(f"- {step}")

    lines.extend(
        [
            "",
            "## Human tenant review",
            "",
            "Record with:",
            "- `organization create review: …`",
            "- `workspace create review: …`",
            "- `project registration review: …`",
            "- `membership review: …`",
            "- `tenant governance review approve/hold/reject/defer: …`",
            "",
            "## Authority",
            "",
            "Multi-tenant foundation models tenancy only. "
            "Automatic tenant creation, cross-tenant access, and permission escalation remain **false**.",
        ]
    )
    return "\n".join(lines)
