# SPDX-License-Identifier: Apache-2.0
"""FIX 327 — enterprise program intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_contract import (
    AUTOMATIC_DEPENDENCY_RESOLUTION_ENABLED_FIX_327,
    AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327,
    AUTOMATIC_PROJECT_CREATION_ENABLED_FIX_327,
    AUTOMATIC_RESOURCE_ASSIGNMENT_ENABLED_FIX_327,
    ENTERPRISE_PROGRAM_INTELLIGENCE_DOMAINS,
    ENTERPRISE_PROGRAM_INTELLIGENCE_ROUTE_ID,
    PROGRAM_AUTHORITY_FIX_327,
    PROGRAM_ENTITY_TYPES,
    PROGRAM_HEALTH_STATUSES,
    PROGRAM_OPPORTUNITY_TYPES,
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
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_intent import (
    parse_enterprise_program_intelligence_intent,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_router import (
    route_enterprise_program_intelligence,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service import (
    build_enterprise_program_intelligence,
)
from aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_store import (
    append_program_review_record,
    clear_program_review_records_for_tests,
    list_program_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "epi-327",
    "sources_ok": {f"fix_{n}": True for n in (290, 309, 313, 316, 324, 325, 326)},
    "fix_290": {
        "sections": {
            "project_portfolio_registry": [{"projects": ["Onboarding automation", "Portfolio intelligence"]}],
            "product_portfolio_registry": [{"products": ["Mission Control", "Atlas Trader"]}],
            "business_goal_registry": [{"objectives": ["Accelerate platform adoption"]}],
        }
    },
    "fix_309": {
        "sections": {
            "launch_risk_registry": [{"risks": ["Incomplete security checklist"]}],
        }
    },
    "fix_313": {
        "sections": {
            "launch_blocker_registry": [{"blockers": ["Pending launch review"]}],
        }
    },
    "fix_316": {
        "sections": {
            "platform_health_baseline": [{"status": "HEALTHY"}],
            "customer_health_baseline": [{"status": "STABLE"}],
        }
    },
    "fix_324": {
        "sections": {
            "portfolio_asset_registry": [
                {
                    "assets": [
                        {"asset_id": "product-mc", "name": "Mission Control", "asset_type": "product"},
                    ]
                }
            ],
            "strategic_value_report": [{"business_value_score": 0.75}],
            "portfolio_risk_report": [
                {
                    "operational_risk": ["Pending launch review"],
                    "product_risk": ["Incomplete security checklist"],
                }
            ],
            "strategic_alignment_report": [{"goals": ["Accelerate platform adoption"], "alignment_nodes": 5}],
            "portfolio_opportunity_registry": [
                {"opportunities": [{"title": "Accelerate workflows", "opportunity_type": "growth"}]}
            ],
        }
    },
    "fix_325": {
        "sections": {
            "executive_decision_dashboard": [{"highest_risk_decision_count": 1, "recommendation_count": 3}],
        }
    },
    "fix_326": {
        "sections": {
            "strategic_plan_registry": [
                {
                    "plans": [
                        {
                            "plan_id": "plan-balanced",
                            "scenario": "Balanced growth",
                            "scenario_type": "balanced_growth",
                            "assumptions": ["Human plan approval preserved"],
                        }
                    ]
                }
            ],
            "strategic_planning_dashboard": [{"generated_plan_count": 5}],
            "strategic_comparison_matrix": [
                {"strongest_plan": {"scenario": "Balanced growth", "comparison_score": 8.1}}
            ],
            "strategic_risk_forecast": [{"execution_risks": ["Address portfolio risk before acceleration"]}],
        }
    },
    "program_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_service.collect_enterprise_program_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.enterprise_program_intelligence.enterprise_program_intelligence_evidence.collect_enterprise_program_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_program_review_records_for_tests()
    yield
    clear_program_review_records_for_tests()


def test_enterprise_program_domains_and_authority_flags():
    result = build_enterprise_program_intelligence(session_id="epi-327")
    board = result.enterprise_program_intelligence
    assert board["program_authority"] is False
    assert board["automatic_project_creation_enabled"] is False
    assert board["automatic_program_execution_enabled"] is False
    assert board["automatic_resource_assignment_enabled"] is False
    assert board["automatic_dependency_resolution_enabled"] is False
    for key in ENTERPRISE_PROGRAM_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_program_registry_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    assert registry["count"] >= 4
    assert set(registry["entity_types"]) == set(PROGRAM_ENTITY_TYPES)
    assert registry["cross_tenant_program_visibility_forbidden"] is True


def test_dependency_intelligence_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    report = build_program_dependency_report(evidence=_MOCK_EVIDENCE, registry=registry)
    assert report["dependencies"]
    assert report["blockers"]
    assert report["critical_path"]
    assert report["validated"] is True


def test_health_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    report = build_program_health_report(evidence=_MOCK_EVIDENCE, registry=registry)
    assert report["sources"] == ["FIX 316", "FIX 324", "FIX 325"]
    assert set(report["health_dimensions"]) == set(PROGRAM_HEALTH_STATUSES)
    assert all(p["health_status"] in PROGRAM_HEALTH_STATUSES for p in report["programs"])
    assert report["validated"] is True


def test_progress_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    report = build_program_progress_report(evidence=_MOCK_EVIDENCE, registry=registry)
    assert report["milestones"]
    assert report["completion_trend"] in {"rising", "steady"}
    assert report["execution_confidence"] in {"low", "medium", "high"}
    assert report["validated"] is True


def test_risk_regression():
    report = build_program_risk_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 309", "FIX 313", "FIX 324", "FIX 326"]
    assert report["program_risks"]
    assert report["validated"] is True


def test_alignment_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    report = build_program_alignment_report(evidence=_MOCK_EVIDENCE, registry=registry)
    assert report["sources"] == ["FIX 290", "FIX 324", "FIX 326"]
    assert report["goals"]
    assert report["programs"]
    assert report["aligned_rows"]
    assert report["validated"] is True


def test_priority_matrix_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    dependency = build_program_dependency_report(evidence=_MOCK_EVIDENCE, registry=registry)
    health = build_program_health_report(evidence=_MOCK_EVIDENCE, registry=registry)
    risk = build_program_risk_report(evidence=_MOCK_EVIDENCE)
    alignment = build_program_alignment_report(evidence=_MOCK_EVIDENCE, registry=registry)
    opportunities = build_program_opportunity_registry(
        dependency_report=dependency,
        health_report=health,
        risk_report=risk,
        alignment_report=alignment,
    )
    matrix = build_program_priority_matrix(
        registry=registry,
        health_report=health,
        risk_report=risk,
        alignment_report=alignment,
        opportunity_registry=opportunities,
    )
    assert matrix["ranked_programs"]
    assert matrix["highest_value_programs"]
    assert matrix["highest_risk_programs"]
    assert matrix["automatic_program_execution_forbidden"] is True
    assert set(opportunities["opportunity_types"]) == set(PROGRAM_OPPORTUNITY_TYPES)


def test_dashboard_regression():
    routed = route_enterprise_program_intelligence("show enterprise program dashboard", session_id="epi-327")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_enterprise_program_intelligence"
    assert meta["route_id"] == ENTERPRISE_PROGRAM_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert PROGRAM_AUTHORITY_FIX_327 is False
    assert AUTOMATIC_PROGRAM_EXECUTION_ENABLED_FIX_327 is False


def test_success_question_routing_regression():
    assert parse_enterprise_program_intelligence_intent("Which programs are healthy?") == {
        "action": "view",
        "focus": "program_health_report",
    }
    routed = route_enterprise_program_intelligence(
        "Where should leadership intervene?",
        session_id="epi-327-q",
    )
    assert routed is not None
    assert "priority" in routed[0].lower() or "Program priority" in routed[0]


def test_program_review_registry_record_only():
    append_program_review_record(kind="program_note", content="Review blocked program dependencies", session_id="epi-327")
    routed = route_enterprise_program_intelligence(
        "program note: monitor critical path blockers",
        session_id="epi-327",
    )
    assert routed is not None
    assert "humans execute programs" in routed[0].lower()
    assert len(list_program_review_records()) == 2


def test_dashboard_builder_regression():
    registry = build_program_registry(evidence=_MOCK_EVIDENCE)
    dependency = build_program_dependency_report(evidence=_MOCK_EVIDENCE, registry=registry)
    health = build_program_health_report(evidence=_MOCK_EVIDENCE, registry=registry)
    progress = build_program_progress_report(evidence=_MOCK_EVIDENCE, registry=registry)
    risk = build_program_risk_report(evidence=_MOCK_EVIDENCE)
    alignment = build_program_alignment_report(evidence=_MOCK_EVIDENCE, registry=registry)
    opportunities = build_program_opportunity_registry(
        dependency_report=dependency,
        health_report=health,
        risk_report=risk,
        alignment_report=alignment,
    )
    matrix = build_program_priority_matrix(
        registry=registry,
        health_report=health,
        risk_report=risk,
        alignment_report=alignment,
        opportunity_registry=opportunities,
    )
    dashboard = build_enterprise_program_dashboard(
        registry=registry,
        dependency_report=dependency,
        health_report=health,
        progress_report=progress,
        risk_report=risk,
        alignment_report=alignment,
        opportunity_registry=opportunities,
        priority_matrix=matrix,
    )
    assert dashboard["program_count"] >= 4
    assert dashboard["automatic_program_execution_forbidden"] is True
