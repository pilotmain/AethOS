# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_G1 — real evidence density & trust maturity tests."""

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
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_intent import (
    handle_customer_value_adoption_validation_intent,
    parse_customer_value_adoption_validation_intent,
)
from aethos_core.workstreams.customer_value_adoption_validation_program.customer_value_adoption_validation_program_store import (
    clear_customer_value_adoption_validation_records_for_tests,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_executor import (
    run_customer_delivery_pilot,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_intent import (
    handle_first_customer_delivery_pilot_intent,
    parse_first_customer_delivery_pilot_intent,
)
from aethos_core.workstreams.first_customer_delivery_pilot_program.first_customer_delivery_pilot_program_store import (
    clear_first_customer_delivery_pilot_records_for_tests,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_contract import (
    AUTHORITY_EXPANSION_FIX_354,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES,
    REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID,
    TRUST_AUTHORITY_FIX_354,
    TRUST_PROMOTION_FIX_354,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_intent import (
    handle_evidence_maturity_intent,
    parse_evidence_maturity_intent,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_renderer import (
    render_all_evidence_maturity_deliverables,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_service import (
    build_real_evidence_density_trust_maturity_program,
)
from aethos_core.workstreams.real_evidence_density_trust_maturity_program.real_evidence_density_trust_maturity_program_store import (
    clear_evidence_maturity_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_evidence_maturity_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_governed_end_to_end_delivery_certification_records_for_tests()
    clear_first_customer_delivery_pilot_records_for_tests()
    clear_customer_value_adoption_validation_records_for_tests()
    clear_evidence_maturity_records_for_tests()


def _seed_operational_evidence(customer_session: str = "ws-g1-alpha") -> None:
    handle_first_customer_delivery_pilot_intent(
        parse_first_customer_delivery_pilot_intent(
            "customer delivery request: goal=Health endpoint, scope=small service, type=health_check_endpoint"
        ),
        session_id=customer_session,
    )
    assert run_customer_delivery_pilot(session_id=customer_session)["passed"] is True
    handle_customer_value_adoption_validation_intent(
        parse_customer_value_adoption_validation_intent(
            "customer usage observation: workflow=health-check, endpoint=/health, executions=4, trend=continued"
        ),
        session_id=customer_session,
    )


def _seed_evidence_maturity(program_session: str = "ws-g1") -> None:
    _seed_operational_evidence("ws-g1-alpha")
    handle_evidence_maturity_intent(
        parse_evidence_maturity_intent("evidence maturity domain: domain=customer, source=f1"),
        session_id=program_session,
    )
    handle_evidence_maturity_intent(
        parse_evidence_maturity_intent(
            "evidence maturity review approve: Human approves real evidence density validation"
        ),
        session_id=program_session,
    )


def test_workstream_phases():
    assert REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID == "WORKSTREAM_G1"
    assert len(REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES) == 9
    assert TRUST_AUTHORITY_FIX_354 is False
    assert TRUST_PROMOTION_FIX_354 is False
    assert AUTHORITY_EXPANSION_FIX_354 is False


def test_intent_parsing():
    assert parse_evidence_maturity_intent("show evidence maturity dashboard") == {
        "action": "view",
        "focus": "evidence_maturity_dashboard",
    }
    domain = parse_evidence_maturity_intent("evidence maturity domain: domain=customer, source=f1")
    assert domain["action"] == "domain"


def test_program_phases_and_deliverables():
    _seed_evidence_maturity(program_session="ws-g1-full")
    board = build_real_evidence_density_trust_maturity_program(
        session_id="ws-g1-full"
    ).real_evidence_density_trust_maturity_program
    assert board["workstream_id"] == REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PROGRAM_ID
    assert board["trust_authority"] is False
    assert board["trust_promotion"] is False
    for phase in REAL_EVIDENCE_DENSITY_TRUST_MATURITY_PHASES:
        assert phase in board["sections"]
    assert board["success_criteria"]["evidence_completeness_demonstrated"] is True
    assert board["success_criteria"]["program_complete"] is True
    assert board["metrics"]["evidence_density_score"] > 0
    assert board["metrics"]["operational_proof_coverage"] > 0

    deliverables = render_all_evidence_maturity_deliverables(board)
    assert set(deliverables) == {
        "REAL_EVIDENCE_DENSITY_REPORT.md",
        "TRUST_MATURITY_REPORT.md",
        "EVIDENCE_GAP_ANALYSIS.md",
    }
    assert "Evidence density ≠ trust authority" in deliverables["REAL_EVIDENCE_DENSITY_REPORT.md"]
