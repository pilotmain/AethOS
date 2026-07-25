# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy router."""

from __future__ import annotations

from aethos_core.providers.railway.execution_contract.execution_context import (
    resolve_execution_id_for_plan,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy import (
    assess_canary_shadow_deployment_policy,
    get_or_create_policy_record,
    is_production_canary_shadow_policy_intent,
    record_synthetic_verification_traffic,
)
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_renderer import (
    render_canary_health_evidence,
    render_canary_rollback_recommendation,
    render_deployment_strategy_policy,
    render_rollout_percentage_governance,
    render_shadow_traffic_policy,
    render_traffic_segmentation,
)
from aethos_core.providers.railway.execution_contract.production_policy_operator_views import (
    is_readonly_canary_shadow_policy_query,
    render_unenrolled_policy_view,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": "railway_production_canary_shadow_policy",
        "matched_module": "providers.railway.execution_contract.production_canary_shadow_policy_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "canary_shadow_policy_stage": stage,
        **extra,
    }


def route_railway_production_canary_shadow_policy(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_production_canary_shadow_policy_intent(raw):
        return None

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_session_hydration import (
        ensure_railway_deployment_lifecycle_for_lane,
    )

    readonly = is_readonly_canary_shadow_policy_query(raw)
    lane = ensure_railway_deployment_lifecycle_for_lane(
        session_id=session_id,
        user_text=raw,
        require_plan=not readonly,
    )
    plan = lane.plan or {}
    execution_id = resolve_execution_id_for_plan(session_id=session_id, plan=plan) if plan else ""

    if not execution_id:
        if not readonly:
            body = render_unenrolled_policy_view("canary_shadow_policy")
            body += (
                "\n\n**Action blocked:** recording synthetic verification traffic "
                "requires a enrolled production execution."
            )
            return body, "railway_production_canary_shadow_policy_blocked", _meta(
                session_id,
                stage="blocked",
                enrollment="missing",
            )
        if "shadow traffic" in raw.lower():
            body = render_unenrolled_policy_view("shadow_traffic")
            return body, "railway_production_shadow_traffic_policy", _meta(
                session_id, stage="shadow_traffic", enrollment="missing"
            )
        if "canary health" in raw.lower():
            body = render_unenrolled_policy_view("canary_health")
            return body, "railway_production_canary_health_evidence", _meta(
                session_id, stage="canary_health", enrollment="missing"
            )
        if "percentage" in raw.lower():
            body = render_unenrolled_policy_view("percentage_governance")
            return body, "railway_production_rollout_percentage_governance", _meta(
                session_id, stage="percentage_governance", enrollment="missing"
            )
        if "rollback recommendation" in raw.lower():
            body = render_unenrolled_policy_view("rollback_recommendation")
            return body, "railway_production_canary_rollback_recommendation", _meta(
                session_id, stage="rollback_recommendation", enrollment="missing"
            )
        if "traffic segmentation" in raw.lower():
            body = render_unenrolled_policy_view("traffic_segmentation")
            return body, "railway_production_traffic_segmentation", _meta(
                session_id, stage="traffic_segmentation", enrollment="missing"
            )
        body = render_unenrolled_policy_view("canary_shadow_policy")
        return body, "railway_production_canary_shadow_policy", _meta(
            session_id, stage="policy", enrollment="missing"
        )

    if "synthetic" in raw.lower() and "verification" in raw.lower() and "record" in raw.lower():
        record = record_synthetic_verification_traffic(
            execution_id=execution_id,
            user_text=raw,
            session_id=session_id,
        )
        assessment = assess_canary_shadow_deployment_policy(
            execution_id=execution_id,
            plan=plan,
            session_id=session_id,
        )
        body = render_deployment_strategy_policy(assessment)
        body += f"\n\nSynthetic runs recorded: **{len(record.get('synthetic_verification_runs') or [])}**"
        return body, "railway_production_synthetic_verification_traffic", _meta(
            session_id,
            stage="synthetic_verification",
            execution_id=execution_id,
        )

    assessment = assess_canary_shadow_deployment_policy(
        execution_id=execution_id,
        plan=plan,
        session_id=session_id,
    )

    if "shadow traffic" in raw.lower():
        body = render_shadow_traffic_policy(assessment)
        return body, "railway_production_shadow_traffic_policy", _meta(session_id, stage="shadow_traffic")

    if "canary health" in raw.lower():
        body = render_canary_health_evidence(assessment)
        return body, "railway_production_canary_health_evidence", _meta(session_id, stage="canary_health")

    if "percentage" in raw.lower():
        body = render_rollout_percentage_governance(assessment)
        return body, "railway_production_rollout_percentage_governance", _meta(
            session_id, stage="percentage_governance"
        )

    if "rollback recommendation" in raw.lower():
        body = render_canary_rollback_recommendation(assessment)
        return body, "railway_production_canary_rollback_recommendation", _meta(
            session_id, stage="rollback_recommendation"
        )

    if "traffic segmentation" in raw.lower():
        record = get_or_create_policy_record(
            execution_id=execution_id,
            session_id=session_id,
            plan=plan,
        )
        body = render_traffic_segmentation(record)
        return body, "railway_production_traffic_segmentation", _meta(session_id, stage="traffic_segmentation")

    body = render_deployment_strategy_policy(assessment)
    return body, "railway_production_canary_shadow_policy", _meta(
        session_id,
        stage="policy",
        deployment_strategy=assessment.deployment_strategy,
    )
