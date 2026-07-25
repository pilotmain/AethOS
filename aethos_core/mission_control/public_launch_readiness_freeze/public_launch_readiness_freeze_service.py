# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_314_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_service import (
    build_atlas_trader_trust_report_freeze,
)
from aethos_core.mission_control.autonomous_capability_registry.autonomous_capability_registry_service import (
    build_autonomous_capability_registry,
)
from aethos_core.mission_control.capability_registry_runtime_integration.capability_registry_runtime_integration_service import (
    build_capability_registry_runtime_integration,
)
from aethos_core.mission_control.customer_support_success_foundation.customer_support_success_foundation_service import (
    build_customer_support_success_foundation,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_service import (
    build_dogfood_pilot_trust_report_freeze,
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
from aethos_core.mission_control.launch_operations_center.launch_operations_center_service import (
    build_launch_operations_center,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_service import (
    build_limited_beta_launch_program,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_service import (
    build_nexora_trust_report_freeze,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_service import (
    build_pilotos_ui_trust_report_freeze,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_contract import (
    AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
    AUTOMATIC_LAUNCH_ENABLED_FIX_314,
    EXECUTION_PERFORMED_FIX_314,
    FORBIDDEN_LAUNCH_FREEZE_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_314,
    HUMAN_LAUNCH_FREEZE_DECISION_KINDS,
    LAUNCH_DECISION_AUTHORITY_FIX_314,
    LAUNCH_FREEZE_AUTHORITY_FIX_314,
    LAUNCH_READINESS_FREEZE_COMPOSES_EVIDENCE_ONLY_FIX_314,
    LAUNCH_READINESS_FREEZE_DOMAINS,
    MUTATION_PERFORMED_FIX_314,
    PILOT_REEXECUTION_PERFORMED_FIX_314,
    PUBLIC_LAUNCH_READINESS_FREEZE_FIX,
    PUBLIC_LAUNCH_READINESS_FREEZE_INVARIANT,
    PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION,
    TRUST_MUTATION_AUTHORITY_FIX_314,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_evaluator import (
    build_evidence_timeline,
    derive_launch_recommendation_freeze,
    summarize_trust_baselines,
)
from aethos_core.mission_control.public_launch_readiness_freeze.public_launch_readiness_freeze_store import (
    has_launch_freeze_review_decision_approve,
    list_public_launch_readiness_freeze_records,
)
from aethos_core.mission_control.public_product_experience.public_product_experience_service import (
    build_public_product_experience,
)
from aethos_core.mission_control.saas_launch_readiness_assessment.saas_launch_readiness_assessment_service import (
    build_saas_launch_readiness_assessment,
)


@dataclass(frozen=True)
class PublicLaunchReadinessFreezeResult:
    ok: bool
    session_id: str
    public_launch_readiness_freeze: dict[str, Any] = field(default_factory=dict)
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


def build_public_launch_readiness_freeze(*, session_id: str) -> PublicLaunchReadinessFreezeResult:
    sid = (session_id or "default").strip()[:64] or "default"
    records = list_public_launch_readiness_freeze_records()
    frozen_at = _exported_at()

    trust_186, trust_186_ok = _safe_build("fix_186", build_dogfood_pilot_trust_report_freeze, session_id=sid)
    trust_192, trust_192_ok = _safe_build("fix_192", build_pilotos_ui_trust_report_freeze, session_id=sid)
    trust_194, trust_194_ok = _safe_build("fix_194", build_atlas_trader_trust_report_freeze, session_id=sid)
    trust_196, trust_196_ok = _safe_build("fix_196", build_nexora_trust_report_freeze, session_id=sid)
    launch, launch_ok = _safe_build("fix_309", build_saas_launch_readiness_assessment, session_id=sid)
    support, support_ok = _safe_build("fix_310", build_customer_support_success_foundation, session_id=sid)
    public, public_ok = _safe_build("fix_311", build_public_product_experience, session_id=sid)
    beta, beta_ok = _safe_build("fix_312", build_limited_beta_launch_program, session_id=sid)
    ops, ops_ok = _safe_build("fix_313", build_launch_operations_center, session_id=sid)
    capability, capability_ok = _safe_build("fix_295", build_autonomous_capability_registry, session_id=sid)
    runtime, runtime_ok = _safe_build("fix_296", build_capability_registry_runtime_integration, session_id=sid)
    merge, merge_ok = _safe_build("fix_200", build_governed_merge_lifecycle, session_id=sid)
    deploy, deploy_ok = _safe_build("fix_210", build_governed_deploy_lifecycle, session_id=sid)
    monitoring, monitoring_ok = _safe_build("fix_220", build_governed_monitoring_lifecycle, session_id=sid)
    rollback, rollback_ok = _safe_build("fix_230", build_governed_rollback_lifecycle, session_id=sid)

    launch_board = _payload(launch, "saas_launch_readiness_assessment")
    overall_launch_status = str(launch_board.get("overall_launch_status") or "UNKNOWN")
    launch_blockers = list(launch_board.get("blockers") or [])

    ops_board = _payload(ops, "launch_operations_center")
    ops_recommendation = str(ops_board.get("launch_recommendation") or "BLOCK_LAUNCH")
    ops_blockers = list(ops_board.get("blockers") or [])
    ops_risk_dashboard = (ops_board.get("sections") or {}).get("launch_risk_dashboard", [{}])[0]
    ops_risks = [
        row
        for bucket in ("product", "operational", "governance", "customer")
        for row in (ops_risk_dashboard.get(bucket) or [])
    ]

    beta_board = _payload(beta, "limited_beta_launch_program")
    beta_recommendation = str(beta_board.get("beta_launch_recommendation") or "DO_NOT_LAUNCH")

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
    trust_baseline_count = sum(1 for row in trust_rows if row.get("available"))

    capability_board = _payload(capability, "autonomous_capability_registry")
    capability_registry = (capability_board.get("sections") or {}).get("capability_registry", [{}])[0]
    capabilities = list(capability_registry.get("capabilities") or [])
    proven_caps = [c for c in capabilities if str(c.get("status") or "").upper() in {"PROVEN", "OPERATIONAL"}]
    unproven_caps = [c for c in capabilities if c not in proven_caps]

    platform_healthy = all((merge_ok, deploy_ok, monitoring_ok, rollback_ok))
    product_ready = public_ok and launch_ok
    all_blockers = sorted(set(launch_blockers + ops_blockers))
    critical_risk_count = sum(1 for row in ops_risks if row.get("level") == "critical")

    recommendation = derive_launch_recommendation_freeze(
        overall_launch_status=overall_launch_status,
        launch_recommendation=ops_recommendation,
        beta_recommendation=beta_recommendation,
        blocker_count=len(all_blockers),
        critical_risk_count=critical_risk_count,
        trust_baseline_count=trust_baseline_count,
        platform_healthy=platform_healthy,
        product_ready=product_ready,
    )

    timeline_events = build_evidence_timeline(
        trust_rows=trust_rows,
        launch_status=overall_launch_status,
        beta_recommendation=beta_recommendation,
        ops_recommendation=ops_recommendation,
    )

    proven_items = [
        f"{row['product']} trust freeze composed ({row['fix']})"
        for row in trust_rows
        if row.get("available")
    ] + [
        f"{len(proven_caps)} capabilities proven in FIX 295 registry",
        "Launch readiness assessment composed (FIX 309)",
        "Beta launch program composed (FIX 312)",
        "Launch operations center composed (FIX 313)",
    ]
    unproven_items = [
        f"{len(unproven_caps)} capabilities not yet proven",
        "Payment processing remains readiness-only",
        "Human launch freeze review required before launch decision",
    ]
    if not platform_healthy:
        unproven_items.append("Platform lifecycle evidence incomplete")

    launch_evidence_timeline = [
        {
            "timeline_id": "launch-evidence-timeline",
            "events": timeline_events,
            "event_count": len(timeline_events),
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_trust_baseline_summary = [
        {
            "summary_id": "launch-trust-baseline-summary",
            "baselines": trust_rows,
            "baseline_count": trust_baseline_count,
            "trust_freezes": [row for row in trust_rows if row.get("available")],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_capability_baseline = [
        {
            "baseline_id": "launch-capability-baseline",
            "capability_count": len(capabilities),
            "proven_count": len(proven_caps),
            "unproven_count": len(unproven_caps),
            "proven_capabilities": proven_caps[:12],
            "runtime_integration_ready": runtime_ok,
            "evidence_sources": ["FIX 295", "FIX 296"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_operational_baseline = [
        {
            "baseline_id": "launch-operational-baseline",
            "delivery_health": merge_ok,
            "deploy_health": deploy_ok,
            "monitoring_health": monitoring_ok,
            "recovery_health": rollback_ok,
            "platform_healthy": platform_healthy,
            "evidence_sources": ["FIX 200", "FIX 210", "FIX 220", "FIX 230"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_product_baseline = [
        {
            "baseline_id": "launch-product-baseline",
            "multi_tenant_ready": launch_ok,
            "public_experience_ready": public_ok,
            "overall_launch_status": overall_launch_status,
            "evidence_sources": ["FIX 300-311"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    support_board = _payload(support, "customer_support_success_foundation")
    support_dashboard = (support_board.get("sections") or {}).get(
        "customer_support_success_dashboard", [{}]
    )[0]
    beta_ops = (beta_board.get("sections") or {}).get("beta_operations_dashboard", [{}])[0]

    launch_customer_baseline = [
        {
            "baseline_id": "launch-customer-baseline",
            "healthy_count": support_dashboard.get("healthy_count", 0),
            "at_risk_count": support_dashboard.get("at_risk_count", 0),
            "beta_participants": beta_ops.get("active_participant_count", 0),
            "customer_support_ready": support_ok,
            "beta_program_ready": beta_ok,
            "evidence_sources": ["FIX 310", "FIX 312"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_risk_freeze = [
        {
            "freeze_id": "launch-risk-freeze",
            "risks": ops_risks,
            "risk_count": len(ops_risks),
            "critical_risk_count": critical_risk_count,
            "evidence_sources": ["FIX 309", "FIX 313"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    frozen_blockers = [
        {
            "blocker_id": f"blocker-{idx}",
            "detail": detail,
            "source": "FIX 309" if detail in launch_blockers else "FIX 313",
            "read_only": True,
        }
        for idx, detail in enumerate(all_blockers)
    ]
    launch_blocker_freeze = [
        {
            "freeze_id": "launch-blocker-freeze",
            "blockers": frozen_blockers,
            "blocker_count": len(frozen_blockers),
            "evidence_sources": ["FIX 309", "FIX 313"],
            "frozen_at": frozen_at,
            "read_only": True,
        }
    ]

    launch_recommendation_freeze = [
        {
            "freeze_id": "launch-recommendation-freeze",
            "recommendation": recommendation,
            "rationale": (
                "Frozen from FIX 309 readiness, FIX 313 operations, FIX 312 beta, "
                "and trust baselines — not launch execution."
            ),
            "overall_launch_status": overall_launch_status,
            "operations_recommendation": ops_recommendation,
            "beta_recommendation": beta_recommendation,
            "launch_execution_performed": False,
            "read_only": True,
        }
    ]

    launch_readiness_freeze_dashboard = [
        {
            "dashboard_id": "launch-readiness-freeze-dashboard",
            "launch_recommendation_freeze": recommendation,
            "overall_launch_status": overall_launch_status,
            "blocker_count": len(frozen_blockers),
            "risk_count": len(ops_risks),
            "trust_baseline_count": trust_baseline_count,
            "proven_capability_count": len(proven_caps),
            "unproven_capability_count": len(unproven_caps),
            "platform_healthy": platform_healthy,
            "proven_items": proven_items,
            "unproven_items": unproven_items,
            "frozen_at": frozen_at,
            "launch_decision_performed": False,
            "read_only": True,
        }
    ]

    sections = {
        "launch_evidence_timeline": launch_evidence_timeline,
        "launch_trust_baseline_summary": launch_trust_baseline_summary,
        "launch_capability_baseline": launch_capability_baseline,
        "launch_operational_baseline": launch_operational_baseline,
        "launch_product_baseline": launch_product_baseline,
        "launch_customer_baseline": launch_customer_baseline,
        "launch_risk_freeze": launch_risk_freeze,
        "launch_blocker_freeze": launch_blocker_freeze,
        "launch_recommendation_freeze": launch_recommendation_freeze,
        "launch_readiness_freeze_dashboard": launch_readiness_freeze_dashboard,
        "human_launch_freeze_review": [
            {
                "review_id": "human-launch-freeze-review",
                "decisions_supported": list(HUMAN_LAUNCH_FREEZE_DECISION_KINDS),
                "launch_freeze_review_decision_approve": has_launch_freeze_review_decision_approve(
                    session_id=sid
                ),
                "launch_freeze_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_launch_freeze_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_LAUNCH_FREEZE_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": PUBLIC_LAUNCH_READINESS_FREEZE_SCHEMA_VERSION,
        "fix": PUBLIC_LAUNCH_READINESS_FREEZE_FIX,
        "exported_at": frozen_at,
        "frozen_at": frozen_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_314,
        "execution_performed": EXECUTION_PERFORMED_FIX_314,
        "pilot_reexecution_performed": PILOT_REEXECUTION_PERFORMED_FIX_314,
        "launch_readiness_freeze_compose_artifacts_only": LAUNCH_READINESS_FREEZE_COMPOSES_EVIDENCE_ONLY_FIX_314,
        "launch_freeze_authority": LAUNCH_FREEZE_AUTHORITY_FIX_314,
        "automatic_launch_enabled": AUTOMATIC_LAUNCH_ENABLED_FIX_314,
        "automatic_beta_expansion_enabled": AUTOMATIC_BETA_EXPANSION_ENABLED_FIX_314,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_314,
        "launch_decision_authority": LAUNCH_DECISION_AUTHORITY_FIX_314,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_314,
        "invariant": PUBLIC_LAUNCH_READINESS_FREEZE_INVARIANT,
        "session_id": sid,
        "launch_readiness_freeze_domains": list(LAUNCH_READINESS_FREEZE_DOMAINS),
        "launch_recommendation_freeze": recommendation,
        "sections": sections,
        "operator_record_count": len(records),
        "launch_freeze_review_decision_approve": has_launch_freeze_review_decision_approve(session_id=sid),
        "fix_314_certification_requirements": list(FIX_314_CERTIFICATION_REQUIREMENTS),
        "sources": {
            "composes_fix_186_through_313": True,
            "pilot_reexecution_performed": False,
            "launch_execution_performed": False,
            "trust_mutation_performed": False,
            "readiness_promotion_performed": False,
            "customer_provisioning_performed": False,
        },
    }

    return PublicLaunchReadinessFreezeResult(
        ok=True,
        session_id=sid,
        public_launch_readiness_freeze=payload,
        blockers=all_blockers,
        detail="Public launch readiness freeze composed from evidence (freeze ≠ launch authority).",
    )
