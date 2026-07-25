# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — channel integration foundation renderer."""

from __future__ import annotations

from typing import Any


def render_channel_integration_foundation(
    payload: dict[str, Any],
    *,
    focus: str = "channel_dashboard",
) -> str:
    sections = dict(payload.get("sections") or {})
    registry = (sections.get("channel_registry") or [{}])[0]
    identity = (sections.get("channel_identity_report") or [{}])[0]
    authorization = (sections.get("channel_authorization_report") or [{}])[0]
    capability = (sections.get("channel_capability_matrix") or [{}])[0]
    dashboard = (sections.get("channel_dashboard") or [{}])[0]
    web = (sections.get("web_channel_report") or [{}])[0]
    telegram = (sections.get("telegram_channel_report") or [{}])[0]
    slack = (sections.get("slack_channel_report") or [{}])[0]
    email = (sections.get("email_channel_report") or [{}])[0]
    voice = (sections.get("voice_channel_report") or [{}])[0]

    lines = [
        "# Channel Integration Foundation",
        "",
        f"**Fix:** {payload.get('fix', 'FIX 304')}",
        f"**Invariant:** {payload.get('invariant', '')}",
        "",
        "Channel integration ≠ channel-specific logic. All channels route into Mission Control core.",
        "",
        "## Channel dashboard",
        "",
        f"Connected channels: **{dashboard.get('connected_channels', 0)}** / **{dashboard.get('total_channels', 0)}**.",
        f"Ingress model: **{dashboard.get('ingress_model', 'all_channels_route_to_mission_control_core')}**.",
        "",
    ]

    if focus in {"channel_dashboard", "channel_readiness"}:
        lines.extend(["## Channel readiness", ""])
        for row in dashboard.get("readiness_summary") or registry.get("channels") or []:
            lines.append(
                f"- **{row.get('channel')}**: {row.get('readiness')} ({row.get('status')})"
            )

    if focus in {"channel_dashboard", "channel_authorization_report"}:
        lines.extend(
            [
                "",
                "## Channel authorization",
                "",
                f"Authorization model: **{authorization.get('authorization_model', 'same_as_mission_control_core')}**.",
                f"Tenant isolation enforced: **{authorization.get('tenant_isolation_enforced', True)}**.",
                f"Authorization bypass enabled: **{authorization.get('authorization_bypass_enabled', False)}**.",
            ]
        )
        for row in authorization.get("channels") or []:
            lines.append(f"- **{row.get('channel', row.get('name', 'channel'))}**: FIX 302 composed")

    if focus in {"channel_dashboard", "channel_capability_matrix"}:
        lines.extend(["", "## Channel capability matrix", ""])
        for row in capability.get("channels") or []:
            lines.append(f"**{row.get('channel')}**")
            for action in row.get("supported_actions") or []:
                lines.append(f"- Supported: {action}")
            for action in row.get("unsupported_actions") or []:
                lines.append(f"- Unsupported: {action}")
            lines.append("")

    if focus == "channel_dashboard":
        lines.extend(
            [
                "## Web channel (reference)",
                "",
                f"- Status: **{web.get('status', 'OPERATIONAL')}**",
                f"- Ingress: **{web.get('ingress', 'mission_control_core')}**",
                "",
                "## Telegram channel",
                "",
                f"- Bot readiness: **{telegram.get('bot_readiness', '—')}**",
                f"- Configured: **{telegram.get('configured', False)}**",
                "",
                "## Slack channel",
                "",
                f"- Workspace readiness: **{slack.get('workspace_readiness', 'planned')}**",
                f"- Status: **{slack.get('status', 'PLANNED')}**",
                "",
                "## Email channel",
                "",
                f"- Inbound: **{email.get('inbound_readiness', 'planned')}**",
                f"- Outbound: **{email.get('outbound_readiness', 'planned')}**",
                "",
                "## Voice channel (future)",
                "",
                f"- Voice readiness: **{voice.get('voice_readiness', 'planned')}**",
                "",
                "## Channel identity mapping",
                "",
                f"- Platform user: **{identity.get('platform_user_id', '—')}**",
                f"- Organization: **{identity.get('organization_id', '—')}**",
                f"- Role: **{identity.get('role', '—')}**",
            ]
        )

    lines.extend(
        [
            "",
            "No channel-specific governance or cross-tenant routing. Use `channel note:` and "
            "`channel review approve:` for human review records only.",
        ]
    )
    return "\n".join(lines)
