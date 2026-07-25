# SPDX-License-Identifier: Apache-2.0
"""FIX 319 — composed feedback evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
    list_feedback_review_records,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
    list_improvement_review_records,
)
from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_store import (
    list_analytics_review_records,
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


def _section_block(payload: dict[str, Any], section: str) -> dict[str, Any]:
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def collect_feedback_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
        build_autonomous_capability_registry,
    )
    from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
        build_capability_registry_runtime_integration,
    )
    from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_service import (
        build_continuous_product_improvement,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
        build_customer_support_success_foundation,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
        build_limited_beta_launch_program,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
        build_product_analytics_foundation,
    )
    from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_service import (
        build_provider_connection_experience,
    )
    from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
        build_public_product_experience,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
        build_tenant_onboarding_activation,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_295", "autonomous_capability_registry", build_autonomous_capability_registry),
        ("fix_296", "capability_registry_runtime_integration", build_capability_registry_runtime_integration),
        ("fix_301", "tenant_onboarding_activation", build_tenant_onboarding_activation),
        ("fix_303", "provider_connection_experience", build_provider_connection_experience),
        ("fix_310", "customer_support_success_foundation", build_customer_support_success_foundation),
        ("fix_311", "public_product_experience", build_public_product_experience),
        ("fix_312", "limited_beta_launch_program", build_limited_beta_launch_program),
        ("fix_317", "continuous_product_improvement", build_continuous_product_improvement),
        ("fix_318", "product_analytics_foundation", build_product_analytics_foundation),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["feedback_review_records"] = [
        r for r in list_feedback_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]
    bundle["improvement_review_records"] = [
        r for r in list_improvement_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]
    bundle["analytics_review_records"] = [
        r for r in list_analytics_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
