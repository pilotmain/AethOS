# SPDX-License-Identifier: Apache-2.0
"""FIX 330 — executive operating system dashboard tests."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_contract import (
    AUTOMATIC_DECISION_ENABLED_FIX_330,
    AUTOMATIC_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330,
    AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330,
    EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS,
    EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID,
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
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_intent import (
    parse_executive_operating_system_dashboard_intent,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_router import (
    route_executive_operating_system_dashboard,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_service import (
    build_executive_operating_system_dashboard_board,
)
from aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_store import (
    append_dashboard_review_record,
    clear_dashboard_review_records_for_tests,
    list_dashboard_review_records,
)

_FIX_KEYS = (
    200, 210, 220, 230, 260, 305, 308, 309, 310, 312, 313, 314, 315, 316,
    318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329,
)

_MOCK_EVIDENCE = {
    "session_id": "eosd-330",
    "sources_ok": {f"fix_{n}": True for n in _FIX_KEYS},
    "fix_200": {"sections": {"merge_readiness_assessment": [{"readiness_level": "READY"}]}},
    "fix_210": {
        "sections": {
            "deploy_readiness_assessment": [{"readiness_level": "READY"}],
            "deploy_recommendation": [{"recommendation": "PROCEED_WITH_REVIEW"}],
        }
    },
    "fix_220": {
        "sections": {
            "monitoring_health_assessment": [{"health_status": "HEALTHY"}],
            "incident_detection": [{"classification": "HEALTHY", "signals": []}],
        }
    },
    "fix_230": {
        "sections": {
            "rollback_assessment": [{"risk_level": "LOW", "recovery_stage": "observation"}],
            "rollback_recommendation": [{"recommendation": "MONITOR"}],
            "recovery_timeline": [{"event": "observation"}],
        }
    },
    "fix_260": {
        "sections": {
            "portfolio_engineering_dashboard": [
                {
                    "portfolio_summary": {"repositories": [{"name": "AethOS"}]},
                    "repository_health_rows": [{"repository": "AethOS", "health_tier": "HEALTHY"}],
                }
            ]
        }
    },
    "fix_305": {
        "sections": {
            "billing_dashboard": [{"subscription_health_status": "HEALTHY", "plan_distribution": [{"plan": "pro"}]}],
            "plan_registry": [{"plans": [{"plan": "pro"}, {"plan": "team"}]}],
            "subscription_registry": [{"active_subscriptions": [{"id": "sub-1"}]}],
            "billing_readiness_report": [{"readiness_level": "READY"}],
            "usage_limit_report": [{"alerts": []}],
        }
    },
    "fix_308": {
        "sections": {
            "payment_readiness_dashboard": [{"readiness_level": "READY", "monetization_score": 0.8}],
            "commercial_governance_report": [{"commercial_risks": []}],
        }
    },
    "fix_309": {
        "overall_launch_status": "READY_WITH_CONDITIONS",
        "sections": {
            "launch_readiness_dashboard": [{"readiness_score": 0.82, "overall_readiness_level": "READY_WITH_CONDITIONS"}],
        },
    },
    "fix_310": {
        "sections": {
            "customer_support_success_dashboard": [{"overall_health_level": "STABLE", "at_risk_customer_count": 1}],
        }
    },
    "fix_312": {"sections": {"beta_program_dashboard": [{"participant_count": 12}]}},
    "fix_313": {
        "sections": {
            "launch_operations_dashboard": [{"operations_status": "MONITORING"}],
            "launch_blocker_registry": [{"blockers": [{"detail": "Pending launch review"}]}],
            "launch_risk_dashboard": [{"risks": [{"detail": "Operational risk signal"}]}],
        }
    },
    "fix_314": {
        "sections": {
            "launch_readiness_freeze_dashboard": [{"freeze_status": "FROZEN"}],
            "launch_trust_baseline_summary": [{"baseline_count": 5, "proven_items": ["cap-a"], "unproven_items": ["cap-b"]}],
        }
    },
    "fix_315": {
        "sections": {
            "launch_decision_dashboard": [{"recommendation": "CONDITIONAL_GO"}],
            "launch_trust_evidence_summary": [{"trust_baseline_count": 5, "trust_summary": "Trust baselines frozen"}],
        }
    },
    "fix_316": {
        "sections": {
            "post_launch_operations_dashboard": [
                {
                    "platform_health_status": "HEALTHY",
                    "customer_health_status": "STABLE",
                    "governance_health_status": "STABLE",
                    "incident_count": 1,
                    "operations_status": "MONITORING",
                }
            ],
            "incident_baseline": [{"active_incidents": ["API latency spike"]}],
        }
    },
    "fix_318": {
        "sections": {
            "analytics_dashboard": [{"onboarding_completion_rate_percent": 72, "activated_customers": 40}],
        }
    },
    "fix_319": {
        "sections": {
            "customer_feedback_dashboard": [{"positive_sentiment_count": 8, "negative_sentiment_count": 2}],
        }
    },
    "fix_320": {
        "sections": {
            "growth_adoption_dashboard": [{"activated_customers": 40, "retained_customers": 32, "disengaged_customers": 3}],
            "retention_intelligence_report": [{"retained_customers": 32, "disengaged_customers": 3, "retention_rate_percent": 80}],
        }
    },
    "fix_321": {
        "sections": {
            "customer_journey_dashboard": [{"current_stage": "retention"}],
        }
    },
    "fix_322": {
        "sections": {
            "product_market_fit_dashboard": [{"fit_level": "DEVELOPING", "overall_fit_score": 0.62, "signal_count": 4}],
        }
    },
    "fix_323": {
        "sections": {
            "customer_value_dashboard": [{"realization_level": "MODERATE", "overall_realization_score": 0.58, "outcome_count": 3}],
        }
    },
    "fix_324": {
        "sections": {
            "strategic_portfolio_dashboard": [{"business_value_score": 0.75, "top_priorities": [{"title": "Mission Control adoption"}]}],
            "strategic_priority_registry": [{"priorities": [{"title": "Mission Control adoption"}]}],
            "portfolio_risk_report": [{"product_risk": ["Security gap"], "operational_risk": ["Pending launch review"]}],
            "portfolio_opportunity_registry": [{"opportunities": [{"title": "Portfolio acceleration"}]}],
            "investment_opportunity_report": [{"high_value_opportunities": [{"title": "Accelerate Mission Control"}]}],
            "portfolio_initiative_registry": [{"initiatives": [{"title": "Executive dashboard"}]}],
        }
    },
    "fix_325": {
        "sections": {
            "executive_decision_dashboard": [{"pending_decision_count": 2}],
            "executive_recommendation_report": [{"recommendations": [{"title": "Review governance backlog"}]}],
            "executive_opportunity_registry": [{"opportunities": [{"title": "Expand adoption"}]}],
        }
    },
    "fix_326": {
        "sections": {
            "strategic_planning_dashboard": [{"scenario_count": 5, "generated_plan_count": 5}],
            "strategic_comparison_matrix": [{"strongest_plan": {"scenario": "Balanced growth", "comparison_score": 8.2}}],
            "strategic_risk_forecast": [{"execution_risks": ["Address portfolio risk before acceleration"]}],
            "strategic_opportunity_forecast": [{"growth_opportunities": [{"title": "Balanced growth path"}]}],
        }
    },
    "fix_327": {
        "sections": {
            "enterprise_program_dashboard": [
                {
                    "program_count": 6,
                    "blocked_program_count": 1,
                    "blocked_programs": ["Mission Control Program"],
                }
            ],
            "program_health_report": [
                {
                    "programs": [{"name": "Mission Control Program", "health_status": "blocked"}],
                    "health_status_counts": {"healthy": 1, "warning": 2, "at_risk": 1, "blocked": 1},
                }
            ],
            "program_dependency_report": [
                {
                    "dependencies": [{"program": "Mission Control Program", "dependency": "Security checklist"}],
                    "blockers": [{"blocker": "Incomplete security checklist"}],
                }
            ],
        }
    },
    "fix_328": {
        "sections": {
            "organizational_effectiveness_dashboard": [{"overall_effectiveness_level": "STABLE", "friction_signal_count": 4}],
            "organizational_effectiveness_scorecard": [{"overall_score": 0.61}],
            "governance_friction_report": [{"friction_signals": ["Review delay"], "approval_delay_count": 2, "bottleneck_count": 1}],
            "coordination_intelligence_report": [{"coordination_failures": ["Cross-program gap"], "dependency_gaps": ["Pending launch review"]}],
            "organizational_capacity_report": [{"capacity_level": "STABLE", "initiative_load": 4, "review_burden": 3}],
        }
    },
    "fix_329": {
        "sections": {
            "enterprise_operating_dashboard": [
                {
                    "overall_operating_level": "STABLE",
                    "overall_operating_score": 0.68,
                    "business_value_score": 0.75,
                    "executive_attention_items": [{"title": "Investigate risk: Pending launch review", "action_type": "investigate"}],
                }
            ]
        }
    },
    "dashboard_review_records": [],
}


@pytest.fixture(autouse=True)
def _mock_evidence():
    with patch(
        "aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_service.collect_executive_operating_system_dashboard_evidence",
        return_value=_MOCK_EVIDENCE,
    ), patch(
        "aethos_core.mission_control.executive_operating_system_dashboard.executive_operating_system_dashboard_evidence.collect_executive_operating_system_dashboard_evidence",
        return_value=_MOCK_EVIDENCE,
    ):
        yield


@pytest.fixture(autouse=True)
def _clean_store():
    clear_dashboard_review_records_for_tests()
    yield
    clear_dashboard_review_records_for_tests()


def test_dashboard_domains_and_authority_flags():
    result = build_executive_operating_system_dashboard_board(session_id="eosd-330")
    board = result.executive_operating_system_dashboard
    assert board["executive_dashboard_authority"] is False
    assert board["automatic_execution_enabled"] is False
    assert board["automatic_decision_enabled"] is False
    assert board["automatic_strategy_execution_enabled"] is False
    assert board["automatic_operational_execution_enabled"] is False
    for key in EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_DOMAINS:
        assert board["sections"][key]


def test_executive_summary_regression():
    panel = build_executive_summary_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 309", "FIX 314", "FIX 315", "FIX 316", "FIX 329"]
    assert panel["overall_health"]
    assert panel["launch_state"]
    assert panel["trust_state"]
    assert panel["readiness_state"]
    assert panel["major_alerts"]
    assert panel["validated"] is True


def test_strategy_panel_regression():
    panel = build_strategy_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 324", "FIX 325", "FIX 326"]
    assert panel["top_priorities"]
    assert panel["strategic_plans"]
    assert panel["strategic_risks"]
    assert panel["opportunities"]
    assert panel["validated"] is True


def test_program_panel_regression():
    panel = build_program_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 327"]
    assert panel["active_program_count"] == 6
    assert panel["blocked_program_count"] == 1
    assert panel["critical_dependencies"]
    assert panel["validated"] is True


def test_organization_panel_regression():
    panel = build_organization_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 328"]
    assert panel["effectiveness"]["overall_level"] == "STABLE"
    assert panel["governance_friction"]
    assert panel["capacity"]
    assert panel["coordination"]
    assert panel["validated"] is True


def test_customer_panel_regression():
    panel = build_customer_panel(evidence=_MOCK_EVIDENCE)
    assert "FIX 310" in panel["sources"]
    assert "FIX 323" in panel["sources"]
    assert panel["adoption"]["activated_customers"] == 40
    assert panel["retention"]["retained_customers"] == 32
    assert panel["pmf"]["fit_level"] == "DEVELOPING"
    assert panel["value_realization"]["realization_level"] == "MODERATE"
    assert panel["customer_health"]["health_level"] == "STABLE"
    assert panel["validated"] is True


def test_operations_panel_regression():
    panel = build_operations_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 200", "FIX 210", "FIX 220", "FIX 230", "FIX 313", "FIX 316"]
    assert panel["deploy_health"]
    assert panel["incidents"]
    assert panel["recovery_status"]
    assert panel["operational_risks"]
    assert panel["validated"] is True


def test_commercial_panel_regression():
    panel = build_commercial_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 305", "FIX 308"]
    assert panel["plan_distribution"]
    assert panel["subscription_health"]["active_subscriptions"] == 1
    assert panel["monetization_readiness"]
    assert panel["validated"] is True


def test_portfolio_panel_regression():
    panel = build_portfolio_panel(evidence=_MOCK_EVIDENCE)
    assert panel["sources"] == ["FIX 260", "FIX 324"]
    assert panel["products"]
    assert panel["initiatives"]
    assert panel["investment_opportunities"]
    assert panel["portfolio_risks"]
    assert panel["business_value_score"] == 0.75
    assert panel["validated"] is True


def test_executive_dashboard_regression():
    summary = build_executive_summary_panel(evidence=_MOCK_EVIDENCE)
    strategy = build_strategy_panel(evidence=_MOCK_EVIDENCE)
    program = build_program_panel(evidence=_MOCK_EVIDENCE)
    organization = build_organization_panel(evidence=_MOCK_EVIDENCE)
    customer = build_customer_panel(evidence=_MOCK_EVIDENCE)
    operations = build_operations_panel(evidence=_MOCK_EVIDENCE)
    commercial = build_commercial_panel(evidence=_MOCK_EVIDENCE)
    portfolio = build_portfolio_panel(evidence=_MOCK_EVIDENCE)
    dashboard = build_executive_operating_system_dashboard(
        summary_panel=summary,
        strategy_panel=strategy,
        program_panel=program,
        organization_panel=organization,
        customer_panel=customer,
        operations_panel=operations,
        commercial_panel=commercial,
        portfolio_panel=portfolio,
    )
    assert dashboard["executive_attention_items"]
    assert dashboard["automatic_execution_forbidden"] is True
    assert dashboard["automatic_decision_forbidden"] is True


def test_dashboard_router_regression():
    routed = route_executive_operating_system_dashboard(
        "show executive operating system dashboard",
        session_id="eosd-330",
    )
    assert routed is not None
    body, intent, meta = routed
    assert intent == "mission_control_executive_operating_system_dashboard"
    assert meta["route_id"] == EXECUTIVE_OPERATING_SYSTEM_DASHBOARD_ROUTE_ID
    assert EXECUTIVE_DASHBOARD_AUTHORITY_FIX_330 is False
    assert "automatic" in body.lower()


def test_success_question_routing_regression():
    assert parse_executive_operating_system_dashboard_intent("How is the business doing?") == {
        "action": "view",
        "focus": "executive_summary_panel",
    }
    assert parse_executive_operating_system_dashboard_intent("How are customers doing?") == {
        "action": "view",
        "focus": "customer_panel",
    }
    routed = route_executive_operating_system_dashboard(
        "What requires executive attention?",
        session_id="eosd-330-q",
    )
    assert routed is not None
    assert "attention" in routed[0].lower() or "Executive" in routed[0]


def test_dashboard_review_registry_record_only():
    append_dashboard_review_record(kind="dashboard_note", content="Review blocked programs", session_id="eosd-330")
    records = list_dashboard_review_records()
    assert len(records) == 1
    assert records[0]["kind"] == "dashboard_note"
    assert AUTOMATIC_EXECUTION_ENABLED_FIX_330 is False
    assert AUTOMATIC_DECISION_ENABLED_FIX_330 is False
    assert AUTOMATIC_STRATEGY_EXECUTION_ENABLED_FIX_330 is False
    assert AUTOMATIC_OPERATIONAL_EXECUTION_ENABLED_FIX_330 is False
