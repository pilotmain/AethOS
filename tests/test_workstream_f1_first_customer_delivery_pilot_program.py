# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_F1 — first customer delivery pilot tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_end_to_end_delivery_certification.governed_end_to_end_delivery_certification_store import (
    clear_governed_end_to_end_delivery_certification_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_contract import (
    AUTHORITY_EXPANSION_FIX_347,
    CUSTOMER_AUTHORITY_FIX_347,
    FIRST_CUSTOMER_DELIVERY_PILOT_PHASES,
    FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    run_customer_delivery_pilot,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_intent import (
    handle_first_customer_delivery_pilot_intent,
    parse_first_customer_delivery_pilot_intent,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_renderer import (
    render_all_first_customer_delivery_pilot_deliverables,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_service import (
    build_first_customer_delivery_pilot_program,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    clear_first_customer_delivery_pilot_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()


def _seed_intake_and_run(session_id: str = "ws-f1") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Add health-check endpoint, "
            "scope=small FastAPI service, type=health_check_endpoint, "
            "success=verified deploy, out_of_scope=production-critical systems"
        ),
        session_id=session_id,
    )
    result = run_customer_delivery_pilot(session_id=session_id)
    assert result["passed"] is True
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer pilot review approve: Human approves first customer delivery pilot evidence"
        ),
        session_id=session_id,
    )


def test_workstream_phases():
    assert FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID == "WORKSTREAM_F1"
    assert len(FIRST_CUSTOMER_DELIVERY_PILOT_PHASES) == 10
    assert CUSTOMER_AUTHORITY_FIX_347 is False
    assert AUTHORITY_EXPANSION_FIX_347 is False


def test_intent_parsing():
    assert parse_first_customer_delivery_pilot_intent("show customer delivery pilot dashboard") == {
        "action": "view",
        "focus": "customer_delivery_pilot_dashboard",
    }
    intake = parse_first_customer_delivery_pilot_intent(
        "customer delivery request: goal=Landing page, scope=marketing, type=nextjs_landing_page"
    )
    assert intake["action"] == "intake"
    assert parse_first_customer_delivery_pilot_intent("customer delivery pilot run") == {"action": "run", "request_type": None}


def test_pilot_requires_intake():
    result = run_customer_delivery_pilot(session_id="ws-f1-no-intake")
    assert result["ok"] is False
    assert result["error"] == "customer_delivery_request_required"


def test_program_phases_and_deliverables():
    _seed_intake_and_run(session_id="ws-f1-full")
    board = build_first_customer_delivery_pilot_program(session_id="ws-f1-full").first_customer_delivery_pilot_program
    assert board["workstream_id"] == FIRST_CUSTOMER_DELIVERY_PILOT_PROGRAM_ID
    assert board["customer_authority"] is False
    assert board["automatic_customer_acceptance"] is False
    for phase in FIRST_CUSTOMER_DELIVERY_PILOT_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["program_complete"] is True

    deliverables = render_all_first_customer_delivery_pilot_deliverables(board)
    assert set(deliverables) == {
        "FIRST_CUSTOMER_DELIVERY_PILOT_REPORT.md",
        "CUSTOMER_DELIVERY_EVIDENCE_BUNDLE.md",
        "CUSTOMER_VALUE_REALIZATION_REPORT.md",
    }
    assert "Customer delivery pilot ≠ customer authority" in deliverables["FIRST_CUSTOMER_DELIVERY_PILOT_REPORT.md"]
