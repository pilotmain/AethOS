# SPDX-License-Identifier: Apache-2.0
"""Cognition capability fallback planning tests."""

from __future__ import annotations

import pytest

from aethos_core.capabilities.capability_planner import attach_capabilities, plan_capability_chain
from aethos_core.operational_cognition.types import OperationalCognitionDecision
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.operational_result_store import clear_operational_results_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_operational_results_for_tests()


def _decision(intent: str) -> OperationalCognitionDecision:
    return OperationalCognitionDecision(intent=intent, scope="failed_service", provider="railway", target="MongoDB", confidence=0.9)


def test_diagnose_failure_adds_discovery_capabilities_when_cache_missing():
    chain = plan_capability_chain(_decision("diagnose_failure"), session_id="cap-missing")
    assert chain[:3] == ["discover_provider_inventory", "resolve_target", "collect_health_state"]
    assert "correlate_evidence_freshness" in chain
    assert "plan_best_next_step" in chain
    assert "compose_diagnosis" in chain


def test_create_fix_plan_adds_inventory_resolution_when_cache_missing():
    chain = plan_capability_chain(_decision("create_fix_plan"), session_id="cap-plan")
    assert "discover_provider_inventory" in chain
    assert "correlate_evidence_freshness" in chain
    assert "compose_fix_plan" in chain


def test_cached_health_skips_discovery_capabilities():
    store_provider_wide_health_result(
        session_id="cap-cached",
        provider="railway",
        payload={"services": [{"service": "MongoDB", "project": "p", "environment": "production", "status": "failed", "health": "failed"}], "counts": {"total": 1, "failed": 1}, "failures": [], "unknown": []},
        summary={"total": 1, "failed": 1},
    )
    chain = plan_capability_chain(_decision("diagnose_failure"), session_id="cap-cached")
    assert "discover_provider_inventory" not in chain
    assert "correlate_evidence_freshness" in chain
    assert chain[0] == "correlate_evidence_freshness"


def test_manual_prerequisite_only_after_discovery_failure():
    from unittest.mock import patch

    from aethos_core.failed_service_investigation.failed_service_router import compose_failed_service_investigation_reply

    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=([], "no token"),
    ):
        reply, intent, meta = compose_failed_service_investigation_reply("why is MongoDB failed?", session_id="cap-manual")
    assert intent == "failed_service_investigation_discovery_failed"
    assert "check all services in railway" in reply.lower()
    assert "Run **check all services in railway** first" not in reply


def test_attach_capabilities_includes_session_context():
    decision = attach_capabilities(_decision("diagnose_failure"), session_id="cap-attach")
    assert decision.capabilities
    assert decision.capabilities[0] == "discover_provider_inventory"
