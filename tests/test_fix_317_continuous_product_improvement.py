# SPDX-License-Identifier: Apache-2.0
"""FIX 317 — continuous product improvement tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_contract import (
    AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317,
    CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317,
    CONTINUOUS_PRODUCT_IMPROVEMENT_DOMAINS,
    CONTINUOUS_PRODUCT_IMPROVEMENT_ROUTE_ID,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_evaluator import (
    build_commercial_improvement_report,
    build_feedback_intelligence_report,
    build_governance_improvement_report,
    build_improvement_opportunity_registry,
    build_improvement_priority_matrix,
    build_onboarding_improvement_report,
    build_operational_improvement_report,
    build_product_experience_improvement_report,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_intent import (
    parse_continuous_product_improvement_intent,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_router import (
    route_continuous_product_improvement,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_service import (
    build_continuous_product_improvement,
)
from aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_store import (
    append_improvement_review_record,
    clear_improvement_review_records_for_tests,
    list_improvement_review_records,
)

_MOCK_EVIDENCE = {
    "session_id": "cpi-317",
    "sources_ok": {f"fix_{n}": True for n in (220, 230, 300, 301, 302, 305, 307, 308, 310, 311, 312, 313)},
    "fix_310": {
        "blockers": ["Customer adoption lag in onboarding cohort"],
        "sections": {
            "customer_risk_registry": [{"at_risk_count": 2, "healthy_count": 1}],
            "customer_support_success_dashboard": [{"evidence_coverage": "partial"}],
        },
    },
    "fix_312": {
        "blockers": ["Beta feedback triage backlog"],
        "sections": {
            "beta_feedback_registry": [{"feedback_items": ["Confusing capability labels"]}],
        },
    },
    "fix_301": {
        "sections": {
            "onboarding_progress_registry": [{"incomplete_steps": ["Connect provider", "Activate Mission Control"]}],
            "provider_connection_checklist": [{"pending_connections": ["github"]}],
        }
    },
    "fix_300": {
        "sections": {
            "tenant_onboarding_registry": [{"abandoned_onboarding": 1}],
        }
    },
    "fix_311": {
        "sections": {
            "capability_explorer": [{"confusion_points": ["Trust vs capability maturity"]}],
            "trust_explorer": [{"gaps": ["Human approval steps unclear"]}],
            "public_product_dashboard": [{"navigation_friction": "Tour drop-off", "launch_status": "ATTENTION"}],
        }
    },
    "fix_220": {"blockers": ["Recurring monitoring alert noise"]},
    "fix_230": {"blockers": ["Rollback rehearsal not documented"]},
    "fix_313": {
        "blockers": ["Launch blocker: support runbook incomplete"],
        "sections": {
            "launch_blocker_registry": [{"blockers": ["Incomplete support runbook"]}],
        },
    },
    "fix_302": {
        "sections": {
            "least_privilege_report": [{"gaps": ["Approval queue delay"]}],
            "tenant_boundary_audit": [{"findings": ["Cross-workspace read scope review pending"]}],
        }
    },
    "fix_307": {
        "sections": {
            "governance_timeline": [{"delayed_reviews": ["Launch trust review waiting 5 days"]}],
        }
    },
    "fix_305": {
        "sections": {
            "usage_limit_report": [{"limits_reached": ["Starter plan API quota"]}],
            "billing_readiness_report": [{"gaps": ["Invoice preview copy"]}],
        }
    },
    "fix_308": {
        "sections": {
            "upgrade_path_registry": [{"paths": ["Starter to Pro upgrade unclear"]}],
            "commercial_governance_report": [{"confusion_points": ["Entitlement matrix hard to read"]}],
        }
    },
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_service.collect_improvement_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.continuous_product_improvement.continuous_product_improvement_evidence.collect_improvement_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_improvement_review_records_for_tests()
    yield
    clear_improvement_review_records_for_tests()


def test_continuous_product_improvement_domains_and_authority_flags():
    result = build_continuous_product_improvement(session_id="cpi-317")
    board = result.continuous_product_improvement
    assert board["continuous_improvement_authority"] is False
    assert board["automatic_backlog_creation_enabled"] is False
    assert board["automatic_feature_creation_enabled"] is False
    for key in CONTINUOUS_PRODUCT_IMPROVEMENT_DOMAINS:
        assert board["sections"][key]


def test_feedback_intelligence_regression():
    report = build_feedback_intelligence_report(evidence=_MOCK_EVIDENCE)
    assert report["validated"] is True
    assert any("adoption" in opp["title"].lower() for opp in report["opportunities"])


def test_onboarding_intelligence_regression():
    report = build_onboarding_improvement_report(evidence=_MOCK_EVIDENCE)
    assert "Connect provider" in (report.get("friction_points") or [])
    assert report["opportunities"]


def test_product_experience_intelligence_regression():
    report = build_product_experience_improvement_report(evidence=_MOCK_EVIDENCE)
    assert report["capability_confusion_signals"]
    assert report["opportunities"]


def test_operational_intelligence_regression():
    report = build_operational_improvement_report(evidence=_MOCK_EVIDENCE)
    assert report["validated"] is True
    assert len(report["opportunities"]) >= 2


def test_governance_intelligence_regression():
    report = build_governance_improvement_report(evidence=_MOCK_EVIDENCE)
    assert report["review_delays"]
    assert report["opportunities"]


def test_commercial_intelligence_regression():
    report = build_commercial_improvement_report(evidence=_MOCK_EVIDENCE)
    assert report["upgrade_opportunities"]
    assert report["opportunities"]


def test_improvement_prioritization_regression():
    reports = {
        "feedback": build_feedback_intelligence_report(evidence=_MOCK_EVIDENCE),
        "onboarding": build_onboarding_improvement_report(evidence=_MOCK_EVIDENCE),
    }
    registry = build_improvement_opportunity_registry(reports=reports)
    matrix = build_improvement_priority_matrix(registry=registry)
    assert registry["count"] >= 2
    assert matrix["ranked_opportunities"]
    assert matrix["automatic_execution_forbidden"] is True


def test_dashboard_regression():
    routed = route_continuous_product_improvement("show continuous improvement dashboard", session_id="cpi-317")
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_continuous_product_improvement"
    assert meta["route_id"] == CONTINUOUS_PRODUCT_IMPROVEMENT_ROUTE_ID
    assert "Recommendations only" in body
    assert CONTINUOUS_IMPROVEMENT_AUTHORITY_FIX_317 is False
    assert AUTOMATIC_BACKLOG_CREATION_ENABLED_FIX_317 is False


def test_success_question_routing_regression():
    assert parse_continuous_product_improvement_intent("What should improve next?") == {
        "action": "view",
        "focus": "improvement_priority_matrix",
    }
    routed = route_continuous_product_improvement("What are users struggling with?", session_id="cpi-317-q")
    assert routed is not None
    assert "Feedback intelligence" in routed[0]


def test_improvement_review_registry_record_only():
    append_improvement_review_record(kind="improvement_note", content="Track onboarding friction", session_id="cpi-317")
    routed = route_continuous_product_improvement("improvement note: prioritize provider onboarding", session_id="cpi-317")
    assert routed is not None
    assert "record-only" not in routed[0].lower()
    assert "automatic execution" in routed[0].lower()
    assert len(list_improvement_review_records()) == 2
