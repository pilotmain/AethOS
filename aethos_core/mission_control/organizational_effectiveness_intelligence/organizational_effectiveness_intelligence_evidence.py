# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — composed organizational effectiveness evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_store import (
    list_organizational_review_records,
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


def collect_organizational_effectiveness_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
        build_customer_usage_audit_portal,
    )
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service import (
        build_enterprise_program_intelligence,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
        build_executive_decision_intelligence,
    )
    from aethos_core.mission_control.identity_access_hardening.identity_access_hardening_service import (
        build_identity_access_hardening,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
        build_launch_operations_center,
    )
    from aethos_core.mission_control.multi_tenant_platform_foundation.multi_tenant_platform_foundation_service import (
        build_multi_tenant_platform_foundation,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
        build_saas_launch_readiness_assessment,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_300", "multi_tenant_platform_foundation", build_multi_tenant_platform_foundation),
        ("fix_302", "identity_access_hardening", build_identity_access_hardening),
        ("fix_307", "customer_usage_audit_portal", build_customer_usage_audit_portal),
        ("fix_309", "saas_launch_readiness_assessment", build_saas_launch_readiness_assessment),
        ("fix_313", "launch_operations_center", build_launch_operations_center),
        ("fix_325", "executive_decision_intelligence", build_executive_decision_intelligence),
        ("fix_327", "enterprise_program_intelligence", build_enterprise_program_intelligence),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["organizational_review_records"] = [
        r for r in list_organizational_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
