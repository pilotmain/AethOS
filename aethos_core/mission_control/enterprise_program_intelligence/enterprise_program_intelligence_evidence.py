# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — composed enterprise program evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_store import (
    list_program_review_records,
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


def collect_enterprise_program_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.autonomous_business_operating_system.autonomous_business_operating_system_service import (
        build_autonomous_business_operating_system,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
        build_executive_decision_intelligence,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
        build_launch_operations_center,
    )
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
        build_post_launch_operations_baseline,
    )
    from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
        build_saas_launch_readiness_assessment,
    )
    from aethos_core.mission_control.strategic_planning_intelligence.strategic_planning_intelligence_service import (
        build_strategic_planning_intelligence,
    )
    from aethos_core.mission_control.strategic_portfolio_intelligence.strategic_portfolio_intelligence_service import (
        build_strategic_portfolio_intelligence,
    )

    builders: tuple[tuple[str, str, Any], ...] = (
        ("fix_290", "autonomous_business_operating_system", build_autonomous_business_operating_system),
        ("fix_309", "saas_launch_readiness_assessment", build_saas_launch_readiness_assessment),
        ("fix_313", "launch_operations_center", build_launch_operations_center),
        ("fix_316", "post_launch_operations_baseline", build_post_launch_operations_baseline),
        ("fix_324", "strategic_portfolio_intelligence", build_strategic_portfolio_intelligence),
        ("fix_325", "executive_decision_intelligence", build_executive_decision_intelligence),
        ("fix_326", "strategic_planning_intelligence", build_strategic_planning_intelligence),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["program_review_records"] = [
        r for r in list_program_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
