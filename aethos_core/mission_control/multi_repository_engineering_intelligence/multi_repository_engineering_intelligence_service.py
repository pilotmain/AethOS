# SPDX-License-Identifier: Apache-2.0
"""FIX 260 — multi-repository engineering intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Final

from aethos_core.governance.governance_friction_approval_contract import FIX_260_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_contract import (
    CROSS_REPO_AUTHORITY_FIX_260,
    DEPLOY_AUTHORITY_FIX_260,
    ENGINEERING_HEALTH_TIERS,
    EXECUTION_PERFORMED_FIX_260,
    FORBIDDEN_MULTI_REPOSITORY_INTELLIGENCE_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_260,
    GOVERNANCE_MUTATION_PERFORMED_FIX_260,
    MERGE_AUTHORITY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_FIX,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_INVARIANT,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_PRINCIPLES,
    MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_260,
    PORTFOLIO_AUTHORITY_FIX_260,
    PORTFOLIO_REPOSITORIES,
    PROGRAM_DELIVERY_AUTHORITY_FIX_260,
    PROGRAM_DELIVERY_STAGES,
    PROVIDER_MUTATION_AUTHORITY_FIX_260,
    REPOSITORY_DISPLAY_NAMES,
)
from aethos_core.mission_control.multi_repository_engineering_intelligence.multi_repository_engineering_intelligence_store import (
    list_multi_repository_engineering_intelligence_records,
)
from aethos_core.mission_control.repository_knowledge_graph.repository_knowledge_graph_store import (
    list_repository_knowledge_graph_records,
)

_GOVERNED_LIFECYCLE_STAGES: Final = {
    "plan": "FIX 125A",
    "patch": "FIX 125B",
    "verify": "FIX 125C",
    "pr_open": "FIX 125I",
    "merge": "FIX 200",
    "deploy": "FIX 210",
    "monitor": "FIX 220",
    "rollback": "FIX 230",
}

_DEFAULT_ADVISORY_DEPENDENCIES: Final = (
    {
        "link_id": "pilotos-ui-to-aethos-governance-patterns",
        "source_repository": PHASE_2_REPOSITORY_ORDER[0],
        "target_repository": PHASE_1_REPOSITORY,
        "relationship": "advisory",
        "detail": "PilotOS UI delivery patterns reference AethOS governance substrate (no inherited trust).",
        "executable": False,
        "read_only": True,
    },
    {
        "link_id": "atlas-trader-to-aethos-delivery-patterns",
        "source_repository": PHASE_2_REPOSITORY_ORDER[1],
        "target_repository": PHASE_1_REPOSITORY,
        "relationship": "advisory",
        "detail": "Atlas Trader pilot arc should earn independent evidence — not inherit AethOS trust.",
        "executable": False,
        "read_only": True,
    },
    {
        "link_id": "nexora-to-aethos-delivery-patterns",
        "source_repository": PHASE_2_REPOSITORY_ORDER[2],
        "target_repository": PHASE_1_REPOSITORY,
        "relationship": "advisory",
        "detail": "Nexora monorepo pilot should follow independent trust progression.",
        "executable": False,
        "read_only": True,
    },
)


@dataclass(frozen=True)
class MultiRepositoryEngineeringIntelligenceResult:
    ok: bool
    session_id: str
    multi_repository_engineering_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _knowledge_signal(repository: str) -> dict[str, Any]:
    records = list_repository_knowledge_graph_records(repository_id=repository, limit=50)
    kinds = {str(r.get("kind") or "") for r in records}
    return {
        "repository": repository,
        "knowledge_record_count": len(records),
        "discovery_kinds": sorted(k for k in kinds if k),
        "intelligence_depth": "deep"
        if len(records) >= 5
        else "moderate"
        if len(records) >= 2
        else "minimal"
        if records
        else "none",
        "read_only": True,
    }


def _health_tier(score: float, *, trust_state: str) -> str:
    if trust_state == "UNPROVEN" and score < 30:
        return "UNPROVEN"
    if score >= 90:
        return "EXCELLENT"
    if score >= 75:
        return "HEALTHY"
    if score >= 50:
        return "WATCH"
    if score >= 25:
        return "AT_RISK"
    return "UNPROVEN"


def _engineering_health_score(
    *,
    trust_state: str,
    throughput: float | None,
    alignment_score: int | None,
    knowledge_record_count: int,
    pilot_3_complete: bool,
) -> dict[str, Any]:
    base = {
        "UNPROVEN": 15.0,
        "PILOTING": 45.0,
        "TRUST_REVIEW_PENDING": 58.0,
        "CONDITIONALLY_TRUSTED": 78.0,
    }.get(trust_state, 20.0)
    score = base
    if throughput is not None:
        score += min(15.0, float(throughput) * 0.15)
    if alignment_score is not None:
        score += min(10.0, int(alignment_score) * 0.1)
    score += min(10.0, knowledge_record_count * 2.0)
    if pilot_3_complete:
        score += 8.0
    score = max(0.0, min(100.0, round(score, 1)))
    tier = _health_tier(score, trust_state=trust_state)
    return {
        "engineering_health_score": score,
        "engineering_health_tier": tier,
        "advisory_only": True,
        "read_only": True,
    }


def _program_delivery_row(*, validation_row: dict[str, Any]) -> dict[str, Any]:
    progression = dict(validation_row.get("pilot_progression") or {})
    live_stages: list[str] = []
    if progression.get("pilot_1_complete"):
        live_stages.append("plan")
    if progression.get("pilot_2_complete"):
        live_stages.extend(["patch", "verify"])
    if progression.get("pilot_3_complete") or validation_row.get("pr_open_success"):
        live_stages.extend(["pr_open", "merge", "deploy", "monitor", "rollback"])

    governed = {
        stage: {
            "platform_capability": _GOVERNED_LIFECYCLE_STAGES.get(stage),
            "live_evidence": stage in live_stages,
            "authority_required": stage in {"merge", "deploy", "rollback"},
            "read_only": True,
        }
        for stage in PROGRAM_DELIVERY_STAGES
    }
    return {
        "repository": validation_row.get("repository"),
        "display_name": validation_row.get("display_name"),
        "trust_state": validation_row.get("trust_state"),
        "governed_delivery_stages": governed,
        "live_evidence_stages": sorted(set(live_stages)),
        "program_visibility": "proven_end_to_end"
        if progression.get("pilot_3_complete")
        else "alignment_protection_proven"
        if progression.get("pilot_2_complete")
        else "loop_partial"
        if progression.get("pilot_1_complete")
        else "unproven",
        "read_only": True,
    }


def _cross_repo_dependency_map(
    *,
    operator_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    links = [dict(row) for row in _DEFAULT_ADVISORY_DEPENDENCIES]
    for record in operator_records:
        if str(record.get("kind") or "") != "cross_repo_dependency_note":
            continue
        links.append(
            {
                "link_id": f"operator-{record.get('recorded_at', 'note')}",
                "source_repository": record.get("source_repository"),
                "target_repository": record.get("target_repository"),
                "relationship": record.get("relationship") or "advisory",
                "detail": record.get("content"),
                "operator_recorded": True,
                "executable": False,
                "read_only": True,
            }
        )
    return links


def _portfolio_summary(*, repo_health_rows: list[dict[str, Any]]) -> dict[str, Any]:
    scores = [
        float(r.get("engineering_health_score") or 0)
        for r in repo_health_rows
        if r.get("engineering_health_score") is not None
    ]
    trusted = sum(1 for r in repo_health_rows if r.get("trust_state") == "CONDITIONALLY_TRUSTED")
    unproven = sum(1 for r in repo_health_rows if r.get("trust_state") == "UNPROVEN")
    portfolio_score = round(sum(scores) / len(scores), 1) if scores else 0.0
    return {
        "portfolio_engineering_health_score": portfolio_score,
        "portfolio_health_tier": _health_tier(portfolio_score, trust_state="PILOTING"),
        "repositories_tracked": len(repo_health_rows),
        "conditionally_trusted_count": trusted,
        "unproven_count": unproven,
        "cross_repo_authority": False,
        "program_delivery_authority": False,
        "read_only": True,
    }


def build_multi_repository_engineering_intelligence(
    *, session_id: str
) -> MultiRepositoryEngineeringIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    operator_records = list_multi_repository_engineering_intelligence_records()

    validation = build_cross_repository_multi_agent_delivery_validation(session_id=sid)
    matrix = list(
        (validation.cross_repository_multi_agent_delivery_validation.get("sections") or {}).get(
            "cross_repository_validation_matrix"
        )
        or []
    )

    repo_health_rows: list[dict[str, Any]] = []
    program_rows: list[dict[str, Any]] = []
    knowledge_signals: list[dict[str, Any]] = []

    for repo in PORTFOLIO_REPOSITORIES:
        row = next((r for r in matrix if r.get("repository") == repo), None)
        if row is None:
            row = {
                "repository": repo,
                "display_name": REPOSITORY_DISPLAY_NAMES.get(repo, repo),
                "trust_state": "UNPROVEN",
                "throughput_score": None,
                "alignment_score": None,
                "pilot_progression": {},
                "pr_open_success": False,
            }

        knowledge = _knowledge_signal(repo)
        knowledge_signals.append(knowledge)
        progression = dict(row.get("pilot_progression") or {})
        health = _engineering_health_score(
            trust_state=str(row.get("trust_state") or "UNPROVEN"),
            throughput=row.get("throughput_score"),
            alignment_score=row.get("alignment_score"),
            knowledge_record_count=int(knowledge.get("knowledge_record_count") or 0),
            pilot_3_complete=bool(progression.get("pilot_3_complete")),
        )
        repo_health_rows.append(
            {
                "repository": repo,
                "display_name": REPOSITORY_DISPLAY_NAMES.get(repo, repo),
                "trust_state": row.get("trust_state"),
                "throughput_score": row.get("throughput_score"),
                "alignment_score": row.get("alignment_score"),
                **health,
                "read_only": True,
            }
        )
        program_rows.append(_program_delivery_row(validation_row=row))

    portfolio_summary = _portfolio_summary(repo_health_rows=repo_health_rows)
    dependency_map = _cross_repo_dependency_map(operator_records=operator_records)

    sections = {
        "portfolio_engineering_dashboard": [
            {
                "dashboard_id": "portfolio-engineering-intelligence",
                "portfolio_summary": portfolio_summary,
                "repository_health_rows": repo_health_rows,
                "read_only": True,
            }
        ],
        "cross_repository_dependency_map": dependency_map,
        "engineering_health_scores": repo_health_rows,
        "program_delivery_visibility": program_rows,
        "repository_knowledge_signals": knowledge_signals,
        "multi_repo_intelligence_memory": [
            {**r, "read_only": True} for r in operator_records[-50:]
        ],
        "forbidden_intelligence_actions": [
            {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
            for aid, detail in FORBIDDEN_MULTI_REPOSITORY_INTELLIGENCE_ACTIONS
        ],
    }

    payload: dict[str, Any] = {
        "schema_version": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_SCHEMA_VERSION,
        "fix": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_260,
        "execution_performed": EXECUTION_PERFORMED_FIX_260,
        "intelligence_compose_artifacts_only": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_COMPOSES_EVIDENCE_ONLY_FIX_260,
        "portfolio_authority": PORTFOLIO_AUTHORITY_FIX_260,
        "cross_repo_authority": CROSS_REPO_AUTHORITY_FIX_260,
        "program_delivery_authority": PROGRAM_DELIVERY_AUTHORITY_FIX_260,
        "merge_authority": MERGE_AUTHORITY_FIX_260,
        "deploy_authority": DEPLOY_AUTHORITY_FIX_260,
        "provider_mutation_authority": PROVIDER_MUTATION_AUTHORITY_FIX_260,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_260,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_260,
        "invariant": MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_INVARIANT,
        "session_id": sid,
        "repositories": list(PORTFOLIO_REPOSITORIES),
        "engineering_health_tiers": list(ENGINEERING_HEALTH_TIERS),
        "sections": sections,
        "operator_record_count": len(operator_records),
        "fix_260_certification_requirements": list(FIX_260_CERTIFICATION_REQUIREMENTS),
        "multi_repository_engineering_intelligence_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in MULTI_REPOSITORY_ENGINEERING_INTELLIGENCE_PRINCIPLES
        ],
        "sources": {
            "composes_fix_191_cross_repo_validation": True,
            "composes_fix_240_knowledge_signals": True,
            "composes_fix_187_trust_registry_indirectly": True,
            "composes_governed_lifecycle_capabilities_200_230": True,
            "pilot_reexecution_performed": False,
        },
    }

    return MultiRepositoryEngineeringIntelligenceResult(
        ok=True,
        session_id=sid,
        multi_repository_engineering_intelligence=payload,
        detail="Multi-repository engineering intelligence composed from stored evidence (portfolio ≠ authority).",
    )
