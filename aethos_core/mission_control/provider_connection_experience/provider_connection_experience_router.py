# SPDX-License-Identifier: Apache-2.0
"""FIX 303 — chat router for provider connection experience."""

from __future__ import annotations

from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_contract import (
    AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303,
    MUTATION_PERFORMED_FIX_303,
    PERMISSION_ESCALATION_ENABLED_FIX_303,
    PROVIDER_CONNECTION_AUTHORITY_FIX_303,
    PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID,
    PROVIDER_MUTATION_AUTHORITY_FIX_303,
    SECRET_COLLECTION_ENABLED_FIX_303,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_intent import (
    handle_provider_connection_experience_intent,
    parse_provider_connection_experience_intent,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_renderer import (
    render_provider_connection_experience,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
    build_provider_connection_experience,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PROVIDER_CONNECTION_EXPERIENCE_ROUTE_ID,
        "matched_module": (
            "mission_control.provider_connection_experience.provider_connection_experience_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_303 is False else "true",
        "provider_connection_authority": "false"
        if PROVIDER_CONNECTION_AUTHORITY_FIX_303 is False
        else "true",
        "automatic_provider_connection_enabled": "false"
        if AUTOMATIC_PROVIDER_CONNECTION_ENABLED_FIX_303 is False
        else "true",
        "provider_mutation_authority": "false" if PROVIDER_MUTATION_AUTHORITY_FIX_303 is False else "true",
        "secret_collection_enabled": "false" if SECRET_COLLECTION_ENABLED_FIX_303 is False else "true",
        "permission_escalation_enabled": "false"
        if PERMISSION_ESCALATION_ENABLED_FIX_303 is False
        else "true",
        "mutation_scope": "provider_connection_experience",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "provider_connection_guidance_not_mutation",
        **extra,
    }


def route_provider_connection_experience(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_provider_connection_experience_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_provider_connection_experience_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded provider connection note ({record.get('kind', 'note')}). "
            "Provider connection guidance ≠ provider mutation authority."
        )
        return (
            body,
            "mission_control_provider_connection_experience_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "provider_connection_dashboard")
    result = build_provider_connection_experience(session_id=sid)
    markdown = render_provider_connection_experience(result.provider_connection_experience, focus=focus)
    dashboard = (
        (result.provider_connection_experience.get("sections") or {})
        .get("provider_connection_dashboard", [{}])[0]
    )
    headline = (
        f"Phase 1 providers **{len(dashboard.get('phase_1_providers') or [])}**, "
        f"connected **{dashboard.get('connected_provider_count', 0)}**. "
        "Manual connection in Settings — never automatic provisioning or secret collection in chat."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_provider_connection_experience",
        _meta(sid, stage="view", focus=focus),
    )
