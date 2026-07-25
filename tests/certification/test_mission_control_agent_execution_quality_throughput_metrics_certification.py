# SPDX-License-Identifier: Apache-2.0
"""FIX 190 — agent execution quality and throughput metrics certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_190_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_contract import (
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_FIX,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_INVARIANT,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_PRINCIPLES,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID,
    AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION,
    AGENT_METRICS_GRANT_AUTHORITY_FIX_190,
    EXECUTION_PERFORMED_FIX_190,
    METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190,
    THROUGHPUT_METRIC_IDS,
)
from aethos_core.mission_control.agent_execution_quality_throughput_metrics.agent_execution_quality_throughput_metrics_service import (
    build_agent_execution_quality_throughput_metrics,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_agent_execution_quality_throughput_metrics import (
    _seed_fix_189_receipts,
)
from tests.test_mission_control_bounded_execution_participation import _participation_stack

pytestmark = pytest.mark.certification

SESSION = "mc-aetm-cert-190"


class TestMissionControlAgentExecutionQualityThroughputMetricsCertification:
    def test_fix_190_contract(self) -> None:
        assert AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_FIX == "FIX 190"
        assert AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_SCHEMA_VERSION == (
            "mission_control_agent_execution_quality_throughput_metrics_v1"
        )
        assert AGENT_METRICS_GRANT_AUTHORITY_FIX_190 is False
        assert EXECUTION_PERFORMED_FIX_190 is False
        assert METRICS_COMPOSE_RECEIPTS_ONLY_FIX_190 is True
        assert len(THROUGHPUT_METRIC_IDS) == 11
        assert len(AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_PRINCIPLES) >= 8

    def test_fix_190_metrics_not_authority(self) -> None:
        _participation_stack(SESSION)
        _seed_fix_189_receipts(SESSION)
        result = build_agent_execution_quality_throughput_metrics(session_id=SESSION)
        report = result.agent_execution_quality_throughput_metrics
        assert set(report["fix_190_certification_requirements"]) == set(FIX_190_CERTIFICATION_REQUIREMENTS)
        assert report["agent_metrics_grant_authority"] is False
        assert "metrics" in AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_INVARIANT

    def test_fix_190_outputs_present(self) -> None:
        _participation_stack(SESSION)
        _seed_fix_189_receipts(SESSION)
        result = build_agent_execution_quality_throughput_metrics(session_id=SESSION)
        sections = result.agent_execution_quality_throughput_metrics["sections"]
        for metric_id in THROUGHPUT_METRIC_IDS:
            assert metric_id in sections

    def test_fix_190_certification_requirement_count(self) -> None:
        assert len(FIX_190_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_190_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_190_route_id(self) -> None:
        assert AGENT_EXECUTION_QUALITY_THROUGHPUT_METRICS_ROUTE_ID == (
            "mission_control_agent_execution_quality_throughput_metrics"
        )
