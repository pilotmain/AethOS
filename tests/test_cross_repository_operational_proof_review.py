# SPDX-License-Identifier: Apache-2.0
"""Cross-repository operational proof review tests."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_contract import (
    ATLAS_PILOT_SESSIONS,
)
from aethos_core.mission_control.atlas_trader_pilot_arc_orchestrator.atlas_trader_pilot_arc_orchestrator_store import (
    append_atlas_trader_pilot_arc_orchestrator_record,
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests,
)
from aethos_core.mission_control.atlas_trader_trust_report_freeze.atlas_trader_trust_report_freeze_store import (
    append_atlas_trader_trust_report_freeze_record,
    clear_atlas_trader_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    append_dogfood_pilot_trust_report_freeze_record,
    clear_dogfood_pilot_trust_report_freeze_records_for_tests,
)
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
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_contract import (
    NEXORA_PILOT_SESSIONS,
)
from aethos_core.mission_control.nexora_pilot_arc_orchestrator.nexora_pilot_arc_orchestrator_store import (
    append_nexora_pilot_arc_orchestrator_record,
    clear_nexora_pilot_arc_orchestrator_records_for_tests,
)
from aethos_core.mission_control.nexora_trust_report_freeze.nexora_trust_report_freeze_store import (
    append_nexora_trust_report_freeze_record,
    clear_nexora_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_contract import (
    PILOTOS_PILOT_SESSIONS,
)
from aethos_core.mission_control.pilotos_ui_pilot_arc_orchestrator.pilotos_ui_pilot_arc_orchestrator_store import (
    append_pilotos_ui_pilot_arc_orchestrator_record,
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests,
)
from aethos_core.mission_control.pilotos_ui_trust_report_freeze.pilotos_ui_trust_report_freeze_store import (
    append_pilotos_ui_trust_report_freeze_record,
    clear_pilotos_ui_trust_report_freeze_records_for_tests,
)
from aethos_core.workstreams.cross_repository_operational_proof_review.cross_repository_operational_proof_review_contract import (
    CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_ID,
    REVIEW_AREAS,
    TRUST_GENERALIZATION_LEVELS,
)
from aethos_core.workstreams.cross_repository_operational_proof_review.cross_repository_operational_proof_review_renderer import (
    render_all_cross_repository_operational_proof_deliverables,
)
from aethos_core.workstreams.cross_repository_operational_proof_review.cross_repository_operational_proof_review_service import (
    build_cross_repository_operational_proof_review,
)


@pytest.fixture(autouse=True)
def _clean_stores():
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests()
    clear_nexora_pilot_arc_orchestrator_records_for_tests()
    clear_nexora_trust_report_freeze_records_for_tests()
    yield
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_trust_report_freeze_records_for_tests()
    clear_pilotos_ui_pilot_arc_orchestrator_records_for_tests()
    clear_atlas_trader_trust_report_freeze_records_for_tests()
    clear_atlas_trader_pilot_arc_orchestrator_records_for_tests()
    clear_nexora_pilot_arc_orchestrator_records_for_tests()
    clear_nexora_trust_report_freeze_records_for_tests()


def _seed_repo_pilot_audits(*, sessions: tuple[str, ...], repo_issue: str) -> None:
    for idx, session_id in enumerate(sessions):
        persist_pilot_run_audit(
            {
                "session_id": session_id,
                "repo_issue": repo_issue,
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


def _seed_four_repository_evidence() -> None:
    append_dogfood_pilot_trust_report_freeze_record(
        session_id="cross-review",
        kind="trust_report_freeze_artifact",
        content="AethOS trust baseline",
    )
    _seed_repo_pilot_audits(
        sessions=("dogfood-pilot-1", "dogfood-pilot-2", "dogfood-pilot-3"),
        repo_issue="pilotmain/AethOS#1",
    )

    append_independent_repository_trust_expansion_record(
        session_id="cross-review",
        kind="repo_expansion_approval",
        content="PilotOS expansion",
        repository=PHASE_2_REPOSITORY_ORDER[0],
    )
    append_pilotos_ui_pilot_arc_orchestrator_record(
        session_id="cross-review",
        kind="repo_issue_binding",
        content="pilotmain/pilot-os-ui#1",
        repo_issue="pilotmain/pilot-os-ui#1",
    )
    _seed_repo_pilot_audits(sessions=PILOTOS_PILOT_SESSIONS, repo_issue="pilotmain/pilot-os-ui#1")
    append_pilotos_ui_trust_report_freeze_record(
        session_id="cross-review",
        kind="pilotos_trust_report_freeze_artifact",
        content="PilotOS trust freeze",
    )
    append_pilotos_ui_trust_report_freeze_record(
        session_id="cross-review",
        kind="human_trust_decision_approve",
        content="PilotOS trust approve",
    )

    append_independent_repository_trust_expansion_record(
        session_id="cross-review",
        kind="repo_expansion_approval",
        content="Atlas expansion",
        repository=PHASE_2_REPOSITORY_ORDER[1],
    )
    append_atlas_trader_pilot_arc_orchestrator_record(
        session_id="cross-review",
        kind="repo_issue_binding",
        content="pilotmain/atlas-trader#1",
        repo_issue="pilotmain/atlas-trader#1",
    )
    _seed_repo_pilot_audits(sessions=ATLAS_PILOT_SESSIONS, repo_issue="pilotmain/atlas-trader#1")
    append_atlas_trader_trust_report_freeze_record(
        session_id="cross-review",
        kind="atlas_trust_report_freeze_artifact",
        content="Atlas trust freeze",
    )
    append_atlas_trader_trust_report_freeze_record(
        session_id="cross-review",
        kind="human_trust_decision_approve",
        content="Atlas trust approve",
    )

    append_independent_repository_trust_expansion_record(
        session_id="cross-review",
        kind="repo_expansion_approval",
        content="Nexora expansion",
        repository=PHASE_2_REPOSITORY_ORDER[2],
    )
    append_nexora_pilot_arc_orchestrator_record(
        session_id="cross-review",
        kind="repo_issue_binding",
        content="pilotmain/nexora-monorepo-starter#1",
        repo_issue="pilotmain/nexora-monorepo-starter#1",
    )
    _seed_repo_pilot_audits(
        sessions=NEXORA_PILOT_SESSIONS,
        repo_issue="pilotmain/nexora-monorepo-starter#1",
    )
    append_nexora_trust_report_freeze_record(
        session_id="cross-review",
        kind="nexora_trust_report_freeze_artifact",
        content="Nexora trust freeze",
    )
    append_nexora_trust_report_freeze_record(
        session_id="cross-review",
        kind="human_trust_decision_approve",
        content="Nexora trust approve",
    )


def test_review_areas_present():
    _seed_four_repository_evidence()
    board = build_cross_repository_operational_proof_review(session_id="cross-review").cross_repository_operational_proof_review
    assert board["review_id"] == CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW_ID
    assert len(board["review_areas"]) == len(REVIEW_AREAS)
    for area in REVIEW_AREAS:
        assert board["sections"][area]


def test_trust_baseline_review_regression():
    _seed_four_repository_evidence()
    area1 = (
        build_cross_repository_operational_proof_review(session_id="cross-review")
        .cross_repository_operational_proof_review["sections"]["review_area_1_repository_trust_baselines"][0]
    )
    baselines = area1["repository_trust_baseline_review"]
    assert len(baselines) == 4
    assert area1["repositories_with_trust_freeze"] == 4
    assert area1["repositories_with_trust_decision"] == 4


def test_trust_generalization_regression():
    _seed_four_repository_evidence()
    assessment = (
        build_cross_repository_operational_proof_review(session_id="cross-review")
        .cross_repository_operational_proof_review["sections"]["review_area_8_trust_generalization"][0][
            "trust_generalization_assessment"
        ]
    )
    assert assessment["level"] in TRUST_GENERALIZATION_LEVELS
    assert assessment["repositories_operational_proof_complete"] == 4
    assert assessment["governed_delivery_generalizes"] is True


def test_strategic_recommendation_regression():
    _seed_four_repository_evidence()
    recommendation = (
        build_cross_repository_operational_proof_review(session_id="cross-review")
        .cross_repository_operational_proof_review["sections"]["review_area_10_strategic_recommendation"][0][
            "cross_repository_strategic_recommendation"
        ]
    )
    assert recommendation["primary_recommendation"] == "option_c_limited_external_customer_validation"
    assert recommendation["human_decision_required"] is True


def test_deliverable_renderers():
    _seed_four_repository_evidence()
    board = build_cross_repository_operational_proof_review(session_id="cross-review").cross_repository_operational_proof_review
    docs = render_all_cross_repository_operational_proof_deliverables(board)
    assert set(docs) == {
        "CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW.md",
        "TRUST_GENERALIZATION_ASSESSMENT.md",
        "POST_PROOF_STRATEGIC_RECOMMENDATION.md",
    }
    assert "FIX 191" in docs["CROSS_REPOSITORY_OPERATIONAL_PROOF_REVIEW.md"]
