# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_D1 — Phase 2 provider execution expansion tests."""

from __future__ import annotations

import pytest

from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_intent import (
    handle_governed_code_generation_intent,
)
from aethos_core.execution_tracks.governed_code_generation_changeset_creation.governed_code_generation_changeset_creation_store import (
    clear_governed_code_generation_records_for_tests,
)
from aethos_core.execution_tracks.governed_deployment_execution.governed_deployment_execution_store import (
    clear_governed_deployment_execution_records_for_tests,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_intent import (
    handle_governed_git_delivery_intent,
    parse_governed_git_delivery_intent,
)
from aethos_core.execution_tracks.governed_git_delivery.governed_git_delivery_store import (
    clear_governed_git_delivery_records_for_tests,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_intent import (
    handle_governed_workspace_creation_intent,
)
from aethos_core.execution_tracks.governed_workspace_creation_repository_bootstrap.governed_workspace_creation_repository_bootstrap_store import (
    clear_governed_workspace_creation_records_for_tests,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_contract import (
    AUTHORITY_EXPANSION_FIX_341,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES,
    PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID,
    WAVE_1_PROVIDER_ORDER,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_executor import (
    execute_phase2_provider_deployment,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_intent import (
    handle_phase2_provider_execution_expansion_intent,
    parse_phase2_provider_execution_expansion_intent,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_renderer import (
    render_all_phase2_provider_expansion_deliverables,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_service import (
    build_phase2_provider_execution_expansion_program,
)
from aethos_core.workstreams.phase2_provider_execution_expansion_program.phase2_provider_execution_expansion_program_store import (
    clear_phase2_provider_execution_expansion_records_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_phase2_provider_execution_expansion_records_for_tests()
    yield
    clear_governed_workspace_creation_records_for_tests()
    clear_governed_code_generation_records_for_tests()
    clear_governed_git_delivery_records_for_tests()
    clear_governed_deployment_execution_records_for_tests()
    clear_phase2_provider_execution_expansion_records_for_tests()


def _seed_et1_et2_et3(session_id: str) -> None:
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_creation_review_note",
            "content": "name=phase2-api template=generic_repository org=org-phase2",
            "metadata": {
                "workspace_name": "phase2-api",
                "template_id": "generic_repository",
                "org_id": "org-phase2",
            },
        },
        session_id=session_id,
    )
    handle_governed_workspace_creation_intent(
        {
            "action": "record",
            "kind": "workspace_decision_approve",
            "content": "Human approves workspace for Phase 2 provider deployment",
        },
        session_id=session_id,
    )
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_request_review_note",
            "content": "type=story feature=phase2-deploy Phase 2 deployment feature",
            "metadata": {
                "type": "story",
                "feature_name": "phase2-deploy",
                "title": "Phase 2 Deploy",
            },
        },
        session_id=session_id,
    )
    handle_governed_code_generation_intent(
        {
            "action": "record",
            "kind": "generation_decision_approve",
            "content": "Human approves code generation for Phase 2 deployment",
        },
        session_id=session_id,
    )
    for text in (
        "git delivery review: work_item=phase2-deploy target_branch=main",
        "branch delivery review: Approve delivery branch for Phase 2",
        "commit delivery review: Approve commit assembly for Phase 2",
        "pull request review: Approve PR creation for Phase 2",
        "git delivery decision approve: Human approves git delivery for Phase 2",
    ):
        intent = parse_governed_git_delivery_intent(text)
        assert intent is not None
        handle_governed_git_delivery_intent(intent, session_id=session_id)


def _seed_phase2_gates(session_id: str, provider: str = "aws", service: str = "ECS") -> None:
    _seed_et1_et2_et3(session_id)
    for text in (
        "phase2 provider expansion note: Enable AWS Phase 2 governed deployment",
        f"phase2 provider readiness review: provider={provider}",
        f"phase2 provider execution review: provider={provider} service={service}",
        "phase2 provider expansion review approve: Human approves Phase 2 provider expansion",
    ):
        intent = parse_phase2_provider_execution_expansion_intent(text)
        assert intent is not None
        handle_phase2_provider_execution_expansion_intent(intent, session_id=session_id)


def test_workstream_phases():
    assert PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID == "WORKSTREAM_D1"
    assert len(PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES) == 9
    assert len(WAVE_1_PROVIDER_ORDER) == 4


def test_intent_parsing():
    assert parse_phase2_provider_execution_expansion_intent("show phase2 provider dashboard") == {
        "action": "view",
        "focus": "expansion_dashboard",
    }
    deploy = parse_phase2_provider_execution_expansion_intent(
        "phase2 provider deploy: provider=aws service=ECS environment=staging"
    )
    assert deploy["action"] == "deploy"
    assert deploy["provider"] == "aws"


def test_program_phases_and_outputs():
    board = build_phase2_provider_execution_expansion_program(session_id="ws-d1-empty").phase2_provider_execution_expansion_program
    assert board["workstream_id"] == PHASE2_PROVIDER_EXECUTION_EXPANSION_PROGRAM_ID
    assert board["authority_expansion"] is False
    for phase in PHASE2_PROVIDER_EXECUTION_EXPANSION_PHASES:
        assert phase in board["sections"]


def test_phase2_aws_deployment():
    session_id = "ws-d1-aws"
    _seed_phase2_gates(session_id, provider="aws", service="ECS")
    result = execute_phase2_provider_deployment(
        session_id=session_id,
        provider="aws",
        service="ECS",
        environment="staging",
    )
    assert result["executed"] is True
    assert result["provider"] == "AWS"
    assert result["authority_expansion_performed"] is False

    board = build_phase2_provider_execution_expansion_program(session_id=session_id).phase2_provider_execution_expansion_program
    aws_section = board["sections"]["phase_2_aws_execution"][0]
    assert aws_section["aws_deployment_report"]["provider"] == "AWS"
    assert aws_section["aws_evidence_bundle"]["bundle_id"] == "aws-evidence-bundle"


def test_phase2_blocked_without_approval():
    _seed_et1_et2_et3("ws-d1-blocked")
    handle_phase2_provider_execution_expansion_intent(
        parse_phase2_provider_execution_expansion_intent("phase2 provider readiness review: provider=aws"),
        session_id="ws-d1-blocked",
    )
    result = execute_phase2_provider_deployment(session_id="ws-d1-blocked", provider="aws")
    assert result["executed"] is False


def test_deliverable_renderers():
    _seed_phase2_gates("ws-d1-render", provider="kubernetes", service="deployment_rollout")
    execute_phase2_provider_deployment(
        session_id="ws-d1-render",
        provider="kubernetes",
        service="deployment_rollout",
    )
    board = build_phase2_provider_execution_expansion_program(session_id="ws-d1-render").phase2_provider_execution_expansion_program
    deliverables = render_all_phase2_provider_expansion_deliverables(board)
    assert set(deliverables) == {
        "PHASE2_PROVIDER_EXPANSION_REPORT.md",
        "AWS_EXECUTION_READINESS_REPORT.md",
        "KUBERNETES_EXECUTION_READINESS_REPORT.md",
    }
    assert "Provider expansion ≠ authority expansion" in deliverables["PHASE2_PROVIDER_EXPANSION_REPORT.md"]
    assert AUTHORITY_EXPANSION_FIX_341 is False
