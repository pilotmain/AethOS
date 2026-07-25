# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — composed improvement evidence."""

from __future__ import annotations

from typing import Any


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


def collect_improvement_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
        build_billing_entitlements_foundation,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
        build_customer_support_success_foundation,
    )
    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
        build_customer_usage_audit_portal,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
        build_governed_monitoring_lifecycle,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
        build_governed_rollback_lifecycle,
    )
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
        build_identity_access_hardening,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
        build_launch_operations_center,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
        build_limited_beta_launch_program,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
        build_multi_tenant_platform_foundation,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
        build_payment_integration_readiness,
    )
    from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
        build_public_product_experience,
    )
    from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_service import (
        build_tenant_onboarding_activation,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_300", "multi_tenant_platform_foundation", build_multi_tenant_platform_foundation),
        ("fix_301", "tenant_onboarding_activation", build_tenant_onboarding_activation),
        ("fix_302", "identity_access_hardening", build_identity_access_hardening),
        ("fix_305", "billing_entitlements_foundation", build_billing_entitlements_foundation),
        ("fix_307", "customer_usage_audit_portal", build_customer_usage_audit_portal),
        ("fix_308", "payment_integration_readiness", build_payment_integration_readiness),
        ("fix_310", "customer_support_success_foundation", build_customer_support_success_foundation),
        ("fix_311", "public_product_experience", build_public_product_experience),
        ("fix_312", "limited_beta_launch_program", build_limited_beta_launch_program),
        ("fix_220", "governed_monitoring_lifecycle", build_governed_monitoring_lifecycle),
        ("fix_230", "governed_rollback_lifecycle", build_governed_rollback_lifecycle),
        ("fix_313", "launch_operations_center", build_launch_operations_center),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    return bundle
