# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — composed executive operating system dashboard evidence."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_store import (
    list_dashboard_review_records,
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


def collect_executive_operating_system_dashboard_evidence(*, session_id: str = "default") -> dict[str, Any]:
    sid = (session_id or "default").strip()[:64] or "default"
    bundle: dict[str, Any] = {"session_id": sid, "sources_ok": {}}

    from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
        build_billing_entitlements_foundation,
    )
    from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_service import (
        build_customer_feedback_intelligence,
    )
    from aethos_core.mission_control.customer_journey_intelligence.customer_journey_intelligence_service import (
        build_customer_journey_intelligence,
    )
    from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
        build_customer_support_success_foundation,
    )
    from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_service import (
        build_customer_value_realization_intelligence,
    )
    from aethos_core.mission_control.enterprise_operating_review_intelligence.enterprise_operating_review_intelligence_service import (
        build_enterprise_operating_review_intelligence,
    )
    from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service import (
        build_enterprise_program_intelligence,
    )
    from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_service import (
        build_executive_decision_intelligence,
    )
    from aethos_core.mission_control.governed_deploy_lifecycle.governed_deploy_lifecycle_service import (
        build_governed_deploy_lifecycle,
    )
    from aethos_core.mission_control.governed_merge_lifecycle.governed_merge_lifecycle_service import (
        build_governed_merge_lifecycle,
    )
    from aethos_core.mission_control.governed_monitoring_lifecycle.governed_monitoring_lifecycle_service import (
        build_governed_monitoring_lifecycle,
    )
    from aethos_core.mission_control.governed_rollback_lifecycle.governed_rollback_lifecycle_service import (
        build_governed_rollback_lifecycle,
    )
    from aethos_core.mission_control.growth_adoption_intelligence.growth_adoption_intelligence_service import (
        build_growth_adoption_intelligence,
    )
    from aethos_core.mission_control.launch_decision_package.launch_decision_package_service import (
        build_launch_decision_package,
    )
    from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
        build_launch_operations_center,
    )
    from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
        build_limited_beta_launch_program,
    )
    from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
        build_multi_repository_engineering_intelligence,
    )
    from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_service import (
        build_organizational_effectiveness_intelligence,
    )
    from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
        build_payment_integration_readiness,
    )
    from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_service import (
        build_post_launch_operations_baseline,
    )
    from aethos_core.mission_control.product_analytics_foundation.product_analytics_foundation_service import (
        build_product_analytics_foundation,
    )
    from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_service import (
        build_product_market_fit_intelligence,
    )
    from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_service import (
        build_public_launch_readiness_freeze,
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
        ("fix_200", "governed_merge_lifecycle", build_governed_merge_lifecycle),
        ("fix_210", "governed_deploy_lifecycle", build_governed_deploy_lifecycle),
        ("fix_220", "governed_monitoring_lifecycle", build_governed_monitoring_lifecycle),
        ("fix_230", "governed_rollback_lifecycle", build_governed_rollback_lifecycle),
        ("fix_260", "multi_repository_engineering_intelligence", build_multi_repository_engineering_intelligence),
        ("fix_305", "billing_entitlements_foundation", build_billing_entitlements_foundation),
        ("fix_308", "payment_integration_readiness", build_payment_integration_readiness),
        ("fix_309", "saas_launch_readiness_assessment", build_saas_launch_readiness_assessment),
        ("fix_310", "customer_support_success_foundation", build_customer_support_success_foundation),
        ("fix_312", "limited_beta_launch_program", build_limited_beta_launch_program),
        ("fix_313", "launch_operations_center", build_launch_operations_center),
        ("fix_314", "public_launch_readiness_freeze", build_public_launch_readiness_freeze),
        ("fix_315", "launch_decision_package", build_launch_decision_package),
        ("fix_316", "post_launch_operations_baseline", build_post_launch_operations_baseline),
        ("fix_318", "product_analytics_foundation", build_product_analytics_foundation),
        ("fix_319", "customer_feedback_intelligence", build_customer_feedback_intelligence),
        ("fix_320", "growth_adoption_intelligence", build_growth_adoption_intelligence),
        ("fix_321", "customer_journey_intelligence", build_customer_journey_intelligence),
        ("fix_322", "product_market_fit_intelligence", build_product_market_fit_intelligence),
        ("fix_323", "customer_value_realization_intelligence", build_customer_value_realization_intelligence),
        ("fix_324", "strategic_portfolio_intelligence", build_strategic_portfolio_intelligence),
        ("fix_325", "executive_decision_intelligence", build_executive_decision_intelligence),
        ("fix_326", "strategic_planning_intelligence", build_strategic_planning_intelligence),
        ("fix_327", "enterprise_program_intelligence", build_enterprise_program_intelligence),
        ("fix_328", "organizational_effectiveness_intelligence", build_organizational_effectiveness_intelligence),
        ("fix_329", "enterprise_operating_review_intelligence", build_enterprise_operating_review_intelligence),
    )

    for key, attr, builder in builders:
        result, ok = _safe_build(key.upper(), builder, session_id=sid)
        bundle[key] = _payload(result, attr)
        bundle["sources_ok"][key] = ok

    bundle["dashboard_review_records"] = [
        r for r in list_dashboard_review_records() if not sid or str(r.get("session_id") or sid) == sid
    ]

    return bundle
