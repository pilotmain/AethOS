# SPDX-License-Identifier: Apache-2.0
"""FIX 308 — chat router for payment integration readiness."""

from __future__ import annotations

from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_contract import (
    AUTOMATIC_CHARGING_ENABLED_FIX_308,
    AUTOMATIC_REFUND_ENABLED_FIX_308,
    CREDIT_CARD_STORAGE_ENABLED_FIX_308,
    MUTATION_PERFORMED_FIX_308,
    PAYMENT_INTEGRATION_READINESS_ROUTE_ID,
    PAYMENT_PROCESSING_ENABLED_FIX_308,
    SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_intent import (
    handle_payment_integration_readiness_intent,
    parse_payment_integration_readiness_intent,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_renderer import (
    render_payment_integration_readiness,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PAYMENT_INTEGRATION_READINESS_ROUTE_ID,
        "matched_module": (
            "mission_control.payment_integration_readiness.payment_integration_readiness_router"
        ),
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_308 is False else "true",
        "payment_processing_enabled": "false"
        if PAYMENT_PROCESSING_ENABLED_FIX_308 is False
        else "true",
        "credit_card_storage_enabled": "false"
        if CREDIT_CARD_STORAGE_ENABLED_FIX_308 is False
        else "true",
        "automatic_charging_enabled": "false"
        if AUTOMATIC_CHARGING_ENABLED_FIX_308 is False
        else "true",
        "automatic_refund_enabled": "false"
        if AUTOMATIC_REFUND_ENABLED_FIX_308 is False
        else "true",
        "subscription_mutation_authority": "false"
        if SUBSCRIPTION_MUTATION_AUTHORITY_FIX_308 is False
        else "true",
        "mutation_scope": "payment_integration_readiness",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "payment_readiness_not_processing",
        **extra,
    }


def route_payment_integration_readiness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_payment_integration_readiness_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_payment_integration_readiness_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded payment readiness note ({record.get('kind', 'note')}). "
            "Payment readiness ≠ payment processing."
        )
        return (
            body,
            "mission_control_payment_integration_readiness_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "payment_readiness_dashboard")
    result = build_payment_integration_readiness(session_id=sid)
    markdown = render_payment_integration_readiness(
        result.payment_integration_readiness,
        focus=focus,
    )
    dashboard = (
        (result.payment_integration_readiness.get("sections") or {})
        .get("payment_readiness_dashboard", [{}])[0]
    )
    headline = (
        f"Subscription readiness **{dashboard.get('subscription_readiness', '—')}**. "
        "Future payment architecture modeled — no charging, card storage, or subscription mutation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_payment_integration_readiness",
        _meta(sid, stage="view", focus=focus),
    )
