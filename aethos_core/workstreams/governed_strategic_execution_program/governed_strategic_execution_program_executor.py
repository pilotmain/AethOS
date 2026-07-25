# SPDX-License-Identifier: Apache-2.0
"""FIX 359 / WORKSTREAM_H2 — governed strategic execution executor."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_contract import (
    APPROVED_GROWTH_PATHS,
    EXECUTION_READINESS_LEVELS,
    RISK_PLANNING_FIX_MODULES,
    STRATEGIC_INITIATIVE_MIN_SIZE,
)
from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
    has_strategic_execution_review_approve,
    list_strategic_initiative_registry_entries,
    register_strategic_initiative,
)
from aethos_core.workstreams.strategic_direction_next_growth_decision_program.strategic_direction_next_growth_decision_program_executor import (
    build_growth_path_report,
    build_strategic_tradeoff_report,
    compute_strategic_direction_metrics,
)

INITIATIVE_WORKSTREAM_MAP: dict[str, tuple[str, ...]] = {
    "customer_acquisition_expansion": ("WORKSTREAM_F1", "WORKSTREAM_F2", "WORKSTREAM_G2"),
    "enterprise_expansion": ("WORKSTREAM_G1", "WORKSTREAM_G4", "WORKSTREAM_F7"),
    "self_serve_expansion": ("FIX 301", "WORKSTREAM_G2", "WORKSTREAM_G3"),
    "partner_expansion": ("WORKSTREAM_D1", "WORKSTREAM_D2", "ET4"),
}

INITIATIVE_OBJECTIVE_MAP: dict[str, tuple[str, ...]] = {
    "customer_acquisition_expansion": ("growth_objective", "customer_objective"),
    "enterprise_expansion": ("platform_objective", "customer_objective"),
    "self_serve_expansion": ("growth_objective", "platform_objective"),
    "partner_expansion": ("platform_objective", "growth_objective"),
}


def _parse_kv_blob(blob: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for match in re.finditer(r"(\w+)\s*=\s*([^,]+?)(?=,\s*\w+\s*=|$)", blob):
        out[match.group(1).lower()] = match.group(2).strip()
    return out


def _initiative_entries(*, program_session_id: str) -> list[dict[str, Any]]:
    return [
        row
        for row in list_strategic_initiative_registry_entries()
        if str(row.get("program_session_id") or program_session_id) == program_session_id
    ]


def _normalize_growth_path(path: str | None) -> str:
    raw = str(path or "customer_acquisition_expansion").strip().lower()
    if raw in APPROVED_GROWTH_PATHS:
        return raw
    return "customer_acquisition_expansion"


def build_strategic_initiative_registry(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    h1_metrics = compute_strategic_direction_metrics(program_session_id=program_session_id)
    growth = build_growth_path_report(program_session_id=program_session_id)
    approved_paths = sorted({str(i.get("growth_path") or "") for i in initiatives if i.get("growth_path")})

    return {
        "registry_id": "strategic-initiative-registry",
        "program_session_id": program_session_id,
        "initiative_count": len(initiatives),
        "minimum_initiative_count": STRATEGIC_INITIATIVE_MIN_SIZE,
        "initiatives": initiatives,
        "approved_growth_paths": approved_paths,
        "recommended_path_from_h1": growth.get("highest_opportunity_path"),
        "leading_outcome_from_h1": h1_metrics.get("leading_outcome_category"),
        "workstream_h1_reference": {"workstream": "WORKSTREAM_H1", "composed_read_only": True},
        "read_only": True,
    }


def build_initiative_decomposition_report(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    decompositions: list[dict[str, Any]] = []

    for initiative in initiatives:
        growth_path = _normalize_growth_path(str(initiative.get("growth_path") or ""))
        workstreams = INITIATIVE_WORKSTREAM_MAP.get(growth_path, ("WORKSTREAM_F1",))
        objectives = INITIATIVE_OBJECTIVE_MAP.get(growth_path, ("growth_objective",))
        decompositions.append(
            {
                "initiative_id": initiative.get("initiative_id"),
                "growth_path": growth_path,
                "objective": initiative.get("objective"),
                "success_criteria": initiative.get("success_criteria") or "measurable adoption and delivery outcomes",
                "objective_types": list(objectives),
                "execution_workstreams": list(workstreams),
                "planning_only": True,
            }
        )

    return {
        "report_id": "initiative-decomposition-report",
        "program_session_id": program_session_id,
        "decompositions": decompositions,
        "initiative_decomposition_demonstrated": len(decompositions) >= STRATEGIC_INITIATIVE_MIN_SIZE,
        "project_creation_performed": False,
        "read_only": True,
    }


def build_initiative_dependency_report(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    dependencies: list[dict[str, Any]] = []

    for initiative in initiatives:
        growth_path = _normalize_growth_path(str(initiative.get("growth_path") or ""))
        platform_deps = ["ET1", "ET5", "FIX 330"]
        provider_deps = ["Railway/Vercel", "ET4"]
        customer_deps = ["F1 delivery proof", "F2 adoption metrics"]
        governance_deps = ["Human review approve", "Governance friction contract"]

        if growth_path == "enterprise_expansion":
            platform_deps.extend(["G1 evidence maturity", "G4 readiness audit"])
            governance_deps.extend(["Trust review path", "FIX 307 audit portal"])
        elif growth_path == "partner_expansion":
            provider_deps.extend(["D1 provider expansion", "D2 multi-cloud proof"])
        elif growth_path == "self_serve_expansion":
            platform_deps.extend(["FIX 301 onboarding", "FIX 320 adoption intelligence"])
            customer_deps.append("Self-serve activation funnel")

        dependencies.append(
            {
                "initiative_id": initiative.get("initiative_id"),
                "platform_dependencies": platform_deps,
                "provider_dependencies": provider_deps,
                "customer_dependencies": customer_deps,
                "governance_dependencies": governance_deps,
                "dependency_count": len(platform_deps) + len(provider_deps) + len(customer_deps) + len(governance_deps),
            }
        )

    total_deps = sum(int(d.get("dependency_count") or 0) for d in dependencies)
    return {
        "report_id": "initiative-dependency-report",
        "program_session_id": program_session_id,
        "initiative_dependencies": dependencies,
        "total_dependency_count": total_deps,
        "dependency_analysis_demonstrated": total_deps > 0,
        "read_only": True,
    }


def build_initiative_resource_planning_report(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    tradeoffs = build_strategic_tradeoff_report(program_session_id=program_session_id)
    plans: list[dict[str, Any]] = []

    for initiative in initiatives:
        growth_path = _normalize_growth_path(str(initiative.get("growth_path") or ""))
        matching = next(
            (t for t in tradeoffs.get("tradeoffs") or [] if growth_path.startswith("customer") and t.get("outcome_category") == "option_a_customer_growth"),
            {},
        )
        if growth_path == "enterprise_expansion":
            matching = next(
                (t for t in tradeoffs.get("tradeoffs") or [] if t.get("outcome_category") == "option_d_enterprise_expansion"),
                {},
            )
        effort = float(matching.get("effort") or 0.5)
        plans.append(
            {
                "initiative_id": initiative.get("initiative_id"),
                "execution_effort_estimate": round(effort, 3),
                "review_effort_estimate": round(min(1.0, effort * 0.4), 3),
                "operational_effort_estimate": round(min(1.0, effort * 0.6), 3),
                "budget_allocation_performed": False,
                "advisory_only": True,
            }
        )

    return {
        "report_id": "initiative-resource-planning-report",
        "program_session_id": program_session_id,
        "resource_plans": plans,
        "resource_planning_demonstrated": bool(plans),
        "resource_commitment_performed": False,
        "read_only": True,
    }


def build_initiative_risk_planning_report(*, program_session_id: str) -> dict[str, Any]:
    tradeoffs = build_strategic_tradeoff_report(program_session_id=program_session_id)
    execution_risk = float(tradeoffs.get("execution_risk_score") or 0)
    confidence = float(tradeoffs.get("confidence_score") or 0)

    fix_modules = {
        "FIX 309": {
            "module": "FIX 309",
            "focus": "saas_launch_readiness_assessment",
            "launch_risk_reference": execution_risk,
            "read_only": True,
        },
        "FIX 313": {
            "module": "FIX 313",
            "focus": "launch_operations_center",
            "operational_risk_reference": execution_risk,
            "read_only": True,
        },
        "FIX 324": {
            "module": "FIX 324",
            "focus": "strategic_portfolio_intelligence",
            "portfolio_risk_reference": execution_risk,
            "read_only": True,
        },
        "FIX 325": {
            "module": "FIX 325",
            "focus": "executive_decision_intelligence",
            "decision_confidence_reference": confidence,
            "read_only": True,
        },
    }

    return {
        "report_id": "initiative-risk-planning-report",
        "program_session_id": program_session_id,
        "risk_planning_fix_modules": list(RISK_PLANNING_FIX_MODULES),
        "fix_module_references": [fix_modules[fix_id] for fix_id in RISK_PLANNING_FIX_MODULES],
        "execution_risk_score": execution_risk,
        "confidence_score": confidence,
        "risk_planning_demonstrated": True,
        "initiative_launch_performed": False,
        "read_only": True,
    }


def build_initiative_governance_readiness_report(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    approved = has_strategic_execution_review_approve(program_session_id=program_session_id)
    readiness_items: list[dict[str, Any]] = []

    for initiative in initiatives:
        readiness_items.append(
            {
                "initiative_id": initiative.get("initiative_id"),
                "approvals_required": [
                    "strategic_execution_review_approve",
                    "governance_friction_review",
                    "human_execution_decision",
                ],
                "trust_impacts": ["Advisory trust boundary review — no trust promotion"],
                "review_paths": ["Mission Control human review", "ET1–ET5 governance gates"],
                "execution_gates": ["ET1", "ET2", "ET3", "ET4", "ET5"],
                "governance_bypass_performed": False,
            }
        )

    governance_score = round(
        0.5 + (0.3 if readiness_items else 0) + (0.2 if approved else 0),
        3,
    )

    return {
        "report_id": "initiative-governance-readiness-report",
        "program_session_id": program_session_id,
        "governance_readiness_items": readiness_items,
        "governance_readiness_score": governance_score,
        "governance_readiness_demonstrated": governance_score >= 0.5,
        "trust_promotion_performed": False,
        "read_only": True,
    }


def build_strategic_execution_opportunity_registry(*, program_session_id: str) -> dict[str, Any]:
    dependencies = build_initiative_dependency_report(program_session_id=program_session_id)
    decomposition = build_initiative_decomposition_report(program_session_id=program_session_id)
    governance = build_initiative_governance_readiness_report(program_session_id=program_session_id)

    execution_opportunities: list[dict[str, Any]] = []
    sequencing_opportunities: list[dict[str, Any]] = []
    dependency_reduction: list[dict[str, Any]] = []

    for item in decomposition.get("decompositions") or []:
        execution_opportunities.append(
            {
                "initiative_id": item.get("initiative_id"),
                "opportunity": "Sequence ET1–ET5 proof before scale-out",
                "advisory_only": True,
            }
        )

    for dep in dependencies.get("initiative_dependencies") or []:
        if int(dep.get("dependency_count") or 0) > 10:
            dependency_reduction.append(
                {
                    "initiative_id": dep.get("initiative_id"),
                    "opportunity": "Reduce cross-provider dependencies before initiative launch",
                    "advisory_only": True,
                }
            )
        sequencing_opportunities.append(
            {
                "initiative_id": dep.get("initiative_id"),
                "opportunity": "Complete governance readiness before execution planning sign-off",
                "advisory_only": True,
            }
        )

    if float(governance.get("governance_readiness_score") or 0) < 0.8:
        sequencing_opportunities.append(
            {
                "opportunity": "Establish human review path before execution readiness claim",
                "advisory_only": True,
            }
        )

    opportunities = execution_opportunities + sequencing_opportunities + dependency_reduction
    return {
        "registry_id": "strategic-execution-opportunity-registry",
        "program_session_id": program_session_id,
        "opportunity_count": len(opportunities),
        "execution_opportunities": execution_opportunities,
        "sequencing_opportunities": sequencing_opportunities,
        "dependency_reduction_opportunities": dependency_reduction,
        "execution_authority_granted": False,
        "read_only": True,
    }


def _execution_readiness_level(
    *,
    program_session_id: str,
    execution_readiness_score: float,
) -> str:
    if has_strategic_execution_review_approve(program_session_id=program_session_id):
        return "approved"
    if execution_readiness_score >= 0.75:
        return "ready"
    if execution_readiness_score >= 0.55:
        return "governed"
    if execution_readiness_score >= 0.35:
        return "planned"
    return "concept"


def compute_strategic_execution_metrics(*, program_session_id: str) -> dict[str, Any]:
    initiatives = _initiative_entries(program_session_id=program_session_id)
    dependencies = build_initiative_dependency_report(program_session_id=program_session_id)
    governance = build_initiative_governance_readiness_report(program_session_id=program_session_id)
    h1_metrics = compute_strategic_direction_metrics(program_session_id=program_session_id)
    decomposition = build_initiative_decomposition_report(program_session_id=program_session_id)

    initiative_count = len(initiatives) or 1
    initiative_readiness = round(
        min(1.0, initiative_count / STRATEGIC_INITIATIVE_MIN_SIZE)
        * (1.0 if decomposition.get("initiative_decomposition_demonstrated") else 0.5),
        3,
    )
    total_deps = int(dependencies.get("total_dependency_count") or 0)
    dependency_complexity = round(min(1.0, total_deps / max(initiative_count * 8, 1)), 3)
    governance_readiness = float(governance.get("governance_readiness_score") or 0)
    strategic_leverage = float(h1_metrics.get("strategic_leverage_score") or 0)

    execution_readiness = round(
        (
            initiative_readiness
            + (1.0 - dependency_complexity * 0.5)
            + governance_readiness
            + strategic_leverage
        )
        / 4,
        3,
    )

    return {
        "initiative_readiness_score": initiative_readiness,
        "dependency_complexity_score": dependency_complexity,
        "governance_readiness_score": governance_readiness,
        "execution_readiness_score": execution_readiness,
        "strategic_leverage_score": strategic_leverage,
        "execution_readiness_level": _execution_readiness_level(
            program_session_id=program_session_id,
            execution_readiness_score=execution_readiness,
        ),
        "execution_readiness_levels": list(EXECUTION_READINESS_LEVELS),
        "read_only": True,
    }


def register_strategic_initiative_from_text(*, program_session_id: str, body: str) -> dict[str, Any]:
    kv = _parse_kv_blob(body)
    initiative_id = kv.get("initiative_id") or kv.get("initiative") or (
        f"initiative-{len(_initiative_entries(program_session_id=program_session_id)) + 1}"
    )
    entry = register_strategic_initiative(
        entry={
            "initiative_id": initiative_id,
            "program_session_id": program_session_id,
            "growth_path": _normalize_growth_path(kv.get("growth_path") or kv.get("path")),
            "objective": kv.get("objective") or "Translate approved strategic direction into governed execution",
            "success_criteria": kv.get("success_criteria") or "measurable delivery and adoption outcomes",
            "approved_by_h1": kv.get("approved_by_h1", "").lower() == "true",
        }
    )
    from aethos_core.workstreams.governed_strategic_execution_program.governed_strategic_execution_program_store import (
        append_strategic_execution_record,
    )

    append_strategic_execution_record(
        session_id=program_session_id,
        kind="strategic_initiative_entry",
        content=body,
        metadata=entry,
    )
    return entry
