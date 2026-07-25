# SPDX-License-Identifier: Apache-2.0
"""FIX 280 — autonomous application lifecycle management service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_280_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_contract import (
    AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
    AUTONOMOUS_APPLICATION_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_280,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_FIX,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_INVARIANT,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_PRINCIPLES,
    AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION,
    DEPLOYMENT_AUTHORITY_FIX_280,
    EXECUTION_PERFORMED_FIX_280,
    FORBIDDEN_LIFECYCLE_MANAGEMENT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_280,
    GOVERNANCE_MUTATION_PERFORMED_FIX_280,
    LIFECYCLE_HEALTH_DIMENSIONS,
    LIFECYCLE_RISK_DIMENSIONS,
    LIFECYCLE_STAGES,
    LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
    MERGE_AUTHORITY_FIX_280,
    MUTATION_PERFORMED_FIX_280,
    PROVIDER_MUTATION_AUTHORITY_FIX_280,
    REPOSITORY_MUTATION_AUTHORITY_FIX_280,
    ROLLBACK_AUTHORITY_FIX_280,
    TRUST_MUTATION_AUTHORITY_FIX_280,
)
from aethos_core.mission_control.autonomous_application_lifecycle_management.autonomous_application_lifecycle_management_store import (
    has_human_lifecycle_decision_approve,
    list_autonomous_application_lifecycle_management_records,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_service import (
    build_autonomous_product_stewardship,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)

_STAGE_NOTE_KIND: dict[str, str] = {
    "concept_lifecycle_note": "concept",
    "design_lifecycle_note": "product_design",
    "delivery_lifecycle_note": "delivery",
    "deployment_lifecycle_note": "deployment",
    "operations_lifecycle_note": "operations",
    "recovery_lifecycle_note": "recovery",
    "evolution_lifecycle_note": "evolution",
}


@dataclass(frozen=True)
class AutonomousApplicationLifecycleManagementResult:
    ok: bool
    session_id: str
    autonomous_application_lifecycle_management: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _health_tier(score: float) -> str:
    if score >= 85:
        return "EXCELLENT"
    if score >= 70:
        return "HEALTHY"
    if score >= 50:
        return "WATCH"
    if score >= 30:
        return "AT_RISK"
    return "UNPROVEN"


def _risk_tier(score: float) -> str:
    if score >= 75:
        return "HIGH"
    if score >= 50:
        return "ELEVATED"
    if score >= 30:
        return "MODERATE"
    return "LOW"


def _infer_current_stage(
    *,
    generation_stage: str,
    delivery_rows: list[dict[str, Any]],
    stewardship_approved: bool,
    evolution_approved: bool,
) -> str:
    live_deploy = any("deploy" in list(r.get("live_evidence_stages") or []) for r in delivery_rows)
    live_pr = any("pr_open" in list(r.get("live_evidence_stages") or []) for r in delivery_rows)
    live_plan = any("plan" in list(r.get("live_evidence_stages") or []) for r in delivery_rows)

    if stewardship_approved or evolution_approved:
        return "evolution"
    if live_deploy:
        return "operations"
    if any("rollback" in list(r.get("live_evidence_stages") or []) for r in delivery_rows):
        return "recovery"
    if live_deploy or generation_stage == "existing_delivery_pipeline":
        return "deployment"
    if live_pr or live_plan:
        return "delivery"
    if generation_stage in {"architecture_generation", "delivery_backlog_generation", "governed_repository_creation_plan"}:
        return "product_design"
    return "concept"


def _stage_registry(
    *,
    stage: str,
    generation: dict[str, Any],
    delivery_rows: list[dict[str, Any]],
    evolution_sections: dict[str, Any],
    stewardship_sections: dict[str, Any],
    lifecycle_records: list[dict[str, Any]],
) -> dict[str, Any]:
    gen_sections = generation.get("sections") or {}
    stage_records = [
        r
        for r in lifecycle_records
        if r.get("lifecycle_stage") == stage or _STAGE_NOTE_KIND.get(str(r.get("kind") or "")) == stage
    ]

    if stage == "concept":
        product = (gen_sections.get("product_understanding_package") or [{}])[0]
        artifacts = ["ideas", "vision", "goals"] if product.get("present") else ["ideas_pending"]
        status = "active" if product.get("present") else "pending"
    elif stage == "product_design":
        artifacts = []
        for key in ("architecture_package", "repository_blueprint", "delivery_backlog"):
            item = (gen_sections.get(key) or [{}])[0]
            if item.get("present"):
                artifacts.append(key)
        status = "active" if artifacts else "pending"
    elif stage == "delivery":
        artifacts = [r.get("repository") for r in delivery_rows if r.get("live_evidence_stages")]
        status = "active" if artifacts else "pending"
    elif stage == "deployment":
        artifacts = [
            r.get("repository")
            for r in delivery_rows
            if "deploy" in list(r.get("live_evidence_stages") or [])
            or r.get("program_visibility") == "proven_end_to_end"
        ]
        status = "active" if artifacts else "pending"
    elif stage == "operations":
        artifacts = [
            r.get("repository")
            for r in delivery_rows
            if "monitor" in list(r.get("live_evidence_stages") or [])
        ]
        status = "active" if artifacts else "watch"
    elif stage == "recovery":
        artifacts = [
            r.get("repository")
            for r in delivery_rows
            if "rollback" in list(r.get("live_evidence_stages") or [])
        ]
        status = "ready" if artifacts else "standby"
    else:
        backlog = (evolution_sections.get("portfolio_evolution_backlog") or [{}])[0]
        steward_backlog = (stewardship_sections.get("stewardship_backlog") or [{}])[0]
        artifacts = [
            f"evolution_epics:{len(backlog.get('epics') or [])}",
            f"stewardship_epics:{len(steward_backlog.get('epics') or [])}",
        ]
        status = "active"

    return {
        "stage": stage,
        "registry_id": f"lifecycle-{stage.replace('_', '-')}-registry",
        "status": status,
        "artifact_count": len(artifacts),
        "artifacts": artifacts[:10],
        "operator_note_count": len(stage_records),
        "read_only": True,
    }


def _lifecycle_timeline(
    *,
    generation: dict[str, Any],
    delivery_rows: list[dict[str, Any]],
    lifecycle_records: list[dict[str, Any]],
    current_stage: str,
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    product_name = str(generation.get("product_name") or "application")
    events.append(
        {
            "event_id": "timeline-concept",
            "stage": "concept",
            "label": f"Concept registered for {product_name}",
            "source": "fix_250_generation",
            "read_only": True,
        }
    )
    if generation.get("current_stage") not in {"product_understanding"}:
        events.append(
            {
                "event_id": "timeline-design",
                "stage": "product_design",
                "label": f"Design artifacts at stage {generation.get('current_stage')}",
                "source": "fix_250_generation",
                "read_only": True,
            }
        )
    for row in delivery_rows:
        repo = row.get("display_name") or row.get("repository")
        for stage in row.get("live_evidence_stages") or []:
            events.append(
                {
                    "event_id": f"timeline-{row.get('repository')}-{stage}",
                    "stage": "delivery"
                    if stage in {"plan", "patch", "verify", "pr_open"}
                    else "deployment"
                    if stage == "deploy"
                    else "operations"
                    if stage == "monitor"
                    else "recovery"
                    if stage == "rollback"
                    else "delivery",
                    "label": f"{repo}: {stage} evidence",
                    "source": "fix_260_program_visibility",
                    "read_only": True,
                }
            )
    for record in lifecycle_records[-20:]:
        events.append(
            {
                "event_id": f"timeline-record-{record.get('recorded_at', 'note')}",
                "stage": record.get("lifecycle_stage") or _STAGE_NOTE_KIND.get(str(record.get("kind") or ""), "concept"),
                "label": record.get("content"),
                "source": "lifecycle_memory",
                "read_only": True,
            }
        )
    return [
        {
            "timeline_id": "application-lifecycle-timeline",
            "current_stage": current_stage,
            "event_count": len(events),
            "events": events,
            "read_only": True,
        }
    ]


def _health_dashboard(
    *,
    engineering_sections: dict[str, Any],
    stewardship_sections: dict[str, Any],
    evolution_sections: dict[str, Any],
) -> list[dict[str, Any]]:
    portfolio_summary = dict(
        ((engineering_sections.get("portfolio_engineering_dashboard") or [{}])[0]).get("portfolio_summary") or {}
    )
    portfolio_score = float(portfolio_summary.get("portfolio_engineering_health_score") or 0)
    steward_dashboard = (stewardship_sections.get("product_stewardship_dashboard") or [{}])[0]
    evolution_dashboard = (evolution_sections.get("product_evolution_dashboard") or [{}])[0]

    dimensions = {
        "delivery": portfolio_score,
        "operational": max(0.0, portfolio_score - 10),
        "governance": 75.0 if steward_dashboard.get("governance_friction_trends") else 55.0,
        "evolution": 70.0 if evolution_dashboard.get("top_opportunities") else 45.0,
        "portfolio": portfolio_score,
    }
    rows = [
        {
            "dimension": dim,
            "health_score": round(score, 1),
            "health_tier": _health_tier(score),
            "read_only": True,
        }
        for dim, score in dimensions.items()
        if dim in LIFECYCLE_HEALTH_DIMENSIONS
    ]
    overall = round(sum(r["health_score"] for r in rows) / len(rows), 1) if rows else 0.0
    return [
        {
            "dashboard_id": "lifecycle-health-dashboard",
            "overall_health_score": overall,
            "overall_health_tier": _health_tier(overall),
            "dimensions": rows,
            "read_only": True,
        }
    ]


def _risk_dashboard(
    *,
    engineering_sections: dict[str, Any],
    stewardship_sections: dict[str, Any],
) -> list[dict[str, Any]]:
    health_rows = list(engineering_sections.get("engineering_health_scores") or [])
    at_risk = sum(1 for r in health_rows if r.get("engineering_health_tier") in {"WATCH", "AT_RISK", "UNPROVEN"})
    steward_dashboard = (stewardship_sections.get("product_stewardship_dashboard") or [{}])[0]
    biggest_risks = list(steward_dashboard.get("biggest_risks") or [])

    dimensions = {
        "delivery": min(100.0, at_risk * 20 + 20),
        "operational": min(100.0, len(steward_dashboard.get("operational_concerns") or []) * 15 + 15),
        "governance": min(100.0, len(steward_dashboard.get("governance_friction_trends") or []) * 15 + 10),
        "architecture": min(100.0, len(steward_dashboard.get("architecture_concerns") or []) * 15 + 10),
        "product": min(100.0, len(biggest_risks) * 12 + 10),
    }
    rows = [
        {
            "dimension": dim,
            "risk_score": round(score, 1),
            "risk_tier": _risk_tier(score),
            "read_only": True,
        }
        for dim, score in dimensions.items()
        if dim in LIFECYCLE_RISK_DIMENSIONS
    ]
    return [
        {
            "dashboard_id": "lifecycle-risk-dashboard",
            "overall_risk_tier": _risk_tier(max(r["risk_score"] for r in rows) if rows else 0),
            "dimensions": rows,
            "read_only": True,
        }
    ]


def _unified_opportunities(
    *,
    generation: dict[str, Any],
    evolution_sections: dict[str, Any],
    stewardship_sections: dict[str, Any],
) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    readiness = (generation.get("sections") or {}).get("generation_readiness_report") or [{}]
    if readiness and readiness[0].get("ready_for_delivery_pipeline_handoff") is False:
        opportunities.append(
            {
                "opportunity_id": "generation-readiness-gap",
                "source_fix": "FIX 250",
                "lifecycle_stage": "product_design",
                "title": "Complete generation readiness before delivery handoff",
                "detail": str(readiness[0].get("outstanding_blockers") or "Generation readiness incomplete"),
                "read_only": True,
            }
        )
    for item in list(evolution_sections.get("evolution_priority_matrix") or [])[:10]:
        if item.get("opportunity_id") or item.get("title"):
            opportunities.append(
                {
                    "opportunity_id": item.get("opportunity_id"),
                    "source_fix": "FIX 261",
                    "lifecycle_stage": "evolution",
                    "title": item.get("title"),
                    "priority_tier": item.get("priority_tier"),
                    "read_only": True,
                }
            )
    steward_registry = (stewardship_sections.get("stewardship_opportunity_registry") or [{}])[0]
    for item in (steward_registry.get("improvement_candidates") or [])[:10]:
        opportunities.append(
            {
                "opportunity_id": item.get("candidate_id"),
                "source_fix": "FIX 270",
                "lifecycle_stage": "evolution",
                "title": item.get("title"),
                "priority_tier": item.get("priority_tier"),
                "read_only": True,
            }
        )
    return [
        {
            "registry_id": "lifecycle-opportunity-registry",
            "opportunity_count": len(opportunities),
            "opportunities": opportunities,
            "read_only": True,
        }
    ]


def _lifecycle_memory(
    *,
    lifecycle_records: list[dict[str, Any]],
    timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            "memory_id": "application-lifecycle-memory",
            "event_count": len((timeline[0].get("events") or []) if timeline else []),
            "decision_history_count": sum(
                1
                for r in lifecycle_records
                if str(r.get("kind") or "").startswith("human_lifecycle_decision_")
            ),
            "observation_count": len(lifecycle_records),
            "entries": [{**r, "read_only": True} for r in lifecycle_records[-50:]],
            "read_only": True,
        }
    ]


def build_autonomous_application_lifecycle_management(
    *, session_id: str
) -> AutonomousApplicationLifecycleManagementResult:
    sid = (session_id or "default").strip()[:64] or "default"
    lifecycle_records = list_autonomous_application_lifecycle_management_records()
    human_approved = has_human_lifecycle_decision_approve(session_id=sid)

    generation = build_governed_application_generation(session_id=sid)
    gen_payload = generation.governed_application_generation or {}

    engineering = build_multi_repository_engineering_intelligence(session_id=sid)
    engineering_sections = engineering.multi_repository_engineering_intelligence.get("sections") or {}
    delivery_rows = list(engineering_sections.get("program_delivery_visibility") or [])

    evolution = build_cross_repository_product_evolution_intelligence(session_id=sid)
    evolution_sections = (evolution.cross_repository_product_evolution_intelligence or {}).get("sections") or {}

    stewardship = build_autonomous_product_stewardship(session_id=sid)
    stewardship_sections = (stewardship.autonomous_product_stewardship or {}).get("sections") or {}

    evolution_approved = bool(
        (evolution.cross_repository_product_evolution_intelligence or {}).get("human_evolution_decision_approve")
    )
    stewardship_approved = bool(
        (stewardship.autonomous_product_stewardship or {}).get("human_stewardship_decision_approve")
    )

    current_stage = _infer_current_stage(
        generation_stage=str(gen_payload.get("current_stage") or "product_understanding"),
        delivery_rows=delivery_rows,
        stewardship_approved=stewardship_approved,
        evolution_approved=evolution_approved,
    )

    stage_registries = [
        _stage_registry(
            stage=stage,
            generation=gen_payload,
            delivery_rows=delivery_rows,
            evolution_sections=evolution_sections,
            stewardship_sections=stewardship_sections,
            lifecycle_records=lifecycle_records,
        )
        for stage in LIFECYCLE_STAGES
    ]

    timeline = _lifecycle_timeline(
        generation=gen_payload,
        delivery_rows=delivery_rows,
        lifecycle_records=lifecycle_records,
        current_stage=current_stage,
    )
    health_dashboard = _health_dashboard(
        engineering_sections=engineering_sections,
        stewardship_sections=stewardship_sections,
        evolution_sections=evolution_sections,
    )
    risk_dashboard = _risk_dashboard(
        engineering_sections=engineering_sections,
        stewardship_sections=stewardship_sections,
    )
    opportunity_registry = _unified_opportunities(
        generation=gen_payload,
        evolution_sections=evolution_sections,
        stewardship_sections=stewardship_sections,
    )
    lifecycle_memory = _lifecycle_memory(lifecycle_records=lifecycle_records, timeline=timeline)

    sections = {
        "lifecycle_stage_registry": stage_registries,
        "application_lifecycle_timeline": timeline,
        "lifecycle_health_dashboard": health_dashboard,
        "lifecycle_risk_dashboard": risk_dashboard,
        "lifecycle_opportunity_registry": opportunity_registry,
        "application_lifecycle_memory": lifecycle_memory,
        "lifecycle_management_dashboard": [
            {
                "dashboard_id": "lifecycle-management-dashboard",
                "current_lifecycle_stage": current_stage,
                "lifecycle_stages": list(LIFECYCLE_STAGES),
                "overall_health": (health_dashboard[0] if health_dashboard else {}).get("overall_health_tier"),
                "overall_risk": (risk_dashboard[0] if risk_dashboard else {}).get("overall_risk_tier"),
                "open_opportunity_count": (opportunity_registry[0] if opportunity_registry else {}).get(
                    "opportunity_count", 0
                ),
                "delivery_status": "active" if any(r.get("live_evidence_stages") for r in delivery_rows) else "pending",
                "operational_status": "active" if current_stage in {"operations", "recovery", "evolution"} else "watch",
                "recovery_status": "ready" if current_stage == "recovery" else "standby",
                "evolution_status": "active" if current_stage == "evolution" else "pending",
                "human_lifecycle_decision_approve": human_approved,
                "feeds_governed_delivery_planning": human_approved,
                "read_only": True,
            }
        ],
        "human_lifecycle_review": [
            {
                "review_id": "human-lifecycle-decision",
                "decisions_supported": list(
                    (
                        "human_lifecycle_decision_approve",
                        "human_lifecycle_decision_hold",
                        "human_lifecycle_decision_reject",
                        "human_lifecycle_decision_defer",
                    )
                ),
                "human_lifecycle_decision_approve": human_approved,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_lifecycle_management_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_LIFECYCLE_MANAGEMENT_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_SCHEMA_VERSION,
        "fix": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_280,
        "execution_performed": EXECUTION_PERFORMED_FIX_280,
        "lifecycle_compose_artifacts_only": AUTONOMOUS_APPLICATION_LIFECYCLE_COMPOSES_EVIDENCE_ONLY_FIX_280,
        "lifecycle_management_authority": LIFECYCLE_MANAGEMENT_AUTHORITY_FIX_280,
        "automatic_lifecycle_execution_enabled": AUTOMATIC_LIFECYCLE_EXECUTION_ENABLED_FIX_280,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_280,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_280,
        "rollback_authority": ROLLBACK_AUTHORITY_FIX_280,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_280,
        "merge_authority": MERGE_AUTHORITY_FIX_280,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_280,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_280,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_280,
        "invariant": AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_INVARIANT,
        "session_id": sid,
        "current_lifecycle_stage": current_stage,
        "lifecycle_stages": list(LIFECYCLE_STAGES),
        "sections": sections,
        "operator_record_count": len(lifecycle_records),
        "human_lifecycle_decision_approve": human_approved,
        "fix_280_certification_requirements": list(FIX_280_CERTIFICATION_REQUIREMENTS),
        "autonomous_application_lifecycle_management_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in AUTONOMOUS_APPLICATION_LIFECYCLE_MANAGEMENT_PRINCIPLES
        ],
        "sources": {
            "composes_fix_250_governed_application_generation": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_fix_261_product_evolution_intelligence": True,
            "composes_fix_270_product_stewardship": True,
            "composes_governed_lifecycle_capabilities_200_230": True,
            "pilot_reexecution_performed": False,
            "code_generation_performed": False,
        },
    }

    return AutonomousApplicationLifecycleManagementResult(
        ok=True,
        session_id=sid,
        autonomous_application_lifecycle_management=payload,
        detail="Autonomous application lifecycle management composed from unified lifecycle evidence (lifecycle ≠ execution).",
    )
