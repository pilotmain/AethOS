# SPDX-License-Identifier: Apache-2.0
"""FIX 307 — chat router for customer usage & audit portal."""

from __future__ import annotations

from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_contract import (
    AUDIT_AUTHORITY_FIX_307,
    AUDIT_MUTATION_ENABLED_FIX_307,
    AUTHORIZATION_BYPASS_ENABLED_FIX_307,
    CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307,
    CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID,
    EVIDENCE_MUTATION_ENABLED_FIX_307,
    MUTATION_PERFORMED_FIX_307,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_intent import (
    handle_customer_usage_audit_portal_intent,
    parse_customer_usage_audit_portal_intent,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_renderer import (
    render_customer_usage_audit_portal,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
    build_customer_usage_audit_portal,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_USAGE_AUDIT_PORTAL_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_usage_audit_portal.customer_usage_audit_portal_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_307 is False else "true",
        "audit_authority": "false" if AUDIT_AUTHORITY_FIX_307 is False else "true",
        "audit_mutation_enabled": "false" if AUDIT_MUTATION_ENABLED_FIX_307 is False else "true",
        "evidence_mutation_enabled": "false"
        if EVIDENCE_MUTATION_ENABLED_FIX_307 is False
        else "true",
        "cross_tenant_audit_access_enabled": "false"
        if CROSS_TENANT_AUDIT_ACCESS_ENABLED_FIX_307 is False
        else "true",
        "authorization_bypass_enabled": "false"
        if AUTHORIZATION_BYPASS_ENABLED_FIX_307 is False
        else "true",
        "mutation_scope": "customer_usage_audit_portal",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "audit_visibility_not_authority",
        **extra,
    }


def route_customer_usage_audit_portal(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_usage_audit_portal_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_usage_audit_portal_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded audit note ({record.get('kind', 'note')}). "
            "Audit visibility ≠ audit authority — records remain immutable."
        )
        return (
            body,
            "mission_control_customer_usage_audit_portal_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_audit_dashboard")
    result = build_customer_usage_audit_portal(session_id=sid)
    markdown = render_customer_usage_audit_portal(
        result.customer_usage_audit_portal,
        focus=focus,
    )
    dashboard = (
        (result.customer_usage_audit_portal.get("sections") or {})
        .get("customer_audit_dashboard", [{}])[0]
    )
    headline = (
        f"Audit registry **{dashboard.get('audit_registry_entry_count', 0)}** entries. "
        "Complete tenant transparency — what happened, who did it, when — without audit mutation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_usage_audit_portal",
        _meta(sid, stage="view", focus=focus),
    )
