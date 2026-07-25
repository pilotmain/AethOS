# SPDX-License-Identifier: Apache-2.0
"""FIX 302 — chat router for identity and access hardening."""

from __future__ import annotations

from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_contract import (
    AUTHORIZATION_AUTHORITY_FIX_302,
    AUTHORIZATION_BYPASS_ENABLED_FIX_302,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302,
    AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302,
    CROSS_TENANT_ACCESS_ENABLED_FIX_302,
    IDENTITY_ACCESS_HARDENING_ROUTE_ID,
    MUTATION_PERFORMED_FIX_302,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_intent import (
    handle_identity_access_hardening_intent,
    parse_identity_access_hardening_intent,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_renderer import (
    render_identity_access_hardening,
)
from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
    build_identity_access_hardening,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": IDENTITY_ACCESS_HARDENING_ROUTE_ID,
        "matched_module": (
            "mission_control.identity_access_hardening.identity_access_hardening_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_302 is False else "true",
        "authorization_authority": "false" if AUTHORIZATION_AUTHORITY_FIX_302 is False else "true",
        "automatic_permission_granting_enabled": "false"
        if AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_302 is False
        else "true",
        "automatic_role_escalation_enabled": "false"
        if AUTOMATIC_ROLE_ESCALATION_ENABLED_FIX_302 is False
        else "true",
        "cross_tenant_access_enabled": "false"
        if CROSS_TENANT_ACCESS_ENABLED_FIX_302 is False
        else "true",
        "authorization_bypass_enabled": "false"
        if AUTHORIZATION_BYPASS_ENABLED_FIX_302 is False
        else "true",
        "mutation_scope": "identity_access_hardening",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "authorization_enforcement_not_escalation",
        **extra,
    }


def route_identity_access_hardening(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_identity_access_hardening_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_identity_access_hardening_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded authorization review note ({record.get('kind', 'note')}). "
            "Authorization enforcement ≠ authority escalation."
        )
        return (
            body,
            "mission_control_identity_access_hardening_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "authorization_dashboard")
    result = build_identity_access_hardening(session_id=sid)
    markdown = render_identity_access_hardening(result.identity_access_hardening, focus=focus)
    identity = (
        (result.identity_access_hardening.get("sections") or {})
        .get("identity_resolution_report", [{}])[0]
    )
    headline = (
        f"Identity resolved for **{identity.get('user_id', '—')}** as **{identity.get('role', '—')}** "
        f"in org **{identity.get('organization_id', '—')}**. "
        "Authorization enforcement ≠ authority escalation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_identity_access_hardening",
        _meta(sid, stage="view", focus=focus),
    )
