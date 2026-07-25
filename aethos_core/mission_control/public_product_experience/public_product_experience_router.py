# SPDX-License-Identifier: Apache-2.0
"""FIX 311 — chat router for public product experience."""

from __future__ import annotations

from aethos_core.mission_control.public_product_experience.public_product_experience_contract import (
    AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311,
    MUTATION_PERFORMED_FIX_311,
    PROVIDER_MUTATION_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_AUTHORITY_FIX_311,
    PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID,
    TENANT_MUTATION_AUTHORITY_FIX_311,
    TRUST_MUTATION_AUTHORITY_FIX_311,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_intent import (
    handle_public_product_experience_intent,
    parse_public_product_experience_intent,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_renderer import (
    render_public_product_experience,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": PUBLIC_PRODUCT_EXPERIENCE_ROUTE_ID,
        "matched_module": "mission_control.public_product_experience.public_product_experience_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false" if MUTATION_PERFORMED_FIX_311 is False else "true",
        "public_product_authority": "false" if PUBLIC_PRODUCT_AUTHORITY_FIX_311 is False else "true",
        "automatic_customer_onboarding_enabled": "false"
        if AUTOMATIC_CUSTOMER_ONBOARDING_ENABLED_FIX_311 is False
        else "true",
        "trust_mutation_authority": "false" if TRUST_MUTATION_AUTHORITY_FIX_311 is False else "true",
        "provider_mutation_authority": "false" if PROVIDER_MUTATION_AUTHORITY_FIX_311 is False else "true",
        "tenant_mutation_authority": "false" if TENANT_MUTATION_AUTHORITY_FIX_311 is False else "true",
        "mutation_scope": "public_product_experience",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "mission_control_stage": stage,
        "lane_separation": "public_experience_not_platform_authority",
        **extra,
    }


def route_public_product_experience(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    intent = parse_public_product_experience_intent(text)
    if intent is None:
        return None

    sid = (session_id or "default").strip()[:64] or "default"
    handled = handle_public_product_experience_intent(intent, session_id=sid)

    if handled.get("action") == "record":
        record = handled.get("record") or {}
        body = (
            f"Recorded public experience note ({record.get('kind', 'note')}). "
            "Public product experience ≠ platform authority."
        )
        return (
            body,
            "mission_control_public_product_experience_record",
            _meta(sid, stage="record", record_kind=str(record.get("kind") or "")),
        )

    focus = str(handled.get("focus") or "public_product_dashboard")
    result = build_public_product_experience(session_id=sid)
    markdown = render_public_product_experience(result.public_product_experience, focus=focus)
    dashboard = (
        (result.public_product_experience.get("sections") or {}).get("public_product_dashboard", [{}])[0]
    )
    headline = (
        f"Public product surface with **{dashboard.get('proven_capability_count', 0)}** proven capabilities "
        "and trust baselines — explainable without internal documentation."
    )
    body = f"{headline}\n\n{markdown}"
    return (
        body,
        "mission_control_public_product_experience",
        _meta(
            sid,
            stage="view",
            focus=focus,
            proven_count=str(dashboard.get("proven_capability_count") or 0),
        ),
    )
