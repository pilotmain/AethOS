# SPDX-License-Identifier: Apache-2.0
"""FIX 305 — chat router for billing & entitlements foundation."""

from __future__ import annotations

from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_contract import (
    AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305,
    AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305,
    AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305,
    BILLING_AUTHORITY_FIX_305,
    BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID,
    MUTATION_PERFORMED_FIX_305,
    PAYMENT_PROCESSING_ENABLED_FIX_305,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_intent import (
    handle_billing_entitlements_foundation_intent,
    parse_billing_entitlements_foundation_intent,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_renderer import (
    render_billing_entitlements_foundation,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": BILLING_ENTITLEMENTS_FOUNDATION_ROUTE_ID,
        "matched_module": (
            "mission_control.billing_entitlements_foundation.billing_entitlements_foundation_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_305 is False else "true",
        "billing_authority": "false" if BILLING_AUTHORITY_FIX_305 is False else "true",
        "automatic_subscription_creation_enabled": "false"
        if AUTOMATIC_SUBSCRIPTION_CREATION_ENABLED_FIX_305 is False
        else "true",
        "automatic_plan_upgrade_enabled": "false"
        if AUTOMATIC_PLAN_UPGRADE_ENABLED_FIX_305 is False
        else "true",
        "automatic_plan_downgrade_enabled": "false"
        if AUTOMATIC_PLAN_DOWNGRADE_ENABLED_FIX_305 is False
        else "true",
        "payment_processing_enabled": "false"
        if PAYMENT_PROCESSING_ENABLED_FIX_305 is False
        else "true",
        "mutation_scope": "billing_entitlements_foundation",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "billing_entitlements_not_authority",
        **extra,
    }


def route_billing_entitlements_foundation(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_billing_entitlements_foundation_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_billing_entitlements_foundation_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded billing note ({record.get('kind', 'note')}). "
            "Entitlements ≠ authority — no payment processing or plan mutation."
        )
        return (
            body,
            "mission_control_billing_entitlements_foundation_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "billing_dashboard")
    result = build_billing_entitlements_foundation(session_id=sid)
    markdown = render_billing_entitlements_foundation(
        result.billing_entitlements_foundation,
        focus=focus,
    )
    dashboard = (
        (result.billing_entitlements_foundation.get("sections") or {})
        .get("billing_dashboard", [{}])[0]
    )
    headline = (
        f"Plan **{dashboard.get('plan', 'FREE')}**. "
        "Entitlements control access — paid users still follow the same governance rules. "
        "No payment collection or automatic plan mutation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_billing_entitlements_foundation",
        _meta(sid, stage="view", focus=focus),
    )
