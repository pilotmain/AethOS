# SPDX-License-Identifier: Apache-2.0
"""FIX 322 — composed PMF evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
    list_pmf_review_records,
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


def collect_pmf_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
        build_autonomous_capability_registry,
    )
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
        build_capability_registry_runtime_integration,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
        build_customer_feedback_intelligence,
    )
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service import (
        build_customer_journey_intelligence,
    )
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
        build_growth_adoption_intelligence,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
        build_product_analytics_foundation,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_295", "autonomous_capability_registry", build_autonomous_capability_registry),
        ("fix_296", "capability_registry_runtime_integration", build_capability_registry_runtime_integration),
        ("fix_318", "product_analytics_foundation", build_product_analytics_foundation),
        ("fix_319", "customer_feedback_intelligence", build_customer_feedback_intelligence),
        ("fix_320", "growth_adoption_intelligence", build_growth_adoption_intelligence),
        ("fix_321", "customer_journey_intelligence", build_customer_journey_intelligence),
    )

    for key, attr, builder in builders:
        if key in ("fix_295", "fix_296"):
            from aethos_core.workstreams.intelligence_scalability_implementation_program.intelligence_scalable_compose_bridge import (
                memoized_compose_build,
            )

            payload, ok = memoized_compose_build(
                session_id=sid, module_key=key, attr=attr, builder=builder
            )
            bundle[key] = payload
            bundle["sources_ok"][key] = ok
            continue

        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["pmf_review_records"] = [
        r for r in list_pmf_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
