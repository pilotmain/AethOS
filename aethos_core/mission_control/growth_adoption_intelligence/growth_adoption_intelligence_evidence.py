# SPDX-License-Identifier: Apache-2.0
"""FIX 320 — composed growth evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_store import (
    list_growth_review_records,
)


def _safe_build(name: str, builder, *, session_id: str) -> tuple[Any, bool]:
    try:
        result = builder(session_id=session_id)
        return result, bool(getattr(result, "ok", True))
    except Exception:
        return None, False


def _payload(result: Any, attr: str) -> dict[str, Any]:
    if not result:
        return {}
    board = getattr(result, attr, None)
    return board if isinstance(board, dict) else {}


def collect_growth_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
        build_billing_entitlements_foundation,
    )
    from aethos_core.mission_control.channel_integration_foundation.channel_integration_foundation_service import (
        build_channel_integration_foundation,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
        build_customer_feedback_intelligence,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
        build_customer_support_success_foundation,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
        build_limited_beta_launch_program,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
        build_payment_integration_readiness,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
        build_product_analytics_foundation,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
        build_provider_connection_experience,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
        build_tenant_onboarding_activation,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
        build_multi_tenant_platform_foundation,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_300", "multi_tenant_platform_foundation", build_multi_tenant_platform_foundation),
        ("fix_301", "tenant_onboarding_activation", build_tenant_onboarding_activation),
        ("fix_303", "provider_connection_experience", build_provider_connection_experience),
        ("fix_304", "channel_integration_foundation", build_channel_integration_foundation),
        ("fix_305", "billing_entitlements_foundation", build_billing_entitlements_foundation),
        ("fix_308", "payment_integration_readiness", build_payment_integration_readiness),
        ("fix_310", "customer_support_success_foundation", build_customer_support_success_foundation),
        ("fix_312", "limited_beta_launch_program", build_limited_beta_launch_program),
        ("fix_318", "product_analytics_foundation", build_product_analytics_foundation),
        ("fix_319", "customer_feedback_intelligence", build_customer_feedback_intelligence),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["growth_review_records"] = [
        r for r in list_growth_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
