# SPDX-License-Identifier: Apache-2.0
"""FIX 306 — chat router for customer administration console."""

from __future__ import annotations

from aethos_core.mission_control.customer_administration_console.customer_administration_console_contract import (
    ADMINISTRATION_AUTHORITY_FIX_306,
    AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306,
    AUTOMATIC_USER_CREATION_ENABLED_FIX_306,
    BILLING_MUTATION_AUTHORITY_FIX_306,
    CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306,
    CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID,
    MUTATION_PERFORMED_FIX_306,
    TRUST_MUTATION_AUTHORITY_FIX_306,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_intent import (
    handle_customer_administration_console_intent,
    parse_customer_administration_console_intent,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_renderer import (
    render_customer_administration_console,
)
from aethos_core.mission_control.customer_administration_console.customer_administration_console_service import (
    build_customer_administration_console,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": CUSTOMER_ADMINISTRATION_CONSOLE_ROUTE_ID,
        "matched_module": (
            "mission_control.customer_administration_console.customer_administration_console_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_306 is False else "true",
        "administration_authority": "false" if ADMINISTRATION_AUTHORITY_FIX_306 is False else "true",
        "automatic_user_creation_enabled": "false"
        if AUTOMATIC_USER_CREATION_ENABLED_FIX_306 is False
        else "true",
        "automatic_permission_granting_enabled": "false"
        if AUTOMATIC_PERMISSION_GRANTING_ENABLED_FIX_306 is False
        else "true",
        "cross_tenant_administration_enabled": "false"
        if CROSS_TENANT_ADMINISTRATION_ENABLED_FIX_306 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_306 is False else "true",
        "billing_mutation_authority": "false" if BILLING_MUTATION_AUTHORITY_FIX_306 is False else "true",
        "mutation_scope": "customer_administration_console",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "administration_visibility_not_authority",
        **extra,
    }


def route_customer_administration_console(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_customer_administration_console_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_customer_administration_console_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded administration note ({record.get('kind', 'note')}). "
            "Administration visibility ≠ administrative authority."
        )
        return (
            body,
            "mission_control_customer_administration_console_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "customer_administration_dashboard")
    result = build_customer_administration_console(session_id=sid)
    markdown = render_customer_administration_console(
        result.customer_administration_console,
        focus=focus,
    )
    dashboard = (
        (result.customer_administration_console.get("sections") or {})
        .get("customer_administration_dashboard", [{}])[0]
    )
    headline = (
        f"Organization **{dashboard.get('organization_id', '—')}** · "
        f"Admin access **{dashboard.get('admin_access_allowed', False)}**. "
        "Unified administration visibility — no authority escalation or automatic mutations."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_customer_administration_console",
        _meta(sid, stage="view", focus=focus),
    )
