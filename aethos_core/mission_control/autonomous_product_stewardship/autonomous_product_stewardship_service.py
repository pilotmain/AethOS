# SPDX-License-Identifier: Apache-2.0
"""FIX 270 — autonomous product stewardship service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_270_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_COMPOSES_EVIDENCE_ONLY_FIX_270,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_FIX,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_INVARIANT,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_PRINCIPLES,
    AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION,
    CROSS_REPO_EXECUTION_ENABLED_FIX_270,
    DEPLOYMENT_AUTHORITY_FIX_270,
    EXECUTION_PERFORMED_FIX_270,
    FORBIDDEN_PRODUCT_STEWARDSHIP_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_270,
    GOVERNANCE_MUTATION_PERFORMED_FIX_270,
    MERGE_AUTHORITY_FIX_270,
    MUTATION_PERFORMED_FIX_270,
    PORTFOLIO_REPOSITORIES,
    PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
    PROVIDER_MUTATION_AUTHORITY_FIX_270,
    REPOSITORY_DISPLAY_NAMES,
    REPOSITORY_MUTATION_AUTHORITY_FIX_270,
    STEWARDSHIP_DOMAINS,
    STEWARDSHIP_PRIORITY_TIERS,
    TRUST_MUTATION_AUTHORITY_FIX_270,
)
from aethos_core.mission_control.autonomous_product_stewardship.autonomous_product_stewardship_store import (
    has_human_stewardship_decision_approve,
    list_autonomous_product_stewardship_records,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_service import (
    build_cross_repository_product_evolution_intelligence,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)

_DOMAIN_MAP: dict[str, str] = {
    "feature": "product_health",
    "quality": "engineering",
    "architecture": "engineering",
    "operational": "operational",
    "ux": "governance",
}

_OBSERVATION_KIND_DOMAIN: dict[str, str] = {
    "product_health_observation": "product_health",
    "engineering_stewardship_observation": "engineering",
    "operational_stewardship_observation": "operational",
    "governance_stewardship_observation": "governance",
    "portfolio_stewardship_observation": "portfolio",
}


@dataclass(frozen=True)
class AutonomousProductStewardshipResult:
    ok: bool
    session_id: str
    autonomous_product_stewardship: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _priority_tier(score: float) -> str:
    if score >= 85:
        return "CRITICAL"
    if score >= 70:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    if score >= 30:
        return "LOW"
    return "DEFER"


def _stewardship_score(
    *,
    impact: float,
    risk: float,
    urgency: float,
    effort: float,
    strategic_value: float,
    confidence: float,
) -> dict[str, Any]:
    composite = round(
        impact * 0.25
        + strategic_value * 0.20
        + urgency * 0.20
        + confidence * 0.15
        + risk * 0.10
        + (100 - effort) * 0.10,
        1,
    )
    composite = max(0.0, min(100.0, composite))
    return {
        "impact": impact,
        "risk": risk,
        "urgency": urgency,
        "effort": effort,
        "strategic_value": strategic_value,
        "confidence": confidence,
        "composite_score": composite,
        "priority_tier": _priority_tier(composite),
        "read_only": True,
    }


def _collect_evolution_opportunities(evolution_sections: dict[str, Any]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for domain in ("feature", "quality", "architecture", "operational", "ux"):
        report = (evolution_sections.get(f"{domain}_evolution_report") or [{}])[0]
        for rec in report.get("recommendations") or []:
            opportunities.append(dict(rec))
    return opportunities


def _to_stewardship_candidate(opp: dict[str, Any]) -> dict[str, Any]:
    domain = _DOMAIN_MAP.get(str(opp.get("domain") or ""), "portfolio")
    urgency = 70.0 if opp.get("priority_tier") in {"CRITICAL", "HIGH"} else 45.0
    return {
        "candidate_id": f"steward-{opp.get('opportunity_id', 'unknown')}",
        "stewardship_domain": domain,
        "repository": opp.get("repository"),
        "display_name": opp.get("display_name"),
        "title": opp.get("title"),
        "detail": opp.get("detail"),
        "source": opp.get("source"),
        "recommendation_type": "improvement_candidate",
        **_stewardship_score(
            impact=float(opp.get("impact") or 50),
            risk=float(opp.get("risk") or 40),
            urgency=urgency,
            effort=float(opp.get("effort") or 50),
            strategic_value=float(opp.get("strategic_value") or 55),
            confidence=float(opp.get("confidence") or 70),
        ),
        "read_only": True,
    }


def _operator_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for record in records:
        kind = str(record.get("kind") or "")
        domain = _OBSERVATION_KIND_DOMAIN.get(kind)
        if not domain and kind != "stewardship_opportunity_note":
            continue
        out.append(
            {
                "candidate_id": f"steward-operator-{record.get('recorded_at', 'note')}",
                "stewardship_domain": domain or str(record.get("domain") or "portfolio"),
                "repository": record.get("repository") or "portfolio",
                "display_name": REPOSITORY_DISPLAY_NAMES.get(
                    str(record.get("repository") or ""), str(record.get("repository") or "Portfolio")
                ),
                "title": record.get("content"),
                "detail": "Operator stewardship observation.",
                "source": "stewardship_memory",
                "recommendation_type": "operator_observation",
                "operator_recorded": True,
                **_stewardship_score(
                    impact=55,
                    risk=25,
                    urgency=60,
                    effort=40,
                    strategic_value=50,
                    confidence=90,
                ),
                "read_only": True,
            }
        )
    return out


def _domain_report(
    *,
    domain: str,
    candidates: list[dict[str, Any]],
    engineering_sections: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    domain_candidates = [c for c in candidates if c.get("stewardship_domain") == domain]
    signals: list[str] = []
    if domain == "engineering" and engineering_sections:
        at_risk = [
            r
            for r in engineering_sections.get("engineering_health_scores") or []
            if r.get("engineering_health_tier") in {"WATCH", "AT_RISK"}
        ]
        if at_risk:
            signals.append(f"{len(at_risk)} repositories in WATCH/AT_RISK health tiers")
    if domain == "governance":
        high_intervention = [c for c in candidates if "intervention" in str(c.get("title") or "").lower()]
        if high_intervention:
            signals.append(f"{len(high_intervention)} governance friction signals detected")
    if domain == "portfolio":
        portfolio_candidates = [c for c in candidates if c.get("repository") == "portfolio"]
        signals.append(f"{len(portfolio_candidates)} cross-repository stewardship candidates")

    return [
        {
            "report_id": f"{domain.replace('_', '-')}-stewardship-report",
            "stewardship_domain": domain,
            "monitoring_signals": signals or ["Continuous observation active — no critical signals"],
            "recommendation_count": len(domain_candidates),
            "recommendations": domain_candidates[:10],
            "advisory_only": True,
            "read_only": True,
        }
    ]


def _stewardship_backlog(*, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(candidates, key=lambda c: float(c.get("composite_score") or 0), reverse=True)
    epics: list[dict[str, Any]] = []
    for idx, cand in enumerate(ranked[:8], start=1):
        epics.append(
            {
                "epic_id": f"steward-epic-{idx:02d}",
                "title": cand.get("title"),
                "stewardship_domain": cand.get("stewardship_domain"),
                "repository": cand.get("repository"),
                "priority_tier": cand.get("priority_tier"),
                "features": [
                    {
                        "feature_id": f"steward-feature-{idx:02d}",
                        "title": cand.get("title"),
                        "stories": [
                            {
                                "story_id": f"steward-story-{idx:02d}",
                                "title": f"Review stewardship recommendation: {cand.get('title')}",
                                "tasks": [
                                    {
                                        "task_id": f"steward-task-{idx:02d}",
                                        "title": "Route approved recommendation into governed delivery planning",
                                        "dependencies": [],
                                        "read_only": True,
                                    }
                                ],
                                "read_only": True,
                            }
                        ],
                        "read_only": True,
                    }
                ],
                "dependencies": [],
                "advisory_only": True,
                "read_only": True,
            }
        )
    return [{"backlog_id": "stewardship-backlog", "epics": epics, "read_only": True}]


def _stewardship_memory(
    *,
    stewardship_records: list[dict[str, Any]],
    evolution_memory: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for record in stewardship_records[-30:]:
        entries.append(
            {
                "memory_id": f"steward-{record.get('recorded_at', 'note')}",
                "kind": record.get("kind"),
                "content": record.get("content"),
                "recorded_at": record.get("recorded_at"),
                "domain": record.get("domain") or _OBSERVATION_KIND_DOMAIN.get(str(record.get("kind") or "")),
                "read_only": True,
            }
        )
    for record in evolution_memory[-10:]:
        entries.append(
            {
                "memory_id": f"evolution-ref-{record.get('recorded_at', 'note')}",
                "kind": record.get("kind"),
                "content": record.get("content"),
                "recorded_at": record.get("recorded_at"),
                "source": "fix_261_evolution_memory",
                "read_only": True,
            }
        )
    return [
        {
            "memory_id": "product-stewardship-memory",
            "observation_count": len(stewardship_records),
            "decision_history_count": sum(
                1
                for r in stewardship_records
                if str(r.get("kind") or "").startswith("human_stewardship_decision_")
            ),
            "entries": entries,
            "read_only": True,
        }
    ]


def build_autonomous_product_stewardship(*, session_id: str) -> AutonomousProductStewardshipResult:
    sid = (session_id or "default").strip()[:64] or "default"
    stewardship_records = list_autonomous_product_stewardship_records()
    human_approved = has_human_stewardship_decision_approve(session_id=sid)

    evolution = build_cross_repository_product_evolution_intelligence(session_id=sid)
    evolution_payload = evolution.cross_repository_product_evolution_intelligence or {}
    evolution_sections = evolution_payload.get("sections") or {}

    engineering = build_multi_repository_engineering_intelligence(session_id=sid)
    engineering_sections = engineering.multi_repository_engineering_intelligence.get("sections") or {}

    evolution_opps = _collect_evolution_opportunities(evolution_sections)
    candidates = [_to_stewardship_candidate(o) for o in evolution_opps]
    candidates.extend(_operator_candidates(stewardship_records))

    priority_matrix = [
        {
            "matrix_id": "stewardship-priority-matrix",
            "candidate_id": c.get("candidate_id"),
            "title": c.get("title"),
            "stewardship_domain": c.get("stewardship_domain"),
            "repository": c.get("repository"),
            "impact": c.get("impact"),
            "risk": c.get("risk"),
            "urgency": c.get("urgency"),
            "effort": c.get("effort"),
            "strategic_value": c.get("strategic_value"),
            "confidence": c.get("confidence"),
            "composite_score": c.get("composite_score"),
            "priority_tier": c.get("priority_tier"),
            "read_only": True,
        }
        for c in sorted(candidates, key=lambda x: float(x.get("composite_score") or 0), reverse=True)
    ]

    stewardship_backlog = _stewardship_backlog(candidates=candidates)
    top_candidates = priority_matrix[:5]

    sections = {
        "product_health_report": _domain_report(domain="product_health", candidates=candidates),
        "engineering_stewardship_report": _domain_report(
            domain="engineering",
            candidates=candidates,
            engineering_sections=engineering_sections,
        ),
        "operational_stewardship_report": _domain_report(domain="operational", candidates=candidates),
        "governance_stewardship_report": _domain_report(domain="governance", candidates=candidates),
        "portfolio_stewardship_report": _domain_report(domain="portfolio", candidates=candidates),
        "stewardship_opportunity_registry": [
            {
                "registry_id": "stewardship-opportunity-registry",
                "candidate_count": len(candidates),
                "improvement_candidates": [c for c in candidates if c.get("recommendation_type") == "improvement_candidate"],
                "risk_mitigations": [c for c in candidates if float(c.get("risk") or 0) >= 50],
                "operator_observations": [c for c in candidates if c.get("operator_recorded")],
                "read_only": True,
            }
        ],
        "stewardship_priority_matrix": priority_matrix,
        "stewardship_backlog": stewardship_backlog,
        "product_stewardship_dashboard": [
            {
                "dashboard_id": "product-stewardship-dashboard",
                "top_opportunities": top_candidates,
                "biggest_risks": [c for c in priority_matrix if float(c.get("risk") or 0) >= 50][:5],
                "technical_debt_hotspots": [
                    c for c in candidates if c.get("stewardship_domain") == "engineering"
                ][:5],
                "architecture_concerns": [
                    c
                    for c in candidates
                    if "architecture" in str(c.get("title") or "").lower()
                    or c.get("stewardship_domain") == "engineering"
                ][:5],
                "operational_concerns": [
                    c for c in candidates if c.get("stewardship_domain") == "operational"
                ][:5],
                "governance_friction_trends": [
                    c for c in candidates if c.get("stewardship_domain") == "governance"
                ][:5],
                "recommended_next_actions": top_candidates[:3],
                "stewardship_backlog_epic_count": len((stewardship_backlog[0].get("epics") or [])),
                "human_stewardship_decision_approve": human_approved,
                "feeds_governed_delivery_planning": human_approved,
                "read_only": True,
            }
        ],
        "product_stewardship_memory": _stewardship_memory(
            stewardship_records=stewardship_records,
            evolution_memory=list(evolution_sections.get("product_evolution_memory") or []),
        ),
        "human_stewardship_review": [
            {
                "review_id": "human-stewardship-decision",
                "decisions_supported": [
                    "human_stewardship_decision_approve",
                    "human_stewardship_decision_hold",
                    "human_stewardship_decision_reject",
                    "human_stewardship_decision_defer",
                ],
                "human_stewardship_decision_approve": human_approved,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "forbidden_stewardship_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PRODUCT_STEWARDSHIP_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": AUTONOMOUS_PRODUCT_STEWARDSHIP_SCHEMA_VERSION,
        "fix": AUTONOMOUS_PRODUCT_STEWARDSHIP_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_270,
        "execution_performed": EXECUTION_PERFORMED_FIX_270,
        "stewardship_compose_artifacts_only": AUTONOMOUS_PRODUCT_STEWARDSHIP_COMPOSES_EVIDENCE_ONLY_FIX_270,
        "product_stewardship_authority": PRODUCT_STEWARDSHIP_AUTHORITY_FIX_270,
        "automatic_improvement_enabled": AUTOMATIC_IMPROVEMENT_ENABLED_FIX_270,
        "cross_repo_execution_enabled": CROSS_REPO_EXECUTION_ENABLED_FIX_270,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_270,
        "deployment_authority": DEPLOYMENT_AUTHORITY_FIX_270,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_270,
        "merge_authority": MERGE_AUTHORITY_FIX_270,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_270,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_270,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_270,
        "invariant": AUTONOMOUS_PRODUCT_STEWARDSHIP_INVARIANT,
        "session_id": sid,
        "repositories": list(PORTFOLIO_REPOSITORIES),
        "stewardship_domains": list(STEWARDSHIP_DOMAINS),
        "stewardship_priority_tiers": list(STEWARDSHIP_PRIORITY_TIERS),
        "sections": sections,
        "candidate_count": len(candidates),
        "operator_record_count": len(stewardship_records),
        "human_stewardship_decision_approve": human_approved,
        "fix_270_certification_requirements": list(FIX_270_CERTIFICATION_REQUIREMENTS),
        "autonomous_product_stewardship_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in AUTONOMOUS_PRODUCT_STEWARDSHIP_PRINCIPLES
        ],
        "sources": {
            "composes_fix_261_product_evolution_intelligence": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_fix_250_governed_application_generation": True,
            "composes_fix_240_repository_knowledge_graph": True,
            "composes_fix_189_190_agent_metrics": True,
            "composes_fix_191_cross_repository_validation": True,
            "composes_fix_186_192_194_196_trust_baselines": True,
            "pilot_reexecution_performed": False,
            "code_generation_performed": False,
        },
    }

    return AutonomousProductStewardshipResult(
        ok=True,
        session_id=sid,
        autonomous_product_stewardship=payload,
        detail="Autonomous product stewardship composed from portfolio evidence (stewardship ≠ execution).",
    )
