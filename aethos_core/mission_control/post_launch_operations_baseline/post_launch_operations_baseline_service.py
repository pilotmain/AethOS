# SPDX-License-Identifier: Apache-2.0
"""FIX 316 — post-launch operations baseline service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_316_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
    build_atlas_trader_trust_report_freeze,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
    build_autonomous_product_stewardship,
)
from aethos_core.mission_control.billing_entitlements_foundation.billing_entitlements_foundation_service import (
    build_billing_entitlements_foundation,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.customer_usage_audit_portal.customer_usage_audit_portal_service import (
    build_customer_usage_audit_portal,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
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
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)
from aethos_core.mission_control.payment_integration_readiness.payment_integration_readiness_service import (
    build_payment_integration_readiness,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_contract import (
    AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
    AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
    EXECUTION_PERFORMED_FIX_316,
    FORBIDDEN_POST_LAUNCH_OPERATIONS_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_316,
    HUMAN_OPERATIONS_BASELINE_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_316,
    PILOT_EXECUTION_PERFORMED_FIX_316,
    POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
    POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS,
    POST_LAUNCH_OPERATIONS_BASELINE_FIX,
    POST_LAUNCH_OPERATIONS_BASELINE_INVARIANT,
    POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION,
    POST_LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_316,
    TRUST_MUTATION_AUTHORITY_FIX_316,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_evaluator import (
    assess_customer_health,
    assess_platform_health,
    categorize_capabilities_for_baseline,
    summarize_trust_progression,
)
from aethos_core.mission_control.post_launch_operations_baseline.post_launch_operations_baseline_store import (
    has_operations_baseline_review_decision_approve,
    list_post_launch_operations_baseline_records,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_evaluator import (
    summarize_trust_baselines,
)


@dataclass(frozen=True)
class PostLaunchOperationsBaselineResult:
    ok: bool
    session_id: str
    post_launch_operations_baseline: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _safe_build(name: str, builder, *, session_id: str) -> tuple[Any, bool]:
    try:
        result = builder(session_id=session_id)
        return result, bool(getattr(result, "ok", True))
    except Exception:
        return None, False


def _payload(result: Any, attr: str) -> dict[str, Any]:
    if not result:
        return {}
    value = getattr(result, attr, None)
    return value if isinstance(value, dict) else {}


def _section(board: dict[str, Any], key: str) -> dict[str, Any]:
    sections = board.get("sections") or {}
    rows = sections.get(key) or [{}]
    return rows[0] if rows else {}


def build_post_launch_operations_baseline(*, session_id: str) -> PostLaunchOperationsBaselineResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_post_launch_operations_baseline_records()
    baselined_at = _exported_at()

    monitoring, monitoring_ok = _safe_build("fix_220", build_governed_monitoring_lifecycle, session_id=sid)
    rollback, rollback_ok = _safe_build("fix_230", build_governed_rollback_lifecycle, session_id=sid)
    ops, ops_ok = _safe_build("fix_313", build_launch_operations_center, session_id=sid)
    support, support_ok = _safe_build("fix_310", build_customer_support_success_foundation, session_id=sid)
    beta, beta_ok = _safe_build("fix_312", build_limited_beta_launch_program, session_id=sid)
    identity, identity_ok = _safe_build("fix_302", build_identity_access_hardening, session_id=sid)
    audit, audit_ok = _safe_build("fix_307", build_customer_usage_audit_portal, session_id=sid)
    trust_186, trust_186_ok = _safe_build("fix_186", build_dogfood_pilot_trust_report_freeze, session_id=sid)
    trust_192, trust_192_ok = _safe_build("fix_192", build_pilotos_ui_trust_report_freeze, session_id=sid)
    trust_194, trust_194_ok = _safe_build("fix_194", build_atlas_trader_trust_report_freeze, session_id=sid)
    trust_196, trust_196_ok = _safe_build("fix_196", build_nexora_trust_report_freeze, session_id=sid)
    capability, capability_ok = _safe_build("fix_295", build_autonomous_capability_registry, session_id=sid)
    runtime, runtime_ok = _safe_build("fix_296", build_capability_registry_runtime_integration, session_id=sid)
    billing, billing_ok = _safe_build("fix_305", build_billing_entitlements_foundation, session_id=sid)
    payment, payment_ok = _safe_build("fix_308", build_payment_integration_readiness, session_id=sid)
    portfolio_260, portfolio_260_ok = _safe_build(
        "fix_260", build_multi_repository_engineering_intelligence, session_id=sid
    )
    portfolio_261, portfolio_261_ok = _safe_build(
        "fix_261", build_cross_repository_product_evolution_intelligence, session_id=sid
    )
    portfolio_270, portfolio_270_ok = _safe_build(
        "fix_270", build_autonomous_product_stewardship, session_id=sid
    )

    monitoring_board = _payload(monitoring, "governed_monitoring_lifecycle")
    monitoring_health = _section(monitoring_board, "monitoring_health_assessment")
    incident_detection = _section(monitoring_board, "incident_detection")
    monitoring_classification = str(
        monitoring_board.get("incident_classification")
        or incident_detection.get("classification")
        or "UNKNOWN"
    )
    escalation_rows = monitoring_board.get("sections", {}).get("incident_escalation_artifact") or []

    ops_board = _payload(ops, "launch_operations_center")
    platform_ops = _section(ops_board, "platform_operations_monitor")
    ops_risk_dashboard = _section(ops_board, "launch_risk_dashboard")
    operational_risks = sum(len(ops_risk_dashboard.get(bucket) or []) for bucket in ("operational", "governance"))

    rollback_board = _payload(rollback, "governed_rollback_lifecycle")
    rollback_recommendation = _section(rollback_board, "rollback_recommendation")

    support_board = _payload(support, "customer_support_success_foundation")
    support_dashboard = _section(support_board, "customer_support_success_dashboard")
    healthy_count = int(support_dashboard.get("healthy_count") or 0)
    at_risk_count = int(support_dashboard.get("at_risk_count") or 0)

    beta_board = _payload(beta, "limited_beta_launch_program")
    beta_ops = _section(beta_board, "beta_operations_dashboard")
    beta_participants = int(beta_ops.get("active_participant_count") or 0)

    identity_board = _payload(identity, "identity_access_hardening")
    authorization_matrix = _section(identity_board, "authorization_matrix")
    identity_reviews = identity_board.get("sections", {}).get("human_authorization_review") or []

    audit_board = _payload(audit, "customer_usage_audit_portal")
    audit_dashboard = _section(audit_board, "usage_audit_dashboard")
    audit_events = audit_board.get("sections", {}).get("audit_event_registry") or []

    trust_rows = summarize_trust_baselines(
        fix_186=_payload(trust_186, "dogfood_pilot_trust_report_freeze"),
        fix_192=_payload(trust_192, "pilotos_ui_trust_report_freeze"),
        fix_194=_payload(trust_194, "atlas_trader_trust_report_freeze"),
        fix_196=_payload(trust_196, "nexora_trust_report_freeze"),
        fix_186_ok=trust_186_ok,
        fix_192_ok=trust_192_ok,
        fix_194_ok=trust_194_ok,
        fix_196_ok=trust_196_ok,
    )
    trust_summary = summarize_trust_progression(trust_rows=trust_rows)

    capability_board = _payload(capability, "autonomous_capability_registry")
    capability_registry = _section(capability_board, "capability_registry")
    capabilities = list(capability_registry.get("capabilities") or [])
    cap_categories = categorize_capabilities_for_baseline(capabilities)

    billing_board = _payload(billing, "billing_entitlements_foundation")
    billing_plans = _section(billing_board, "plan_registry")
    billing_usage = _section(billing_board, "usage_registry")
    plans = list(billing_plans.get("plans") or [])

    payment_board = _payload(payment, "payment_integration_readiness")
    payment_readiness = _section(payment_board, "payment_readiness_assessment")

    portfolio_260_board = _payload(portfolio_260, "multi_repository_engineering_intelligence")
    portfolio_261_board = _payload(portfolio_261, "cross_repository_product_evolution_intelligence")
    portfolio_270_board = _payload(portfolio_270, "autonomous_product_stewardship")

    platform_healthy = bool(platform_ops.get("platform_healthy", ops_ok and monitoring_ok))
    deployment_health = monitoring_ok and monitoring_classification not in {"INCIDENT", "DEGRADED"}
    monitoring_health_ok = monitoring_ok and monitoring_classification == "HEALTHY"
    platform_health_status = assess_platform_health(
        monitoring_ok=monitoring_ok,
        monitoring_classification=monitoring_classification,
        platform_healthy=platform_healthy,
        deployment_health=deployment_health,
    )
    customer_health_status = assess_customer_health(
        healthy_count=healthy_count,
        at_risk_count=at_risk_count,
        beta_participants=beta_participants,
        support_ready=support_ok,
    )

    incident_count = 1 if monitoring_classification == "INCIDENT" else 0
    if monitoring_classification == "DEGRADED":
        incident_count = max(incident_count, 1)
    escalation_frequency = len(escalation_rows)
    recovery_trend = str(rollback_recommendation.get("recommendation") or "stable")

    governance_health_status = "HEALTHY" if identity_ok and audit_ok else "ATTENTION"
    if not identity_ok or not audit_ok:
        governance_health_status = "UNKNOWN" if not identity_ok and not audit_ok else "ATTENTION"

    platform_health_baseline = [
        {
            "baseline_id": "platform-health-baseline",
            "deployment_health": deployment_health,
            "monitoring_health": monitoring_health_ok,
            "operational_stability": platform_healthy and operational_risks == 0,
            "health_status": platform_health_status,
            "monitoring_classification": monitoring_classification,
            "evidence_sources": ["FIX 220", "FIX 313"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    customer_health_baseline = [
        {
            "baseline_id": "customer-health-baseline",
            "healthy_count": healthy_count,
            "at_risk_count": at_risk_count,
            "beta_participants": beta_participants,
            "activation_rate": beta_ops.get("activation_rate"),
            "customer_health_score": beta_ops.get("customer_health_score"),
            "health_status": customer_health_status,
            "evidence_sources": ["FIX 310", "FIX 312"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    governance_health_baseline = [
        {
            "baseline_id": "governance-health-baseline",
            "authorization_effective": identity_ok and bool(authorization_matrix),
            "audit_integrity": audit_ok and bool(audit_events or audit_dashboard),
            "approval_count": len(identity_reviews),
            "review_count": len(audit_events),
            "health_status": governance_health_status,
            "evidence_sources": ["FIX 302", "FIX 307"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    incident_baseline = [
        {
            "baseline_id": "incident-baseline",
            "incident_count": incident_count,
            "escalation_frequency": escalation_frequency,
            "recovery_trend": recovery_trend,
            "monitoring_classification": monitoring_classification,
            "operational_risk_count": operational_risks,
            "evidence_sources": ["FIX 220", "FIX 230", "FIX 313"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    trust_baseline = [
        {
            "baseline_id": "trust-baseline",
            "trust_baselines": trust_rows,
            "baseline_count": trust_summary["trust_status_count"],
            "trust_progressions": trust_summary["trust_progressions"],
            "trust_regressions": trust_summary["trust_regressions"],
            "trust_stable": trust_summary["trust_stable"],
            "evidence_sources": ["FIX 186", "FIX 192", "FIX 194", "FIX 196"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    capability_baseline = [
        {
            "baseline_id": "capability-baseline",
            "proven": cap_categories["proven"][:12],
            "experimental": cap_categories["experimental"][:12],
            "blocked": cap_categories["blocked"][:12],
            "proven_count": len(cap_categories["proven"]),
            "experimental_count": len(cap_categories["experimental"]),
            "blocked_count": len(cap_categories["blocked"]),
            "runtime_integration_ready": runtime_ok,
            "evidence_sources": ["FIX 295", "FIX 296"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    commercial_baseline = [
        {
            "baseline_id": "commercial-baseline",
            "plans": plans[:8],
            "plan_count": len(plans),
            "usage_tracked": bool(billing_usage),
            "entitlement_utilization": billing_usage.get("utilization_summary"),
            "payment_readiness": payment_readiness.get("readiness_status"),
            "evidence_sources": ["FIX 305", "FIX 308"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    portfolio_baseline = [
        {
            "baseline_id": "portfolio-baseline",
            "product_health": portfolio_260_board.get("overall_health") or portfolio_260_ok,
            "evolution_opportunities": (
                portfolio_261_board.get("sections", {}).get("evolution_opportunity_registry") or []
            )[:6],
            "stewardship_trends": (
                portfolio_270_board.get("sections", {}).get("stewardship_trend_registry") or []
            )[:6],
            "evidence_sources": ["FIX 260", "FIX 261", "FIX 270"],
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    session_records = [row for row in records if not sid or str(row.get("session_id") or sid) == sid]
    operations_baseline_registry = [
        {
            "registry_id": "operations-baseline-registry",
            "records": session_records[-20:],
            "record_count": len(session_records),
            "baseline_snapshot": {
                "baselined_at": baselined_at,
                "platform_health_status": platform_health_status,
                "customer_health_status": customer_health_status,
                "governance_health_status": governance_health_status,
            },
            "decisions_supported": list(HUMAN_OPERATIONS_BASELINE_DECISION_KINDS),
            "operations_baseline_review_decision_approve": has_operations_baseline_review_decision_approve(
                session_id=sid
            ),
            "post_launch_operations_authority": False,
            "read_only": True,
        }
    ]

    post_launch_operations_dashboard = [
        {
            "dashboard_id": "post-launch-operations-dashboard",
            "platform_health_status": platform_health_status,
            "customer_health_status": customer_health_status,
            "governance_health_status": governance_health_status,
            "incident_count": incident_count,
            "trust_baseline_count": trust_summary["trust_status_count"],
            "proven_capability_count": len(cap_categories["proven"]),
            "experimental_capability_count": len(cap_categories["experimental"]),
            "blocked_capability_count": len(cap_categories["blocked"]),
            "commercial_plan_count": len(plans),
            "platform_healthy": platform_healthy,
            "operational_execution_performed": False,
            "baselined_at": baselined_at,
            "read_only": True,
        }
    ]

    sections = {
        "platform_health_baseline": platform_health_baseline,
        "customer_health_baseline": customer_health_baseline,
        "governance_health_baseline": governance_health_baseline,
        "incident_baseline": incident_baseline,
        "trust_baseline": trust_baseline,
        "capability_baseline": capability_baseline,
        "commercial_baseline": commercial_baseline,
        "portfolio_baseline": portfolio_baseline,
        "post_launch_operations_dashboard": post_launch_operations_dashboard,
        "operations_baseline_registry": operations_baseline_registry,
        "forbidden_post_launch_operations_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_POST_LAUNCH_OPERATIONS_ACTIONS
        ],
    }

    blockers: list[str] = []
    if platform_health_status == "DEGRADED":
        blockers.append("platform_health_degraded")
    if customer_health_status == "AT_RISK":
        blockers.append("customer_health_at_risk")
    if incident_count > 0:
        blockers.append("active_incident_signal")

    payload: dict[str, Any] = {
        "schema_version": POST_LAUNCH_OPERATIONS_BASELINE_SCHEMA_VERSION,
        "fix": POST_LAUNCH_OPERATIONS_BASELINE_FIX,
        "exported_at": baselined_at,
        "baselined_at": baselined_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_316,
        "execution_performed": EXECUTION_PERFORMED_FIX_316,
        "pilot_execution_performed": PILOT_EXECUTION_PERFORMED_FIX_316,
        "post_launch_operations_compose_artifacts_only": POST_LAUNCH_OPERATIONS_COMPOSES_EVIDENCE_ONLY_FIX_316,
        "post_launch_operations_authority": POST_LAUNCH_OPERATIONS_AUTHORITY_FIX_316,
        "automatic_operational_execution_enabled": AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_316,
        "automatic_customer_contact_enabled": AUTOMATIC_CUSTOMER_CONTACT_ENABLED_FIX_316,
        "automatic_incident_response_enabled": AUTOMATIC_INCIDENT_RESPONSE_ENABLED_FIX_316,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_316,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_316,
        "invariant": POST_LAUNCH_OPERATIONS_BASELINE_INVARIANT,
        "session_id": sid,
        "post_launch_operations_baseline_domains": list(POST_LAUNCH_OPERATIONS_BASELINE_DOMAINS),
        "sections": sections,
        "operator_record_count": len(records),
        "operations_baseline_review_decision_approve": has_operations_baseline_review_decision_approve(
            session_id=sid
        ),
        "fix_316_certification_requirements": list(FIX_316_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_186_through_315": True,
            "pilot_execution_performed": False,
            "operational_execution_performed": False,
            "incident_response_performed": False,
            "customer_outreach_performed": False,
            "deployment_actions_performed": False,
            "rollback_actions_performed": False,
            "trust_mutation_performed": False,
            "provider_mutation_performed": False,
        },
    }

    return PostLaunchOperationsBaselineResult(
        ok=True,
        session_id=sid,
        post_launch_operations_baseline=payload,
        blockers=blockers,
        detail="Post-launch operations baseline composed from evidence (baseline ≠ operational authority).",
    )
