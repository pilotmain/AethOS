# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_328_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
    AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
    AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
    EXECUTION_PERFORMED_FIX_328,
    FORBIDDEN_ORGANIZATIONAL_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_328,
    HUMAN_ORGANIZATIONAL_REVIEW_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_328,
    ORGANIZATIONAL_AUTHORITY_FIX_328,
    ORGANIZATIONAL_CORE_PRINCIPLE,
    ORGANIZATIONAL_EFFECTIVENESS_COMPOSES_EVIDENCE_ONLY_FIX_328,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_DOMAINS,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_FIX,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_INVARIANT,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_SCHEMA_VERSION,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_evaluator import (
    build_coordination_intelligence_report,
    build_decision_velocity_report,
    build_governance_friction_report,
    build_organizational_capacity_report,
    build_organizational_effectiveness_dashboard,
    build_organizational_effectiveness_scorecard,
    build_organizational_opportunity_registry,
    build_organizational_risk_report,
    build_organizational_structure_registry,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_evidence import (
    collect_organizational_effectiveness_evidence,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_store import (
    has_organizational_review_decision_approve,
    list_organizational_review_records,
)


@dataclass(frozen=True)
class OrganizationalEffectivenessIntelligenceResult:
    ok: bool
    session_id: str
    organizational_effectiveness_intelligence: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_organizational_effectiveness_intelligence(
    *, session_id: str = "default"
) -> OrganizationalEffectivenessIntelligenceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_organizational_effectiveness_evidence(session_id=sid)

    organizational_structure_registry = build_organizational_structure_registry(evidence=evidence)
    governance_friction_report = build_governance_friction_report(evidence=evidence)
    coordination_intelligence_report = build_coordination_intelligence_report(evidence=evidence)
    organizational_capacity_report = build_organizational_capacity_report(evidence=evidence)
    decision_velocity_report = build_decision_velocity_report(evidence=evidence)
    organizational_risk_report = build_organizational_risk_report(evidence=evidence)
    program_dashboard = (evidence.get("fix_327") or {}).get("sections", {}).get("enterprise_program_dashboard", [{}])
    program_dashboard_row = program_dashboard[0] if program_dashboard else {}
    organizational_opportunity_registry = build_organizational_opportunity_registry(
        friction_report=governance_friction_report,
        coordination_report=coordination_intelligence_report,
        capacity_report=organizational_capacity_report,
        risk_report=organizational_risk_report,
    )
    organizational_effectiveness_scorecard = build_organizational_effectiveness_scorecard(
        friction_report=governance_friction_report,
        coordination_report=coordination_intelligence_report,
        capacity_report=organizational_capacity_report,
        velocity_report=decision_velocity_report,
        risk_report=organizational_risk_report,
        program_dashboard=program_dashboard_row,
    )
    organizational_effectiveness_dashboard = build_organizational_effectiveness_dashboard(
        structure_registry=organizational_structure_registry,
        friction_report=governance_friction_report,
        coordination_report=coordination_intelligence_report,
        capacity_report=organizational_capacity_report,
        velocity_report=decision_velocity_report,
        risk_report=organizational_risk_report,
        opportunity_registry=organizational_opportunity_registry,
        scorecard=organizational_effectiveness_scorecard,
    )
    organizational_effectiveness_dashboard["human_organizational_review_decision_approve"] = (
        has_organizational_review_decision_approve(session_id=sid)
    )

    organizational_review_registry = {
        "records": list_organizational_review_records(),
        "commands": (
            "organization note: ...",
            "organization review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "organizational_structure_registry": [organizational_structure_registry],
        "governance_friction_report": [governance_friction_report],
        "coordination_intelligence_report": [coordination_intelligence_report],
        "organizational_capacity_report": [organizational_capacity_report],
        "decision_velocity_report": [decision_velocity_report],
        "organizational_risk_report": [organizational_risk_report],
        "organizational_opportunity_registry": [organizational_opportunity_registry],
        "organizational_effectiveness_scorecard": [organizational_effectiveness_scorecard],
        "organizational_effectiveness_dashboard": [organizational_effectiveness_dashboard],
        "organizational_review_registry": [organizational_review_registry],
    }

    board = {
        "schema_version": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_SCHEMA_VERSION,
        "fix": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_328,
        "execution_performed": EXECUTION_PERFORMED_FIX_328,
        "organizational_authority": ORGANIZATIONAL_AUTHORITY_FIX_328,
        "automatic_role_changes_enabled": AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
        "automatic_governance_changes_enabled": AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
        "automatic_resource_reallocation_enabled": AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
        "automatic_organizational_changes_enabled": AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
        "organizational_effectiveness_compose_artifacts_only": ORGANIZATIONAL_EFFECTIVENESS_COMPOSES_EVIDENCE_ONLY_FIX_328,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_328,
        "domains": list(ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_DOMAINS),
        "human_organizational_review_decision_kinds": list(HUMAN_ORGANIZATIONAL_REVIEW_DECISION_KINDS),
        "forbidden_organizational_actions": [label for label, _detail in FORBIDDEN_ORGANIZATIONAL_ACTIONS],
        "core_principle": ORGANIZATIONAL_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_328_certification_requirements": list(FIX_328_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return OrganizationalEffectivenessIntelligenceResult(
        ok=True,
        session_id=sid,
        organizational_effectiveness_intelligence=board,
        detail="Organizational effectiveness intelligence composed without organizational authority.",
    )
