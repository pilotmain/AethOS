# SPDX-License-Identifier: Apache-2.0
"""FIX 325 — executive decision intelligence evaluators."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_contract import (
    EXECUTIVE_CORE_PRINCIPLE,
    EXECUTIVE_DECISION_STATUSES,
    EXECUTIVE_OPPORTUNITY_SOURCES,
    EXECUTIVE_RECOMMENDATION_LEVELS,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.executive_decision_intelligence.executive_decision_intelligence_store import (
    classify_executive_decision_status,
)


def _composed_section(evidence: dict[str, Any], fix_key: str, section: str) -> dict[str, Any]:
    payload = evidence.get(fix_key) or {}
    sections = payload.get("sections") or {}
    block = sections.get(section) or [{}]
    return block[0] if block else {}


def build_executive_decision_registry(*, evidence: dict[str, Any]) -> dict[str, Any]:
    records = list(evidence.get("executive_review_records") or [])
    pending: list[dict[str, Any]] = []
    reviewed: list[dict[str, Any]] = []
    deferred: list[dict[str, Any]] = []

    for record in records:
        kind = str(record.get("kind") or "")
        status = classify_executive_decision_status(kind)
        row = {
            "decision_id": f"{kind}-{str(record.get('recorded_at') or 'unknown')}",
            "kind": kind,
            "content": record.get("content"),
            "status": status,
            "session_id": record.get("session_id"),
        }
        if status == "deferred":
            deferred.append(row)
        elif status == "reviewed":
            reviewed.append(row)
        else:
            pending.append(row)

    portfolio = _composed_section(evidence, "fix_324", "strategic_priority_matrix")
    for opp in (portfolio.get("highest_risk_opportunities") or [])[:3]:
        pending.append(
            {
                "decision_id": f"pending-{str(opp.get('opportunity_id') or opp.get('title'))[:32]}",
                "kind": "portfolio_decision_candidate",
                "content": str(opp.get("title") or "Portfolio decision candidate"),
                "status": "pending",
                "source": "FIX 324",
            }
        )

    return {
        "pending_decisions": pending[:12],
        "reviewed_decisions": reviewed[:12],
        "deferred_decisions": deferred[:12],
        "pending_count": len(pending),
        "reviewed_count": len(reviewed),
        "deferred_count": len(deferred),
        "decision_statuses": list(EXECUTIVE_DECISION_STATUSES),
        "cross_tenant_decision_visibility_forbidden": True,
        "validated": bool(pending or reviewed or deferred or portfolio),
    }


def build_decision_opportunity_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    portfolio = _composed_section(evidence, "fix_324", "investment_opportunity_report")
    priority = _composed_section(evidence, "fix_324", "strategic_priority_matrix")
    opportunities = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")

    high_value: list[dict[str, Any]] = []
    for item in portfolio.get("high_value_opportunities") or []:
        high_value.append({**item, "urgency": "medium"})
    for opp in (opportunities.get("opportunities") or [])[:4]:
        if float(opp.get("value") or 0) >= 0.7:
            high_value.append(
                {
                    "title": opp.get("title"),
                    "source": "FIX 324",
                    "urgency": "high" if opp.get("strategic_alignment") == "high" else "medium",
                }
            )

    high_urgency: list[dict[str, Any]] = []
    for opp in (priority.get("highest_risk_opportunities") or [])[:4]:
        high_urgency.append(
            {
                "title": opp.get("title"),
                "source": "FIX 324",
                "urgency": "high",
                "risk_signal": opp.get("risk_signal"),
            }
        )
    for item in portfolio.get("underinvested_areas") or []:
        high_urgency.append({**item, "urgency": "high", "reason": "underinvested"})

    return {
        "sources": ["FIX 324"],
        "high_value_opportunities": high_value[:8],
        "high_urgency_opportunities": high_urgency[:8],
        "validated": bool(high_value or high_urgency),
    }


def build_decision_risk_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    launch_risks = _composed_section(evidence, "fix_309", "launch_risk_registry")
    launch_blockers = _composed_section(evidence, "fix_313", "launch_blocker_registry")
    incident = _composed_section(evidence, "fix_316", "incident_baseline")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    priority = _composed_section(evidence, "fix_324", "strategic_priority_matrix")

    operational = list(launch_blockers.get("blockers") or launch_blockers.get("items") or [])
    operational.extend(incident.get("active_incidents") or incident.get("incidents") or [])
    operational.extend(portfolio_risk.get("operational_risk") or [])

    product = list(launch_risks.get("risks") or launch_risks.get("items") or [])
    product.extend(portfolio_risk.get("product_risk") or [])

    customer = list(portfolio_risk.get("customer_risk") or [])
    commercial = list(portfolio_risk.get("commercial_risk") or [])

    highest_risk_decisions = [
        {
            "title": str(item.get("title") or item),
            "risk_signal": item.get("risk_signal", "elevated"),
            "source": "FIX 324",
        }
        for item in (priority.get("highest_risk_opportunities") or [])[:5]
    ]

    return {
        "sources": ["FIX 309", "FIX 313", "FIX 316", "FIX 324"],
        "operational_risk_signals": operational[:8],
        "product_risk_signals": product[:8],
        "customer_risk_signals": customer[:8],
        "commercial_risk_signals": commercial[:8],
        "highest_risk_decisions": highest_risk_decisions,
        "validated": bool(operational or product or customer or commercial or highest_risk_decisions),
    }


def _recommendation_level(*, value: float, risk_count: int, urgency: str) -> str:
    if risk_count >= 3:
        return "REVIEW"
    if urgency == "high" and value >= 0.75:
        return "ACCELERATE"
    if value >= 0.8:
        return "PRIORITIZE"
    if value < 0.4:
        return "DEFER"
    if risk_count >= 1:
        return "HOLD"
    return "REVIEW"


def build_executive_recommendation_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    improvement = _composed_section(evidence, "fix_317", "improvement_opportunity_registry")
    growth = _composed_section(evidence, "fix_320", "growth_opportunity_registry")
    pmf = _composed_section(evidence, "fix_322", "pmf_opportunity_registry")
    value = _composed_section(evidence, "fix_323", "value_opportunity_registry")
    portfolio = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")
    portfolio_risk = _composed_section(evidence, "fix_324", "portfolio_risk_report")
    opportunity = build_decision_opportunity_report(evidence=evidence)

    risk_count = len(portfolio_risk.get("operational_risk") or []) + len(portfolio_risk.get("product_risk") or [])
    recommendations: list[dict[str, Any]] = []

    def _append_from(source: str, items: list[dict[str, Any]], *, default_value: float) -> None:
        for item in items[:4]:
            title = str(item.get("title") or item.get("name") or "Opportunity")
            val = float(item.get("value") or item.get("priority_score") or default_value)
            urgency = str(item.get("urgency") or "medium")
            level = _recommendation_level(value=val, risk_count=risk_count, urgency=urgency)
            recommendations.append(
                {
                    "title": title,
                    "source": source,
                    "recommendation_level": level,
                    "evidence_summary": f"Composed from {source}",
                    "automatic_decision_execution_forbidden": True,
                }
            )

    _append_from("FIX 317", improvement.get("opportunities") or [], default_value=0.55)
    _append_from("FIX 320", growth.get("opportunities") or [], default_value=0.6)
    _append_from("FIX 322", pmf.get("opportunities") or [], default_value=0.65)
    _append_from("FIX 323", value.get("opportunities") or [], default_value=0.7)
    _append_from("FIX 324", portfolio.get("opportunities") or [], default_value=0.75)

    for item in (opportunity.get("high_urgency_opportunities") or [])[:3]:
        recommendations.append(
            {
                "title": str(item.get("title")),
                "source": "FIX 324 urgency",
                "recommendation_level": "REVIEW",
                "evidence_summary": "High-urgency portfolio signal",
                "automatic_decision_execution_forbidden": True,
            }
        )

    by_level = {level: 0 for level in EXECUTIVE_RECOMMENDATION_LEVELS}
    for rec in recommendations:
        level = str(rec.get("recommendation_level") or "REVIEW")
        if level in by_level:
            by_level[level] += 1

    return {
        "sources": ["FIX 317", "FIX 320", "FIX 322", "FIX 323", "FIX 324"],
        "recommendations": recommendations[:16],
        "recommendation_count": len(recommendations[:16]),
        "recommendation_levels": list(EXECUTIVE_RECOMMENDATION_LEVELS),
        "recommendation_level_counts": by_level,
        "validated": bool(recommendations),
    }


def build_tradeoff_analysis_report(
    *,
    opportunity_report: dict[str, Any],
    risk_report: dict[str, Any],
    recommendation_report: dict[str, Any],
) -> dict[str, Any]:
    tradeoffs: list[dict[str, Any]] = []

    for rec in (recommendation_report.get("recommendations") or [])[:8]:
        title = str(rec.get("title") or "")
        level = str(rec.get("recommendation_level") or "REVIEW")
        value = {"ACCELERATE": 0.9, "PRIORITIZE": 0.8, "REVIEW": 0.6, "HOLD": 0.45, "DEFER": 0.3}.get(level, 0.5)
        effort = {"ACCELERATE": "high", "PRIORITIZE": "medium", "REVIEW": "medium", "HOLD": "low", "DEFER": "low"}.get(
            level, "medium"
        )
        risk = min(1.0, len(risk_report.get("operational_risk_signals") or []) * 0.15 + 0.2)
        confidence = 0.85 if rec.get("source", "").startswith("FIX 324") else 0.72
        tradeoffs.append(
            {
                "title": title,
                "value": value,
                "effort": effort,
                "risk": round(risk, 2),
                "confidence": confidence,
                "recommendation_level": level,
            }
        )

    for item in (opportunity_report.get("high_value_opportunities") or [])[:3]:
        if any(t.get("title") == item.get("title") for t in tradeoffs):
            continue
        tradeoffs.append(
            {
                "title": str(item.get("title")),
                "value": 0.75,
                "effort": "medium",
                "risk": 0.35,
                "confidence": 0.78,
                "recommendation_level": "PRIORITIZE",
            }
        )

    return {
        "tradeoffs": tradeoffs[:12],
        "count": len(tradeoffs[:12]),
        "dimensions": ("value", "effort", "risk", "confidence"),
        "validated": bool(tradeoffs),
    }


def build_executive_alignment_report(*, evidence: dict[str, Any]) -> dict[str, Any]:
    goals = _composed_section(evidence, "fix_290", "business_goal_registry")
    alignment_graph = _composed_section(evidence, "fix_290", "strategic_alignment_graph")
    portfolio_alignment = _composed_section(evidence, "fix_324", "strategic_alignment_report")
    portfolio_value = _composed_section(evidence, "fix_324", "strategic_value_report")
    investment = _composed_section(evidence, "fix_324", "investment_opportunity_report")

    goal_items = list(goals.get("objectives") or goals.get("goals") or [])
    portfolio_goals = list(portfolio_alignment.get("goals") or [])
    aligned_initiatives = list(portfolio_alignment.get("initiatives") or [])

    return {
        "sources": ["FIX 290", "FIX 324"],
        "goal_alignment_score": round(
            min(1.0, (len(goal_items) + len(portfolio_goals)) / 10.0 + 0.4),
            3,
        ),
        "portfolio_alignment_score": round(
            float(portfolio_alignment.get("alignment_nodes") or 0) / 10.0 + 0.5,
            3,
        ),
        "investment_alignment_score": round(
            min(1.0, len(investment.get("high_value_opportunities") or []) / 8.0 + 0.35),
            3,
        ),
        "goals": goal_items[:6] or portfolio_goals[:6],
        "aligned_initiatives": aligned_initiatives[:6],
        "business_value_score": portfolio_value.get("business_value_score", 0),
        "alignment_nodes": alignment_graph.get("node_count", portfolio_alignment.get("alignment_nodes", 0)),
        "validated": bool(goals or portfolio_alignment or investment),
    }


def build_executive_opportunity_registry(
    *,
    opportunity_report: dict[str, Any],
    recommendation_report: dict[str, Any],
    evidence: dict[str, Any],
) -> dict[str, Any]:
    pmf = _composed_section(evidence, "fix_322", "pmf_opportunity_registry")
    value = _composed_section(evidence, "fix_323", "value_opportunity_registry")
    growth = _composed_section(evidence, "fix_320", "growth_opportunity_registry")
    portfolio = _composed_section(evidence, "fix_324", "portfolio_opportunity_registry")

    opportunities: list[dict[str, Any]] = []

    for item in portfolio.get("opportunities") or []:
        opportunities.append({**item, "source_type": "strategic"})
    for item in growth.get("opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"growth-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "source_type": "growth",
                "value": item.get("value", 0.6),
                "automatic_decision_execution_forbidden": True,
            }
        )
    for item in value.get("opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"value-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "source_type": "value",
                "value": item.get("value", 0.65),
                "automatic_decision_execution_forbidden": True,
            }
        )
    for item in pmf.get("opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"pmf-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "source_type": "pmf",
                "value": 0.7 if item.get("impact") == "high" else 0.5,
                "automatic_decision_execution_forbidden": True,
            }
        )

    for item in opportunity_report.get("high_urgency_opportunities") or []:
        opportunities.append(
            {
                "opportunity_id": f"urgent-{str(item.get('title'))[:24]}",
                "title": str(item.get("title")),
                "source_type": "strategic",
                "urgency": "high",
                "automatic_decision_execution_forbidden": True,
            }
        )

    rec_titles = {str(r.get("title")) for r in recommendation_report.get("recommendations") or []}
    for opp in opportunities:
        if str(opp.get("title")) in rec_titles:
            opp["executive_recommended"] = True

    return {
        "opportunities": opportunities[:20],
        "count": len(opportunities[:20]),
        "source_types": list(EXECUTIVE_OPPORTUNITY_SOURCES),
        "core_principle": EXECUTIVE_CORE_PRINCIPLE,
    }


def _decision_priority_score(row: dict[str, Any]) -> float:
    value = float(row.get("value") or row.get("priority_score") or 0.5)
    confidence = float(row.get("confidence") or 0.7)
    leverage = 0.3 if row.get("executive_recommended") or row.get("recommendation_level") in {
        "ACCELERATE",
        "PRIORITIZE",
    } else 0.0
    risk_penalty = 0.5 if row.get("risk_signal") else 0.0
    return round(value * 3.0 + confidence * 2.0 + leverage - risk_penalty, 3)


def build_executive_priority_matrix(
    *,
    registry: dict[str, Any],
    recommendation_report: dict[str, Any],
    risk_report: dict[str, Any],
    tradeoff_report: dict[str, Any],
) -> dict[str, Any]:
    ranked: list[dict[str, Any]] = []

    for rec in recommendation_report.get("recommendations") or []:
        ranked.append(
            {
                **rec,
                "value": {"ACCELERATE": 0.9, "PRIORITIZE": 0.85, "REVIEW": 0.6, "HOLD": 0.45, "DEFER": 0.3}.get(
                    str(rec.get("recommendation_level")), 0.5
                ),
                "priority_score": _decision_priority_score(rec),
            }
        )

    for opp in registry.get("opportunities") or []:
        if any(r.get("title") == opp.get("title") for r in ranked):
            continue
        ranked.append({**opp, "priority_score": _decision_priority_score(opp)})

    ranked.sort(key=lambda row: row.get("priority_score", 0), reverse=True)

    highest_value = sorted(ranked, key=lambda row: float(row.get("value") or 0), reverse=True)[:5]
    highest_risk = [
        {
            "title": str(item.get("title") or item),
            "risk_signal": "elevated",
            "priority_score": 8.5,
            "automatic_decision_execution_forbidden": True,
        }
        for item in (risk_report.get("highest_risk_decisions") or [])[:5]
    ]
    highest_leverage = [row for row in ranked if row.get("recommendation_level") in {"ACCELERATE", "PRIORITIZE"}][:5]
    if not highest_leverage:
        highest_leverage = ranked[:5]

    return {
        "ranked_decisions": ranked[:12],
        "highest_value_decisions": highest_value,
        "highest_risk_decisions": highest_risk,
        "highest_leverage_decisions": highest_leverage,
        "automatic_decision_execution_forbidden": True,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
    }


def build_executive_decision_dashboard(
    *,
    decision_registry: dict[str, Any],
    opportunity_report: dict[str, Any],
    risk_report: dict[str, Any],
    recommendation_report: dict[str, Any],
    tradeoff_report: dict[str, Any],
    alignment_report: dict[str, Any],
    opportunity_registry: dict[str, Any],
    priority_matrix: dict[str, Any],
) -> dict[str, Any]:
    top = (priority_matrix.get("ranked_decisions") or [{}])[0]
    return {
        "pending_decision_count": decision_registry.get("pending_count", 0),
        "reviewed_decision_count": decision_registry.get("reviewed_count", 0),
        "deferred_decision_count": decision_registry.get("deferred_count", 0),
        "high_value_opportunity_count": len(opportunity_report.get("high_value_opportunities") or []),
        "high_urgency_opportunity_count": len(opportunity_report.get("high_urgency_opportunities") or []),
        "highest_risk_decision_count": len(risk_report.get("highest_risk_decisions") or []),
        "recommendation_count": recommendation_report.get("recommendation_count", 0),
        "tradeoff_count": tradeoff_report.get("count", 0),
        "goal_alignment_score": alignment_report.get("goal_alignment_score", 0),
        "executive_opportunity_count": opportunity_registry.get("count", 0),
        "top_priority_decision": top,
        "top_recommendation_level": top.get("recommendation_level", "REVIEW"),
        "core_principle": EXECUTIVE_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "automatic_decision_execution_forbidden": True,
    }
