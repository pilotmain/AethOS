# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard service."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_330_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    AUTOMATIC_DECISION_ENABLED_FIX_330,
    AUTOMATIC_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
    EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
    EXECUTIVE_DASHBOARD_COMPOSES_EVIDENCE_ONLY_FIX_330,
    EXECUTIVE_DASHBOARD_CORE_PRINCIPLE,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_INVARIANT,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_330,
    FORBIDDEN_DASHBOARD_ACTIONS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_330,
    HUMAN_DASHBOARD_DECISION_KINDS,
    MUTATION_PERFORMED_FIX_330,
    PRIVACY_REQUIREMENTS,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_evaluator import (
    build_commercial_panel,
    build_customer_panel,
    build_executive_operating_system_dashboard,
    build_executive_summary_panel,
    build_operations_panel,
    build_organization_panel,
    build_portfolio_panel,
    build_program_panel,
    build_strategy_panel,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_evidence import (
    collect_executive_operating_system_dashboard_evidence,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_store import (
    has_dashboard_review_decision_approve,
    list_dashboard_review_records,
)


@dataclass(frozen=True)
class ExecutiveOperatingSystemDashboardResult:
    ok: bool
    session_id: str
    executive_operating_system_dashboard: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def build_executive_operating_system_dashboard_board(*, session_id: str = "default") -> ExecutiveOperatingSystemDashboardResult:
    sid = (session_id or "default").strip()[:64] or "default"
    evidence = collect_executive_operating_system_dashboard_evidence(session_id=sid)

    executive_summary_panel = build_executive_summary_panel(evidence=evidence)
    strategy_panel = build_strategy_panel(evidence=evidence)
    program_panel = build_program_panel(evidence=evidence)
    organization_panel = build_organization_panel(evidence=evidence)
    customer_panel = build_customer_panel(evidence=evidence)
    operations_panel = build_operations_panel(evidence=evidence)
    commercial_panel = build_commercial_panel(evidence=evidence)
    portfolio_panel = build_portfolio_panel(evidence=evidence)
    executive_dashboard = build_executive_operating_system_dashboard(
        summary_panel=executive_summary_panel,
        strategy_panel=strategy_panel,
        program_panel=program_panel,
        organization_panel=organization_panel,
        customer_panel=customer_panel,
        operations_panel=operations_panel,
        commercial_panel=commercial_panel,
        portfolio_panel=portfolio_panel,
    )
    executive_dashboard["human_dashboard_review_decision_approve"] = has_dashboard_review_decision_approve(
        session_id=sid
    )

    executive_dashboard_review_registry = {
        "records": list_dashboard_review_records(),
        "commands": (
            "dashboard note: ...",
            "dashboard review approve|hold|reject|defer: ...",
        ),
        "record_only": True,
    }

    sections = {
        "executive_summary_panel": [executive_summary_panel],
        "strategy_panel": [strategy_panel],
        "program_panel": [program_panel],
        "organization_panel": [organization_panel],
        "customer_panel": [customer_panel],
        "operations_panel": [operations_panel],
        "commercial_panel": [commercial_panel],
        "portfolio_panel": [portfolio_panel],
        "executive_operating_system_dashboard": [executive_dashboard],
        "executive_dashboard_review_registry": [executive_dashboard_review_registry],
    }

    board = {
        "schema_version": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_SCHEMA_VERSION,
        "fix": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_FIX,
        "exported_at": _exported_at(),
        "session_id": sid,
        "invariant": EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_INVARIANT,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_330,
        "execution_performed": EXECUTION_PERFORMED_FIX_330,
        "executive_dashboard_authority": EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
        "automatic_execution_enabled": AUTOMATIC_EXECUTION_ENABLED_FIX_330,
        "automatic_decision_enabled": AUTOMATIC_DECISION_ENABLED_FIX_330,
        "automatic_strategy_execution_enabled": AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
        "automatic_operational_execution_enabled": AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
        "executive_dashboard_compose_artifacts_only": EXECUTIVE_DASHBOARD_COMPOSES_EVIDENCE_ONLY_FIX_330,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_330,
        "domains": list(EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS),
        "human_dashboard_decision_kinds": list(HUMAN_DASHBOARD_DECISION_KINDS),
        "forbidden_dashboard_actions": [label for label, _detail in FORBIDDEN_DASHBOARD_ACTIONS],
        "core_principle": EXECUTIVE_DASHBOARD_CORE_PRINCIPLE,
        "privacy_requirements": list(PRIVACY_REQUIREMENTS),
        "fix_330_certification_requirements": list(FIX_330_CERTIFICATION_REQUIREMENTS),
        "sources": evidence.get("sources_ok") or {},
        "sections": sections,
    }

    return ExecutiveOperatingSystemDashboardResult(
        ok=True,
        session_id=sid,
        executive_operating_system_dashboard=board,
        detail="Executive operating system dashboard composed without executive authority.",
    )
