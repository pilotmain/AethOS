# SPDX-License-Identifier: Apache-2.0
"""WORKSTREAM_A1 — PilotOS operational proof program tests."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_2_REPOSITORY_ORDER,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    append_independent_repository_trust_expansion_record,
    clear_independent_repository_trust_expansion_records_for_tests,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    append_pilotos_ui_pilot_arc_orchestrator_record,
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    PILOTOS_PILOT_SESSIONS,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    append_pilotos_ui_trust_report_freeze_record,
    clear_pilotos_ui_trust_report_freeze_records_for_tests,
)
from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_contract import (
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID,
    PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES,
)
from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_renderer import (
    render_all_pilotos_operational_proof_deliverables,
)
from aethos_core.workstreams.pilotos_operational_proof_program.pilotos_operational_proof_program_service import (
    build_pilotos_operational_proof_program,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    yield
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()


def _seed_program_evidence() -> None:
    append_independent_repository_trust_expansion_record(
        session_id="ws-a1",
        kind="repo_expansion_approval",
        content="WORKSTREAM_A1 expansion approval",
        repository=PHASE_2_REPOSITORY_ORDER[0],
    )
    append_pilotos_ui_pilot_arc_orchestrator_record(
        session_id="ws-a1",
        kind="repo_issue_binding",
        content="pilotmain/pilot-os-ui#1",
        repo_issue="pilotmain/pilot-os-ui#1",
    )
    for idx, session_id in enumerate(PILOTOS_PILOT_SESSIONS):
        persist_pilot_run_audit(
            {
                "session_id": session_id,
                "repo_issue": "pilotmain/pilot-os-ui#1",
                "outcome": "complete" if idx != 1 else "partial",
                "stages_completed": ["issue_intake"] if idx == 0 else ["pr_open"],
                "pilot_report": {
                    "stages_satisfied": ["issue_intake", "implementation_plan"]
                    if idx == 0
                    else (["intent_alignment"] if idx == 1 else ["pr_open"])
                },
                "blockers": ["stage_blocked:intent_alignment"] if idx == 1 else [],
            }
        )
    append_pilotos_ui_trust_report_freeze_record(
        session_id="ws-a1",
        kind="pilotos_trust_report_freeze_artifact",
        content="WORKSTREAM_A1 trust freeze artifact",
    )
    append_pilotos_ui_trust_report_freeze_record(
        session_id="ws-a1",
        kind="human_trust_decision_approve",
        content="WORKSTREAM_A1 trust decision approve",
    )


def test_program_phases_and_outputs():
    _seed_program_evidence()
    result = build_pilotos_operational_proof_program(session_id="ws-a1")
    board = result.pilotos_operational_proof_program
    assert board["workstream_id"] == PILOTOS_OPERATIONAL_PROOF_PROGRAM_ID
    assert len(board["phases"]) == len(PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES)
    for phase in PILOTOS_OPERATIONAL_PROOF_PROGRAM_PHASES:
        assert board["sections"][phase]


def test_readiness_regression():
    _seed_program_evidence()
    board = build_pilotos_operational_proof_program(session_id="ws-a1").pilotos_operational_proof_program
    phase1 = board["sections"]["phase_1_repository_readiness"][0]
    assert phase1["pilotos_readiness_report"]["fix_187_expansion_approved"] is True
    assert phase1["pilotos_prerequisite_validation"]["all_prerequisites_satisfied"] is True


def test_pilot_evidence_bundles_regression():
    _seed_program_evidence()
    board = build_pilotos_operational_proof_program(session_id="ws-a1").pilotos_operational_proof_program
    p1 = board["sections"]["phase_2_pilot_1_execution"][0]["pilotos_pilot1_evidence_bundle"]
    p2 = board["sections"]["phase_3_pilot_2_execution"][0]["pilotos_pilot2_evidence_bundle"]
    p3 = board["sections"]["phase_4_pilot_3_execution"][0]["pilotos_pilot3_evidence_bundle"]
    assert p1["audit_present"] is True
    assert p2["audit_present"] is True
    assert p3["audit_present"] is True


def test_evidence_density_regression():
    _seed_program_evidence()
    board = build_pilotos_operational_proof_program(session_id="ws-a1").pilotos_operational_proof_program
    density = board["sections"]["phase_7_evidence_density_review"][0]["pilotos_evidence_density_report"]
    assert density["audits_present"] == 3
    assert density["evidence_density_level"] in {"PARTIAL", "ADEQUATE", "STRONG"}


def test_executive_visibility_regression():
    _seed_program_evidence()
    board = build_pilotos_operational_proof_program(session_id="ws-a1").pilotos_operational_proof_program
    visibility = board["sections"]["phase_8_executive_dashboard_validation"][0][
        "pilotos_executive_visibility_report"
    ]
    assert visibility["pilotos_audit_evidence_present"] is True
    assert "FIX 330" in visibility["module_assessments"]


def test_deliverable_renderers():
    _seed_program_evidence()
    board = build_pilotos_operational_proof_program(session_id="ws-a1").pilotos_operational_proof_program
    docs = render_all_pilotos_operational_proof_deliverables(board)
    assert set(docs) == {
        "PILOTOS_OPERATIONAL_PROOF_REPORT.md",
        "PILOTOS_EVIDENCE_DENSITY_REPORT.md",
        "PILOTOS_TRUST_VALIDATION_REPORT.md",
    }
    for content in docs.values():
        assert "PilotOS" in content
