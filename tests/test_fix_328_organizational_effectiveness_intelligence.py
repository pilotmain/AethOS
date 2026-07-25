# SPDX-License-Identifier: Apache-2.0
"""FIX 328 — organizational effectiveness intelligence tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_contract import (
    AUTOMATIC_GOVERNANCE_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_ORGANIZATIONAL_CHANGES_ENABLED_FIX_328,
    AUTOMATIC_RESOURCE_REALLOCATION_ENABLED_FIX_328,
    AUTOMATIC_ROLE_CHANGES_ENABLED_FIX_328,
    ORGANIZATIONAL_AUTHORITY_FIX_328,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_DOMAINS,
    ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_ROUTE_ID,
    ORGANIZATIONAL_EFFECTIVENESS_LEVELS,
    ORGANIZATIONAL_EFFECTIVENESS_SCORECARD_DIMENSIONS,
    ORGANIZATIONAL_OPPORTUNITY_TYPES,
    ORGANIZATIONAL_RISK_CATEGORIES,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_evaluator import (
    build_coordination_intelligence_report,
    build_decision_velocity_report,
    build_governance_friction_report,
    build_organizational_capacity_report,
    build_organizational_effectiveness_scorecard,
    build_organizational_opportunity_registry,
    build_organizational_risk_report,
    build_organizational_structure_registry,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_intent import (
    parse_organizational_effectiveness_intelligence_intent,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_router import (
    route_organizational_effectiveness_intelligence,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_service import (
    build_organizational_effectiveness_intelligence,
)
from aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_store import (
    append_organizational_review_record,
    clear_organizational_review_records_for_tests,
    list_organizational_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "oei-328",
    "sources_ok": {f"fix_{n}": True for n in (300, 302, 307, 309, 313, 325, 327)},
    "fix_300": {
        "sections": {
            "organization_registry": [{"organization_count": 1, "organizations": [{"name": "Primary Org"}]}],
            "workspace_registry": [{"workspace_count": 2, "workspaces": [{"name": "Mission Control"}]}],
            "role_registry": [{"roles": [{"name": "operator"}, {"name": "reviewer"}]}],
            "tenant_governance_boundary_registry": [{"boundaries": ["Tenant-scoped governance review"]}],
            "tenant_dashboard": [{"project_count": 4}],
        }
    },
    "fix_302": {
        "sections": {
            "tenant_boundary_audit": [{"findings": ["Pending boundary review"]}],
            "governance_action_report": [{"pending_actions": ["Approve launch governance"]}],
            "least_privilege_report": [{"gaps": ["Role review backlog"]}],
        }
    },
    "fix_307": {
        "sections": {
            "governance_timeline": [{"delayed_reviews": ["Security review delayed", "Launch review delayed"]}],
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
    "fix_325": {
        "sections": {
            "executive_decision_registry": [{"pending_count": 2, "reviewed_count": 3, "deferred_count": 1}],
            "executive_recommendation_report": [{"recommendations": [{"title": "Review governance backlog"}]}],
            "executive_decision_dashboard": [{"recommendation_count": 4}],
        }
    },
    "fix_327": {
        "sections": {
            "program_registry": [
                {
                    "programs": [
                        {"program_id": "p1", "name": "Mission Control Program", "entity_type": "strategic_program"},
                        {"program_id": "p2", "name": "Onboarding automation", "entity_type": "initiative"},
                        {"program_id": "p3", "name": "Ops workstream", "entity_type": "workstream"},
                    ]
                }
            ],
            "program_dependency_report": [
                {
                    "dependencies": [{"from_program": "Mission Control Program", "to_program": "Onboarding automation"}],
                    "blockers": [{"program": "Mission Control Program", "blocker": "Pending launch review"}],
                    "critical_path": ["resolve:Pending launch review"],
                    "blocker_count": 2,
                }
            ],
            "program_risk_report": [
                {"program_risks": [{"title": "Incomplete security checklist", "risk_signal": "elevated"}]}
            ],
            "enterprise_program_dashboard": [{"healthy_program_count": 1, "program_risk_count": 2, "blocker_count": 2}],
        }
    },
    "organizational_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_service.collect_organizational_effectiveness_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.organizational_effectiveness_intelligence.organizational_effectiveness_intelligence_evidence.collect_organizational_effectiveness_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_organizational_review_records_for_tests()
    yield
    clear_organizational_review_records_for_tests()


def test_organizational_effectiveness_domains_and_authority_flags():
    result = build_organizational_effectiveness_intelligence(session_id="oei-328")
    board = result.organizational_effectiveness_intelligence
    assert board["organizational_authority"] is False
    assert board["automatic_role_changes_enabled"] is False
    assert board["automatic_governance_changes_enabled"] is False
    assert board["automatic_resource_reallocation_enabled"] is False
    assert board["automatic_organizational_changes_enabled"] is False
    for key in ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_DOMAINS:
        assert board["sections"][key]


def test_structure_registry_regression():
    registry = build_organizational_structure_registry(evidence=_MOCK_EVIDENCE)
    assert registry["sources"] == ["FIX 300", "FIX 302"]
    assert registry["organizations"]
    assert registry["workspaces"]
    assert registry["roles"]
    assert registry["cross_tenant_visibility_forbidden"] is True


def test_governance_friction_regression():
    report = build_governance_friction_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 302", "FIX 307", "FIX 327"]
    assert report["approval_delays"]
    assert report["review_delays"]
    assert report["governance_bottlenecks"]
    assert report["friction_signal_count"] >= 3


def test_coordination_regression():
    report = build_coordination_intelligence_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 327"]
    assert report["dependency_coordination"]
    assert report["coordination_failures"]
    assert report["validated"] is True


def test_capacity_regression():
    report = build_organizational_capacity_report(evidence=_MOCK_EVIDENCE)
    assert report["active_initiative_count"] >= 1
    assert report["active_program_count"] >= 1
    assert report["operational_burden"] >= 2
    assert report["review_burden"] >= 2
    assert report["validated"] is True


def test_decision_velocity_regression():
    report = build_decision_velocity_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 325"]
    assert report["review_velocity"] > 0
    assert report["decision_latency"] in {"low", "medium", "high"}
    assert report["validated"] is True


def test_risk_regression():
    report = build_organizational_risk_report(evidence=_MOCK_EVIDENCE)
    assert report["sources"] == ["FIX 309", "FIX 313", "FIX 327"]
    assert set(report["risk_categories"]) == set(ORGANIZATIONAL_RISK_CATEGORIES)
    assert report["execution_risk"]
    assert report["dependency_risk"]
    assert report["governance_risk"]
    assert report["operational_risk"]


def test_scorecard_regression():
    friction = build_governance_friction_report(evidence=_MOCK_EVIDENCE)
    coordination = build_coordination_intelligence_report(evidence=_MOCK_EVIDENCE)
    capacity = build_organizational_capacity_report(evidence=_MOCK_EVIDENCE)
    velocity = build_decision_velocity_report(evidence=_MOCK_EVIDENCE)
    risk = build_organizational_risk_report(evidence=_MOCK_EVIDENCE)
    dashboard = _MOCK_EVIDENCE["fix_327"]["sections"]["enterprise_program_dashboard"][0]
    scorecard = build_organizational_effectiveness_scorecard(
        friction_report=friction,
        coordination_report=coordination,
        capacity_report=capacity,
        velocity_report=velocity,
        risk_report=risk,
        program_dashboard=dashboard,
    )
    assert set(scorecard["dimensions"]) == set(ORGANIZATIONAL_EFFECTIVENESS_SCORECARD_DIMENSIONS)
    assert scorecard["overall_level"] in ORGANIZATIONAL_EFFECTIVENESS_LEVELS
    assert scorecard["automatic_organizational_changes_forbidden"] is True


def test_dashboard_regression():
    routed = route_organizational_effectiveness_intelligence(
        "show organizational effectiveness dashboard",
        session_id="oei-328",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_organizational_effectiveness_intelligence"
    assert meta["route_id"] == ORGANIZATIONAL_EFFECTIVENESS_INTELLIGENCE_ROUTE_ID
    assert "automatic" in body.lower()
    assert ORGANIZATIONAL_AUTHORITY_FIX_328 is False


def test_success_question_routing_regression():
    assert parse_organizational_effectiveness_intelligence_intent("Where is organizational friction?") == {
        "action": "view",
        "focus": "governance_friction_report",
    }
    routed = route_organizational_effectiveness_intelligence(
        "How effective is execution?",
        session_id="oei-328-q",
    )
    assert routed is not None
    assert "scorecard" in routed[0].lower() or "effectiveness" in routed[0].lower()


def test_opportunity_registry_regression():
    friction = build_governance_friction_report(evidence=_MOCK_EVIDENCE)
    coordination = build_coordination_intelligence_report(evidence=_MOCK_EVIDENCE)
    capacity = build_organizational_capacity_report(evidence=_MOCK_EVIDENCE)
    risk = build_organizational_risk_report(evidence=_MOCK_EVIDENCE)
    registry = build_organizational_opportunity_registry(
        friction_report=friction,
        coordination_report=coordination,
        capacity_report=capacity,
        risk_report=risk,
    )
    assert registry["opportunities"]
    assert set(registry["opportunity_types"]) == set(ORGANIZATIONAL_OPPORTUNITY_TYPES)


def test_organizational_review_registry_record_only():
    append_organizational_review_record(
        kind="organization_note",
        content="Review governance review backlog",
        session_id="oei-328",
    )
    routed = route_organizational_effectiveness_intelligence(
        "organization note: track approval bottlenecks",
        session_id="oei-328",
    )
    assert routed is not None
    assert "humans manage organizations" in routed[0].lower()
    assert len(list_organizational_review_records()) == 2
