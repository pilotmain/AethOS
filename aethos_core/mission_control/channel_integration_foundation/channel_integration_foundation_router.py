# SPDX-License-Identifier: Apache-2.0
"""FIX 304 — chat router for channel integration foundation."""

from __future__ import annotations

from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_contract import (
    AUTHORIZATION_BYPASS_ENABLED_FIX_304,
    AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304,
    CHANNEL_AUTHORITY_FIX_304,
    CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID,
    CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304,
    CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304,
    MUTATION_PERFORMED_FIX_304,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_intent import (
    handle_channel_integration_foundation_intent,
    parse_channel_integration_foundation_intent,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_renderer import (
    render_channel_integration_foundation,
)
from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
    build_channel_integration_foundation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CHANNEL_INTEGRATION_FOUNDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.channel_integration_foundation.channel_integration_foundation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_304 is False else "true",
        "channel_authority": "false" if CHANNEL_AUTHORITY_FIX_304 is False else "true",
        "automatic_channel_provisioning_enabled": "false"
        if AUTOMATIC_CHANNEL_PROVISIONING_ENABLED_FIX_304 is False
        else "true",
        "cross_channel_identity_bypass_enabled": "false"
        if CROSS_CHANNEL_IDENTITY_BYPASS_ENABLED_FIX_304 is False
        else "true",
        "cross_tenant_channel_access_enabled": "false"
        if CROSS_TENANT_CHANNEL_ACCESS_ENABLED_FIX_304 is False
        else "true",
        "authorization_bypass_enabled": "false"
        if AUTHORIZATION_BYPASS_ENABLED_FIX_304 is False
        else "true",
        "mutation_scope": "channel_integration_foundation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "channel_integration_not_channel_specific_logic",
        **extra,
    }


def route_channel_integration_foundation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_channel_integration_foundation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_channel_integration_foundation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded channel note ({record.get('kind', 'note')}). "
            "Channel integration ≠ channel-specific logic."
        )
        return (
            body,
            "mission_control_channel_integration_foundation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "channel_dashboard")
    result = build_channel_integration_foundation(session_id=sid)
    markdown = render_channel_integration_foundation(
        result.channel_integration_foundation,
        focus=focus,
    )
    dashboard = (
        (result.channel_integration_foundation.get("sections") or {})
        .get("channel_dashboard", [{}])[0]
    )
    headline = (
        f"Channels **{dashboard.get('total_channels', 0)}**, "
        f"connected **{dashboard.get('connected_channels', 0)}**. "
        "All channels route through Mission Control — no channel-specific governance or cross-tenant routing."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_channel_integration_foundation",
        _meta(sid, stage="view", focus=focus),
    )
