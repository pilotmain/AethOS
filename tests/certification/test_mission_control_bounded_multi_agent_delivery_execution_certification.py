# SPDX-License-Identifier: Apache-2.0
"""FIX 189 — bounded multi-agent delivery execution certification."""

from __future__ import annotations

import pytest

from aethos_core.governance.governance_friction_approval_contract import FIX_189_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_contract import (
    AGENT_EXECUTION_AUTHORITY_FIX_189,
    AGENT_EXECUTION_PIPELINE_ORDER,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_FIX,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_PRINCIPLES,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID,
    BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION,
    DEPLOY_AUTHORITY_FIX_189,
    MERGE_AUTHORITY_FIX_189,
    PROVIDER_AUTHORITY_FIX_189,
    RAILWAY_AUTHORITY_FIX_189,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_execution.bounded_multi_agent_delivery_execution_service import (
    build_bounded_multi_agent_delivery_execution,
)
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_mission_control_bounded_execution_participation import _participation_stack

pytestmark = pytest.mark.certification

SESSION = "mc-bmade-cert-189"


class TestMissionControlBoundedMultiAgentDeliveryExecutionCertification:
    def test_fix_189_contract(self) -> None:
        assert BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_FIX == "FIX 189"
        assert BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_SCHEMA_VERSION == (
            "mission_control_bounded_multi_agent_delivery_execution_v1"
        )
        assert AGENT_EXECUTION_AUTHORITY_FIX_189 is False
        assert MERGE_AUTHORITY_FIX_189 is False
        assert DEPLOY_AUTHORITY_FIX_189 is False
        assert RAILWAY_AUTHORITY_FIX_189 is False
        assert PROVIDER_AUTHORITY_FIX_189 is False
        assert len(BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_PRINCIPLES) >= 8

    def test_fix_189_pipeline_order(self) -> None:
        assert AGENT_EXECUTION_PIPELINE_ORDER == (
            "planner_agent",
            "delivery_agent",
            "verification_agent",
            "diff_audit_agent",
            "risk_agent",
        )

    def test_fix_189_composes_without_authority_expansion(self) -> None:
        _participation_stack(SESSION)
        result = build_bounded_multi_agent_delivery_execution(session_id=SESSION)
        assert result.ok is True
        report = result.bounded_multi_agent_delivery_execution
        assert set(report["fix_189_certification_requirements"]) == set(FIX_189_CERTIFICATION_REQUIREMENTS)
        assert report["agent_execution_authority"] is False
        assert "agent_execution_authority" in BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT or (
            "without_agent_execution_authority" in BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_INVARIANT
        )

    def test_fix_189_outputs_present(self) -> None:
        _participation_stack(SESSION)
        result = build_bounded_multi_agent_delivery_execution(session_id=SESSION)
        sections = result.bounded_multi_agent_delivery_execution["sections"]
        assert sections["agent_execution_packages"]
        assert sections["agent_execution_registry"] is not None
        assert sections["execution_pipeline_state_machine"]
        assert sections["execution_readiness_assessment"]

    def test_fix_189_certification_requirement_count(self) -> None:
        assert len(FIX_189_CERTIFICATION_REQUIREMENTS) == 10

    def test_fix_189_operator_api_surface(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True

    def test_fix_189_route_id(self) -> None:
        assert BOUNDED_MULTI_AGENT_DELIVERY_EXECUTION_ROUTE_ID == (
            "mission_control_bounded_multi_agent_delivery_execution"
        )
