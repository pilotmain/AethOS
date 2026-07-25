# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_B1 — limited external customer validation program tests."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.customer_feedback_intelligence.customer_feedback_intelligence_store import (
    append_feedback_review_record,
    clear_feedback_review_records_for_tests,
)
from aethos_core.mission_control.customer_value_realization_intelligence.customer_value_realization_intelligence_store import (
    append_value_review_record,
    clear_value_review_records_for_tests,
)
from aethos_core.mission_control.limited_beta_launch_program.limited_beta_launch_program_store import (
    append_limited_beta_launch_program_record,
    clear_limited_beta_launch_program_records_for_tests,
)
from aethos_core.mission_control.product_market_fit_intelligence.product_market_fit_intelligence_store import (
    append_pmf_review_record,
    clear_pmf_review_records_for_tests,
)
from aethos_core.mission_control.provider_connection_experience.provider_connection_experience_store import (
    append_provider_connection_experience_record,
    clear_provider_connection_experience_records_for_tests,
)
from aethos_core.mission_control.tenant_onboarding_activation.tenant_onboarding_activation_store import (
    append_tenant_onboarding_activation_record,
    clear_tenant_onboarding_activation_records_for_tests,
)
from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_contract import (
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID,
    LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES,
    SUCCESS_QUESTIONS,
)
from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_renderer import (
    render_all_limited_external_customer_validation_deliverables,
)
from aethos_core.workstreams.limited_external_customer_validation_program.limited_external_customer_validation_program_service import (
    build_limited_external_customer_validation_program,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_limited_beta_launch_program_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_feedback_review_records_for_tests()
    clear_value_review_records_for_tests()
    clear_pmf_review_records_for_tests()
    yield
    clear_limited_beta_launch_program_records_for_tests()
    clear_tenant_onboarding_activation_records_for_tests()
    clear_provider_connection_experience_records_for_tests()
    clear_feedback_review_records_for_tests()
    clear_value_review_records_for_tests()
    clear_pmf_review_records_for_tests()


def _seed_validation_evidence() -> None:
    append_limited_beta_launch_program_record(
        session_id="ws-b1",
        kind="beta_candidate_note",
        content="External founder candidate — platform engineer profile",
    )
    append_limited_beta_launch_program_record(
        session_id="ws-b1",
        kind="beta_admission_review_decision_approve",
        content="Human approves limited external validation cohort admission",
    )
    for kind in (
        "organization_setup_review_note",
        "workspace_setup_review_note",
        "project_registration_review_note",
        "provider_connection_note",
    ):
        append_tenant_onboarding_activation_record(
            session_id="ws-b1",
            kind=kind,
            content=f"Completed {kind} for external user",
        )
    append_tenant_onboarding_activation_record(
        session_id="ws-b1",
        kind="onboarding_decision_approve",
        content="Onboarding validated for external cohort member",
    )
    append_tenant_onboarding_activation_record(
        session_id="ws-b1",
        kind="tenant_onboarding_activation_record",
        content="User completed first governed workflow successfully",
    )
    for provider in ("GitHub", "Railway", "Vercel"):
        append_provider_connection_experience_record(
            session_id="ws-b1",
            kind="provider_connection_note",
            content=f"{provider} connection success for external user",
            provider=provider,
        )
    append_tenant_onboarding_activation_record(
        session_id="ws-b1",
        kind="tenant_onboarding_activation_record",
        content="Trust boundaries understood — governance approvals clear",
    )
    append_feedback_review_record(
        session_id="ws-b1",
        kind="feedback_note",
        content="Great onboarding experience — would continue using AethOS",
    )
    append_value_review_record(
        session_id="ws-b1",
        kind="value_note",
        content="User obtained value from first governed workflow within one session",
    )
    append_pmf_review_record(
        session_id="ws-b1",
        kind="pmf_note",
        content="Would recommend to other platform engineers",
    )


def test_program_phases_and_outputs():
    _seed_validation_evidence()
    board = build_limited_external_customer_validation_program(session_id="ws-b1").limited_external_customer_validation_program
    assert board["workstream_id"] == LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PROGRAM_ID
    assert len(board["phases"]) == len(LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES)
    for phase in LIMITED_EXTERNAL_CUSTOMER_VALIDATION_PHASES:
        assert board["sections"][phase]


def test_candidate_and_admission_regression():
    _seed_validation_evidence()
    phase1 = (
        build_limited_external_customer_validation_program(session_id="ws-b1")
        .limited_external_customer_validation_program["sections"]["phase_1_candidate_selection"][0]
    )
    assert phase1["validation_admission_review"]["admission_review_decision_approve"] is True
    assert phase1["validation_candidate_registry"]["composed_from_fix_312"] is True


def test_onboarding_and_provider_regression():
    _seed_validation_evidence()
    board = build_limited_external_customer_validation_program(session_id="ws-b1").limited_external_customer_validation_program
    onboarding = board["sections"]["phase_2_onboarding_validation"][0]["onboarding_validation_report"]
    provider = board["sections"]["phase_3_provider_connection_validation"][0]["provider_validation_report"]
    assert onboarding["completion_rate"] > 0
    assert provider["github_connection_success"] is True


def test_success_questions_regression():
    _seed_validation_evidence()
    board = build_limited_external_customer_validation_program(session_id="ws-b1").limited_external_customer_validation_program
    answers = board["success_question_answers"]
    for question in SUCCESS_QUESTIONS:
        assert question in answers


def test_deliverable_renderers():
    _seed_validation_evidence()
    board = build_limited_external_customer_validation_program(session_id="ws-b1").limited_external_customer_validation_program
    docs = render_all_limited_external_customer_validation_deliverables(board)
    assert set(docs) == {
        "LIMITED_EXTERNAL_CUSTOMER_VALIDATION_REPORT.md",
        "CUSTOMER_VALUE_VALIDATION_REPORT.md",
        "FIRST_CUSTOMER_EVIDENCE_REPORT.md",
    }
    assert "customer validation" in docs["LIMITED_EXTERNAL_CUSTOMER_VALIDATION_REPORT.md"].lower()
