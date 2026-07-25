# SPDX-License-Identifier: Apache-2.0
"""FIX 261 — cross-repository product evolution intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_261_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_contract import (
    AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
    CROSS_REPO_EXECUTION_ENABLED_FIX_261,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_COMPOSES_EVIDENCE_ONLY_FIX_261,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_FIX,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_INVARIANT,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_PRINCIPLES,
    CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION,
    DEPLOY_AUTHORITY_FIX_261,
    EVOLUTION_DOMAINS,
    EVOLUTION_PRIORITY_TIERS,
    EXECUTION_PERFORMED_FIX_261,
    FORBIDDEN_PRODUCT_EVOLUTION_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_261,
    GOVERNANCE_MUTATION_PERFORMED_FIX_261,
    MERGE_AUTHORITY_FIX_261,
    MUTATION_PERFORMED_FIX_261,
    PORTFOLIO_REPOSITORIES,
    PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
    PROVIDER_MUTATION_AUTHORITY_FIX_261,
    REPOSITORY_DISPLAY_NAMES,
    REPOSITORY_MUTATION_AUTHORITY_FIX_261,
    TRUST_MUTATION_AUTHORITY_FIX_261,
)
from aethos_core.mission_control.cross_repository_product_evolution_intelligence.cross_repository_product_evolution_intelligence_store import (
    has_human_evolution_decision_approve,
    list_cross_repository_product_evolution_intelligence_records,
)
from aethos_core.mission_control.governed_application_generation.governed_application_generation_service import (
    build_governed_application_generation,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_service import (
    build_multi_repository_engineering_intelligence,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
    list_repository_knowledge_graph_records,
)


@dataclass(frozen=True)
class CrossRepositoryProductEvolutionIntelligenceResult:
    ok: bool
    session_id: str
    cross_repository_product_evolution_intelligence: dict[str, Any] = field(default_factory=dict)
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


def _priority_score(
    *,
    impact: float,
    risk: float,
    effort: float,
    strategic_value: float,
    confidence: float,
) -> dict[str, Any]:
    composite = round(
        impact * 0.30 + strategic_value * 0.25 + confidence * 0.20 + risk * 0.15 + (100 - effort) * 0.10,
        1,
    )
    composite = max(0.0, min(100.0, composite))
    return {
        "impact": impact,
        "risk": risk,
        "effort": effort,
        "strategic_value": strategic_value,
        "confidence": confidence,
        "composite_score": composite,
        "priority_tier": _priority_tier(composite),
        "read_only": True,
    }


def _repo_opportunities(
    *,
    repo: str,
    validation_row: dict[str, Any],
    health_row: dict[str, Any],
    knowledge_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    display = REPOSITORY_DISPLAY_NAMES.get(repo, repo)
    trust_state = str(validation_row.get("trust_state") or "UNPROVEN")
    progression = dict(validation_row.get("pilot_progression") or {})
    interventions = int(validation_row.get("human_intervention_count") or 0)
    health_score = float(health_row.get("engineering_health_score") or 0)
    health_tier = str(health_row.get("engineering_health_tier") or "UNPROVEN")
    knowledge_count = len(knowledge_records)

    opportunities: list[dict[str, Any]] = []

    if not progression.get("pilot_3_complete") and trust_state == "CONDITIONALLY_TRUSTED":
        opportunities.append(
            {
                "opportunity_id": f"{repo}-feature-end-to-end-proof",
                "domain": "feature",
                "repository": repo,
                "display_name": display,
                "title": f"Prove end-to-end delivery loop on {display}",
                "detail": "Pilot 3 PR-open evidence strengthens product confidence.",
                "source": "fix_191_pilot_progression",
                **_priority_score(impact=75, risk=40, effort=55, strategic_value=80, confidence=70),
            }
        )

    if health_tier in {"WATCH", "AT_RISK", "UNPROVEN"}:
        opportunities.append(
            {
                "opportunity_id": f"{repo}-quality-health-recovery",
                "domain": "quality",
                "repository": repo,
                "display_name": display,
                "title": f"Reduce technical debt on {display}",
                "detail": f"Engineering health tier {health_tier} at score {health_score}.",
                "source": "fix_260_engineering_health",
                **_priority_score(impact=70, risk=55, effort=60, strategic_value=65, confidence=75),
            }
        )

    if interventions >= 2:
        opportunities.append(
            {
                "opportunity_id": f"{repo}-operational-intervention-reduction",
                "domain": "operational",
                "repository": repo,
                "display_name": display,
                "title": f"Reduce operator interventions on {display}",
                "detail": f"{interventions} human interventions recorded across pilot sessions.",
                "source": "fix_189_190_metrics",
                **_priority_score(impact=65, risk=45, effort=50, strategic_value=70, confidence=80),
            }
        )

    if knowledge_count < 3:
        opportunities.append(
            {
                "opportunity_id": f"{repo}-architecture-knowledge-depth",
                "domain": "architecture",
                "repository": repo,
                "display_name": display,
                "title": f"Deepen architecture knowledge for {display}",
                "detail": f"Only {knowledge_count} knowledge graph records — expand FIX 240 coverage.",
                "source": "fix_240_knowledge_graph",
                **_priority_score(impact=60, risk=35, effort=45, strategic_value=60, confidence=85),
            }
        )

    if interventions >= 1 or health_tier in {"WATCH", "AT_RISK"}:
        opportunities.append(
            {
                "opportunity_id": f"{repo}-ux-operator-friction",
                "domain": "ux",
                "repository": repo,
                "display_name": display,
                "title": f"Reduce operator workflow friction on {display}",
                "detail": "Interventions and health signals suggest approval or workflow friction.",
                "source": "fix_191_interventions",
                **_priority_score(impact=55, risk=30, effort=40, strategic_value=55, confidence=65),
            }
        )

    return opportunities


def _shared_opportunities(
    *,
    matrix: list[dict[str, Any]],
    dependency_map: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    shared: list[dict[str, Any]] = []
    trusted = [r for r in matrix if r.get("trust_state") == "CONDITIONALLY_TRUSTED"]
    if len(trusted) >= 4:
        shared.append(
            {
                "opportunity_id": "portfolio-cross-repo-stewardship",
                "domain": "feature",
                "repository": "portfolio",
                "display_name": "Portfolio",
                "title": "Coordinate cross-repository product evolution backlog",
                "detail": "All four repositories conditionally trusted — portfolio-wide planning is safe to review.",
                "source": "trust_baseline_complete",
                **_priority_score(impact=85, risk=25, effort=50, strategic_value=90, confidence=80),
            }
        )

    high_intervention_repos = [
        str(r.get("repository") or "")
        for r in matrix
        if int(r.get("human_intervention_count") or 0) >= 2
    ]
    if len(high_intervention_repos) >= 2:
        shared.append(
            {
                "opportunity_id": "portfolio-shared-delivery-bottleneck",
                "domain": "operational",
                "repository": "portfolio",
                "display_name": "Portfolio",
                "title": "Address shared delivery bottlenecks",
                "detail": f"Repeated interventions across: {', '.join(high_intervention_repos)}.",
                "source": "fix_191_cross_repo_pattern",
                **_priority_score(impact=80, risk=50, effort=65, strategic_value=85, confidence=70),
            }
        )

    if len(dependency_map) >= 3:
        shared.append(
            {
                "opportunity_id": "portfolio-architecture-boundary-review",
                "domain": "architecture",
                "repository": "portfolio",
                "display_name": "Portfolio",
                "title": "Review cross-repository architecture boundaries",
                "detail": "Multiple advisory dependency links — evaluate coupling and decomposition.",
                "source": "fix_260_dependency_map",
                **_priority_score(impact=70, risk=40, effort=55, strategic_value=75, confidence=65),
            }
        )

    return shared


def _domain_report(
    *,
    domain: str,
    opportunities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    domain_opps = [o for o in opportunities if o.get("domain") == domain]
    return [
        {
            "report_id": f"{domain}-evolution-report",
            "domain": domain,
            "recommendation_count": len(domain_opps),
            "recommendations": domain_opps[:10],
            "advisory_only": True,
            "read_only": True,
        }
    ]


def _opportunity_graph(*, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_repos: set[str] = set()

    for opp in opportunities:
        repo = str(opp.get("repository") or "")
        if repo and repo not in seen_repos:
            seen_repos.add(repo)
            nodes.append(
                {
                    "node_id": f"repo-{repo}",
                    "kind": "repository",
                    "label": opp.get("display_name") or repo,
                    "repository": repo,
                    "read_only": True,
                }
            )
        nodes.append(
            {
                "node_id": opp.get("opportunity_id"),
                "kind": "opportunity",
                "domain": opp.get("domain"),
                "label": opp.get("title"),
                "priority_tier": opp.get("priority_tier"),
                "read_only": True,
            }
        )
        if repo and repo != "portfolio":
            edges.append(
                {
                    "edge_id": f"{opp.get('opportunity_id')}-repo",
                    "source": f"repo-{repo}",
                    "target": opp.get("opportunity_id"),
                    "relationship": "repository_opportunity",
                    "read_only": True,
                }
            )

    shared_pain = [
        o for o in opportunities if o.get("repository") == "portfolio" and "shared" in str(o.get("source") or "")
    ]
    for opp in shared_pain:
        edges.append(
            {
                "edge_id": f"{opp.get('opportunity_id')}-portfolio",
                "source": "node-portfolio",
                "target": opp.get("opportunity_id"),
                "relationship": "shared_pain_point",
                "read_only": True,
            }
        )

    if any(o.get("repository") == "portfolio" for o in opportunities):
        nodes.insert(
            0,
            {
                "node_id": "node-portfolio",
                "kind": "portfolio",
                "label": "Portfolio",
                "read_only": True,
            },
        )

    return [{"graph_id": "cross-repo-opportunity-graph", "nodes": nodes, "edges": edges, "read_only": True}]


def _evolution_backlog(*, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(opportunities, key=lambda o: float(o.get("composite_score") or 0), reverse=True)
    epics: list[dict[str, Any]] = []
    for idx, opp in enumerate(ranked[:8], start=1):
        epic_id = f"epic-{idx:02d}"
        feature_id = f"feature-{idx:02d}"
        story_id = f"story-{idx:02d}"
        task_id = f"task-{idx:02d}"
        epics.append(
            {
                "epic_id": epic_id,
                "title": opp.get("title"),
                "domain": opp.get("domain"),
                "repository": opp.get("repository"),
                "priority_tier": opp.get("priority_tier"),
                "risk_rank": idx,
                "features": [
                    {
                        "feature_id": feature_id,
                        "title": opp.get("title"),
                        "stories": [
                            {
                                "story_id": story_id,
                                "title": f"Investigate: {opp.get('title')}",
                                "tasks": [
                                    {
                                        "task_id": task_id,
                                        "title": f"Review evidence and propose governed delivery plan for {opp.get('display_name')}",
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
    return [{"backlog_id": "portfolio-evolution-backlog", "epics": epics, "read_only": True}]


def _priority_matrix(*, opportunities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [
        {
            "matrix_id": "evolution-priority-matrix",
            "opportunity_id": o.get("opportunity_id"),
            "title": o.get("title"),
            "domain": o.get("domain"),
            "repository": o.get("repository"),
            "impact": o.get("impact"),
            "risk": o.get("risk"),
            "effort": o.get("effort"),
            "strategic_value": o.get("strategic_value"),
            "confidence": o.get("confidence"),
            "composite_score": o.get("composite_score"),
            "priority_tier": o.get("priority_tier"),
            "read_only": True,
        }
        for o in sorted(opportunities, key=lambda x: float(x.get("composite_score") or 0), reverse=True)
    ]
    return rows


def _operator_opportunities(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domain_map = {
        "feature_evolution_note": "feature",
        "quality_evolution_note": "quality",
        "architecture_evolution_note": "architecture",
        "operational_evolution_note": "operational",
        "ux_evolution_note": "ux",
    }
    out: list[dict[str, Any]] = []
    for record in records:
        kind = str(record.get("kind") or "")
        domain = domain_map.get(kind)
        if not domain:
            continue
        out.append(
            {
                "opportunity_id": f"operator-{record.get('recorded_at', 'note')}",
                "domain": domain,
                "repository": record.get("repository") or "portfolio",
                "display_name": REPOSITORY_DISPLAY_NAMES.get(
                    str(record.get("repository") or ""), str(record.get("repository") or "Portfolio")
                ),
                "title": record.get("content"),
                "detail": "Operator-recorded evolution note.",
                "source": "operator_note",
                "operator_recorded": True,
                **_priority_score(impact=50, risk=20, effort=35, strategic_value=45, confidence=90),
            }
        )
    return out


def build_cross_repository_product_evolution_intelligence(
    *, session_id: str
) -> CrossRepositoryProductEvolutionIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    operator_records = list_cross_repository_product_evolution_intelligence_records()

    engineering = build_multi_repository_engineering_intelligence(session_id=sid)
    eng_sections = engineering.multi_repository_engineering_intelligence.get("sections") or {}
    health_rows = list(eng_sections.get("engineering_health_scores") or [])
    dependency_map = list(eng_sections.get("cross_repository_dependency_map") or [])

    validation = build_cross_repository_multi_agent_delivery_validation(session_id=sid)
    matrix = list(
        (validation.cross_repository_multi_agent_delivery_validation.get("sections") or {}).get(
            "cross_repository_validation_matrix"
        )
        or []
    )

    generation = build_governed_application_generation(session_id=sid)
    gen_payload = generation.governed_application_generation or {}
    gen_sections = gen_payload.get("sections") or {}
    product_name = str(gen_payload.get("product_name") or "unknown")
    generation_stage = str(gen_payload.get("current_stage") or "unknown")

    opportunities: list[dict[str, Any]] = []
    for repo in PORTFOLIO_REPOSITORIES:
        validation_row = next((r for r in matrix if r.get("repository") == repo), {})
        health_row = next((r for r in health_rows if r.get("repository") == repo), {})
        knowledge_records = list_repository_knowledge_graph_records(repository_id=repo, limit=50)
        opportunities.extend(
            _repo_opportunities(
                repo=repo,
                validation_row=validation_row,
                health_row=health_row,
                knowledge_records=knowledge_records,
            )
        )

    opportunities.extend(_shared_opportunities(matrix=matrix, dependency_map=dependency_map))
    opportunities.extend(_operator_opportunities(operator_records))

    if gen_sections.get("delivery_backlog"):
        opportunities.append(
            {
                "opportunity_id": "governed-generation-delivery-backlog",
                "domain": "feature",
                "repository": "portfolio",
                "display_name": "Portfolio",
                "title": f"Align portfolio evolution with governed generation backlog ({product_name})",
                "detail": f"FIX 250 stage {generation_stage} — review delivery backlog for cross-repo alignment.",
                "source": "fix_250_governed_application_generation",
                **_priority_score(impact=75, risk=30, effort=45, strategic_value=80, confidence=70),
            }
        )

    priority_matrix = _priority_matrix(opportunities=opportunities)
    top_opportunities = priority_matrix[:5]
    human_approved = has_human_evolution_decision_approve(session_id=sid)
    evolution_backlog = _evolution_backlog(opportunities=opportunities)
    backlog_epic_count = len((evolution_backlog[0].get("epics") or []) if evolution_backlog else [])

    sections = {
        "feature_evolution_report": _domain_report(domain="feature", opportunities=opportunities),
        "quality_evolution_report": _domain_report(domain="quality", opportunities=opportunities),
        "architecture_evolution_report": _domain_report(domain="architecture", opportunities=opportunities),
        "operational_evolution_report": _domain_report(domain="operational", opportunities=opportunities),
        "ux_evolution_report": _domain_report(domain="ux", opportunities=opportunities),
        "opportunity_graph": _opportunity_graph(opportunities=opportunities),
        "portfolio_evolution_backlog": evolution_backlog,
        "evolution_priority_matrix": priority_matrix,
        "product_evolution_dashboard": [
            {
                "dashboard_id": "product-evolution-intelligence",
                "top_opportunities": top_opportunities,
                "highest_risk_areas": [o for o in priority_matrix if float(o.get("risk") or 0) >= 50][:5],
                "technical_debt_hotspots": [
                    o for o in opportunities if o.get("domain") == "quality"
                ][:5],
                "architecture_concerns": [
                    o for o in opportunities if o.get("domain") == "architecture"
                ][:5],
                "operational_concerns": [
                    o for o in opportunities if o.get("domain") == "operational"
                ][:5],
                "evolution_backlog_epic_count": backlog_epic_count,
                "human_evolution_decision_approve": human_approved,
                "human_evolution_decision_required": not human_approved,
                "feeds_governed_delivery_pipeline": human_approved,
                "read_only": True,
            }
        ],
        "human_evolution_review": [
            {
                "review_id": "human-evolution-decision",
                "decisions_supported": [
                    "human_evolution_decision_approve",
                    "human_evolution_decision_hold",
                    "human_evolution_decision_reject",
                    "human_evolution_decision_defer",
                ],
                "human_evolution_decision_approve": human_approved,
                "execution_authority": False,
                "read_only": True,
            }
        ],
        "product_evolution_memory": [{**r, "read_only": True} for r in operator_records[-50:]],
        "forbidden_product_evolution_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_PRODUCT_EVOLUTION_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_SCHEMA_VERSION,
        "fix": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_261,
        "execution_performed": EXECUTION_PERFORMED_FIX_261,
        "intelligence_compose_artifacts_only": CROSS_REPOSITORY_PRODUCT_EVOLUTION_COMPOSES_EVIDENCE_ONLY_FIX_261,
        "product_evolution_authority": PRODUCT_EVOLUTION_AUTHORITY_FIX_261,
        "automatic_improvement_enabled": AUTOMATIC_IMPROVEMENT_ENABLED_FIX_261,
        "cross_repo_execution_enabled": CROSS_REPO_EXECUTION_ENABLED_FIX_261,
        "repository_mutation_authority": REPOSITORY_MUTATION_AUTHORITY_FIX_261,
        "trust_mutation_authority": TRUST_MUTATION_AUTHORITY_FIX_261,
        "merge_authority": MERGE_AUTHORITY_FIX_261,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_261,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_261,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_261,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_261,
        "invariant": CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_INVARIANT,
        "session_id": sid,
        "repositories": list(PORTFOLIO_REPOSITORIES),
        "evolution_domains": list(EVOLUTION_DOMAINS),
        "evolution_priority_tiers": list(EVOLUTION_PRIORITY_TIERS),
        "sections": sections,
        "opportunity_count": len(opportunities),
        "operator_record_count": len(operator_records),
        "human_evolution_decision_approve": human_approved,
        "fix_261_certification_requirements": list(FIX_261_CERTIFICATION_REQUIREMENTS),
        "cross_repository_product_evolution_intelligence_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in CROSS_REPOSITORY_PRODUCT_EVOLUTION_INTELLIGENCE_PRINCIPLES
        ],
        "sources": {
            "composes_fix_240_repository_knowledge_graph": True,
            "composes_fix_250_governed_application_generation": True,
            "composes_fix_260_multi_repository_engineering_intelligence": True,
            "composes_fix_189_190_agent_metrics": True,
            "composes_fix_191_cross_repository_validation": True,
            "composes_fix_186_192_194_196_trust_baselines": True,
            "pilot_reexecution_performed": False,
            "code_generation_performed": False,
        },
    }

    return CrossRepositoryProductEvolutionIntelligenceResult(
        ok=True,
        session_id=sid,
        cross_repository_product_evolution_intelligence=payload,
        detail="Cross-repository product evolution intelligence composed from portfolio evidence (evolution ≠ execution).",
    )
