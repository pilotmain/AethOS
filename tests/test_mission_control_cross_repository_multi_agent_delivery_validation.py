# SPDX-License-Identifier: Apache-2.0
"""FIX 191 — cross-repository multi-agent delivery validation tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_contract import (
    CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191,
    CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID,
    VALIDATION_REPOSITORIES,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_intent import (
    is_cross_repository_multi_agent_delivery_validation_intent,
    parse_cross_repository_multi_agent_delivery_validation_record_intent,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_service import (
    build_cross_repository_multi_agent_delivery_validation,
)
from aethos_core.mission_control.cross_repository_multi_agent_delivery_validation.cross_repository_multi_agent_delivery_validation_store import (
    clear_cross_repository_multi_agent_delivery_validation_records_for_tests,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    clear_independent_repository_trust_expansion_records_for_tests,
)
from tests.test_mission_control_dogfood_pilot_trust_report_freeze import _seed_dogfood_pilot_audits
from tests.test_mission_control_pilotos_ui_pilot_arc_orchestrator import (
    _seed_pilotos_expansion_approval,
    _seed_pilotos_pilot_audits,
)


@pytest.fixture(autouse=True)
def _clean():
    clear_cross_repository_multi_agent_delivery_validation_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    get_settings.cache_clear()
    yield
    clear_cross_repository_multi_agent_delivery_validation_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_records_for_tests()
    get_settings.cache_clear()


def test_cross_repo_validation_intent():
    assert is_cross_repository_multi_agent_delivery_validation_intent(
        "show cross-repo delivery validation"
    )
    assert is_cross_repository_multi_agent_delivery_validation_intent(
        "cross-repository validation matrix"
    )
    assert not is_cross_repository_multi_agent_delivery_validation_intent("validation grant trust")
    assert not is_cross_repository_multi_agent_delivery_validation_intent("rerun pilot")


def test_cross_repo_validation_record_intent():
    parsed = parse_cross_repository_multi_agent_delivery_validation_record_intent(
        "cross-repo validation observation: PilotOS UI pilot 1 evidence reviewed"
    )
    assert parsed == ("validation_observation", "PilotOS UI pilot 1 evidence reviewed")


def test_build_cross_repo_validation_matrix_structure():
    result = build_cross_repository_multi_agent_delivery_validation(session_id="fix-191-test")
    assert result.ok is True
    report = result.cross_repository_multi_agent_delivery_validation
    assert report["cross_repo_validation_grants_trust"] is CROSS_REPO_VALIDATION_GRANTS_TRUST_FIX_191
    assert report["pilot_reexecution_performed"] is False
    assert report["validation_compose_artifacts_only"] is True

    matrix = report["sections"]["cross_repository_validation_matrix"]
    assert len(matrix) == len(VALIDATION_REPOSITORIES)
    repos = {row["repository"] for row in matrix}
    assert repos == set(VALIDATION_REPOSITORIES)

    by_repo = {row["repository"]: row for row in matrix}
    assert by_repo[PHASE_2_REPOSITORY_ORDER[1]]["trust_state"] == "UNPROVEN"
    assert by_repo[PHASE_2_REPOSITORY_ORDER[2]]["trust_state"] == "UNPROVEN"
    assert by_repo[PHASE_2_REPOSITORY_ORDER[1]]["throughput_score"] is None


def test_build_cross_repo_validation_with_seeded_evidence():
    _seed_dogfood_pilot_audits()
    _seed_pilotos_expansion_approval()
    _seed_pilotos_pilot_audits()

    result = build_cross_repository_multi_agent_delivery_validation(session_id="fix-191-seeded")
    matrix = result.cross_repository_multi_agent_delivery_validation["sections"][
        "cross_repository_validation_matrix"
    ]
    by_repo = {row["repository"]: row for row in matrix}

    aethos = by_repo[PHASE_1_REPOSITORY]
    assert aethos["trust_state"] in {"CONDITIONALLY_TRUSTED", "PILOTING"}
    assert aethos["pilot_progression"]["pilot_3_complete"] is True
    assert aethos["throughput_score"] is not None

    pilotos = by_repo[PHASE_2_REPOSITORY_ORDER[0]]
    assert pilotos["trust_state"] in {"PILOTING", "TRUST_REVIEW_PENDING", "CONDITIONALLY_TRUSTED"}
    assert pilotos["composes_fix_188"] is True

    assessment = result.cross_repository_multi_agent_delivery_validation["sections"][
        "delivery_generalization_assessment"
    ][0]
    assert assessment["merge_deploy_premature"] is True
    assert assessment["validation_grants_trust"] is False

    registry = result.cross_repository_multi_agent_delivery_validation["sections"][
        "cross_repo_evidence_registry"
    ]
    assert any(e.get("kind") == "pilot_audit" for e in registry)


def test_chat_route_show_cross_repo_validation():
    _seed_dogfood_pilot_audits()
    turn = resolve_chat_turn("show cross-repo delivery validation", session_id="fix-191-chat")
    assert turn.intent == "mission_control_cross_repository_multi_agent_delivery_validation"
    assert (turn.meta or {}).get("route_id") == CROSS_REPOSITORY_MULTI_AGENT_DELIVERY_VALIDATION_ROUTE_ID


def test_cross_repo_validation_api():
    _seed_dogfood_pilot_audits()
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/cross-repository-multi-agent-delivery-validation",
        params={"session_id": "fix-191-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["cross_repo_validation_grants_trust"] is False
    assert payload["validation_compose_artifacts_only"] is True
    matrix = payload["cross_repository_multi_agent_delivery_validation"]["sections"][
        "cross_repository_validation_matrix"
    ]
    assert len(matrix) == 4
    assert payload["markdown"]
