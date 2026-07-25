# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_327_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
    AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
    ENTERPRISE_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_327,
    ENTERPRISE_PROGRAM_CORE_PRINCIPLE,
    ENTERPRISE_PROGRAM_INTELLIGENCE_DOMAINS,
    ENTERPRISE_PROGRAM_INTELLIGENCE_FIX,
    ENTERPRISE_PROGRAM_INTELLIGENCE_INVARIANT,
    ENTERPRISE_PROGRAM_INTELLIGENCE_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_327,
    FORBIDDEN_PROGRAM_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_327,
    HUMAN_PROGRAM_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_327,
    PRIVACY_REQUIREMENTS,
    PROGRAM_AUTHORITY_FIX_327,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_evaluator import (
    build_enterprise_program_dashboard,
    build_program_alignment_report,
    build_program_dependency_report,
    build_program_health_report,
    build_program_opportunity_registry,
    build_program_priority_matrix,
    build_program_progress_report,
    build_program_registry,
    build_program_risk_report,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_evidence import (
    collect_enterprise_program_evidence,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_store import (
    has_program_review_decision_approve,
    list_program_review_records,
)


@dataclass(frozen=True)
class EnterpriseProgramIntelligenceResult:
    ok: bool
    session_id: str
    enterprise_program_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_enterprise_program_intelligence(*, session_id: str = "default") -> EnterpriseProgramIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_enterprise_program_evidence(session_id=sid)

    program_registry = build_program_registry(evidence=evidence)
    program_dependency_report = build_program_dependency_report(evidence=evidence, registry=program_registry)
    program_health_report = build_program_health_report(evidence=evidence, registry=program_registry)
    program_progress_report = build_program_progress_report(evidence=evidence, registry=program_registry)
    program_risk_report = build_program_risk_report(evidence=evidence)
    program_alignment_report = build_program_alignment_report(evidence=evidence, registry=program_registry)
    program_opportunity_registry = build_program_opportunity_registry(
        dependency_report=program_dependency_report,
        health_report=program_health_report,
        risk_report=program_risk_report,
        alignment_report=program_alignment_report,
    )
    program_priority_matrix = build_program_priority_matrix(
        registry=program_registry,
        health_report=program_health_report,
        risk_report=program_risk_report,
        alignment_report=program_alignment_report,
        opportunity_registry=program_opportunity_registry,
    )
    enterprise_program_dashboard = build_enterprise_program_dashboard(
        registry=program_registry,
        dependency_report=program_dependency_report,
        health_report=program_health_report,
        progress_report=program_progress_report,
        risk_report=program_risk_report,
        alignment_report=program_alignment_report,
        opportunity_registry=program_opportunity_registry,
        priority_matrix=program_priority_matrix,
    )
    enterprise_program_dashboard["human_program_review_decision_approve"] = has_program_review_decision_approve(
        session_id=sid
    )

    program_review_registry = {
        "records": list_program_review_records(),
        "commands": (
            "program note: ...",
            "program review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "program_registry": [program_registry],
        "program_dependency_report": [program_dependency_report],
        "program_health_report": [program_health_report],
        "program_progress_report": [program_progress_report],
        "program_risk_report": [program_risk_report],
        "program_alignment_report": [program_alignment_report],
        "program_opportunity_registry": [program_opportunity_registry],
        "program_priority_matrix": [program_priority_matrix],
        "enterprise_program_dashboard": [enterprise_program_dashboard],
        "program_review_registry": [program_review_registry],
    }

    board = {
        "schema_version": ENTERPRISE_PROGRAM_INTELLIGENCE_SCHEMA_VERSION,
        "fix": ENTERPRISE_PROGRAM_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": ENTERPRISE_PROGRAM_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_327,
        "execution_performed": EXECUTION_PERFORMED_FIX_327,
        "program_authority": PROGRAM_AUTHORITY_FIX_327,
        "automatic_project_creation_enabled": AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
        "automatic_program_execution_enabled": AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
        "automatic_resource_assignment_enabled": AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
        "automatic_dependency_resolution_enabled": AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
        "enterprise_program_compose_artifacts_only": ENTERPRISE_PROGRAM_COMPOSES_EVIDENCE_ONLY_FIX_327,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_327,
        "domains": list(ENTERPRISE_PROGRAM_INTELLIGENCE_DOMAINS),
        "human_program_review_decision_kinds": list(HUMAN_PROGRAM_REVIEW_DECISION_KINDS),
        "forbidden_program_actions": [label for label, _detail in FORBIDDEN_PROGRAM_ACTIONS],
        "core_principle": ENTERPRISE_PROGRAM_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_327_certification_requirements": list(FIX_327_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return EnterpriseProgramIntelligenceResult(
        ok=True,
        session_id=sid,
        enterprise_program_intelligence=board,
        detail="Enterprise program intelligence composed without program execution authority.",
    )
