# SPDX-License-Identifier: Apache-2.0
"""FIX 187 — independent repository trust expansion tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    clear_dogfood_pilot_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_contract import (
    INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID,
    PHASE_1_REPOSITORY,
    PHASE_2_REPOSITORY_ORDER,
    TRUST_TRANSFER_ENABLED_FIX_187,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_186,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_intent import (
    is_independent_repository_trust_expansion_intent,
    parse_independent_repository_trust_expansion_record_intent,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_service import (
    build_independent_repository_trust_expansion,
    clear_independent_repository_trust_expansion_cache_for_tests,
)
from aethos_core.mission_control.independent_repository_trust_expansion.independent_repository_trust_expansion_store import (
    append_independent_repository_trust_expansion_record,
    clear_independent_repository_trust_expansion_records_for_tests,
)
from tests.test_mission_control_dogfood_pilot_trust_report_freeze import _dogfood_trust_stack


@pytest.fixture(autouse=True)
def _clean():
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_cache_for_tests()
    get_settings.cache_clear()
    yield
    clear_independent_repository_trust_expansion_records_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    clear_independent_repository_trust_expansion_cache_for_tests()
    get_settings.cache_clear()


def _trust_expansion_stack(session_id: str = "fix-187-test") -> None:
    from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
        append_dogfood_pilot_trust_report_freeze_record,
    )

    _dogfood_trust_stack()
    append_dogfood_pilot_trust_report_freeze_record(
        session_id=session_id,
        kind="trust_report_freeze_artifact",
        content="AethOS dogfood Phase 1 baseline for FIX 187 tests",
    )
    append_dogfood_pilot_trust_report_freeze_record(
        session_id=session_id,
        kind="operator_review_note",
        content="Operator reviewed FIX 187 test freeze",
    )


def test_independent_repository_trust_expansion_intent():
    assert is_independent_repository_trust_expansion_intent("show repository trust expansion")
    assert not is_independent_repository_trust_expansion_intent("inherit trust from aethos")


def test_repo_expansion_record_intent():
    parsed = parse_independent_repository_trust_expansion_record_intent(
        "repo expansion: pilotmain/pilot-os-ui approved for independent pilot arc"
    )
    assert parsed == ("repo_expansion_approval", "pilotmain/pilot-os-ui approved for independent pilot arc")


def test_build_trust_expansion_registry():
    _trust_expansion_stack()
    result = build_independent_repository_trust_expansion(session_id="fix-187-test")
    assert result.ok is True
    report = result.independent_repository_trust_expansion
    assert report["trust_transfer_enabled"] is TRUST_TRANSFER_ENABLED_FIX_187
    assert report["pilot_execution_performed"] is False
    assert report["phase_1_complete"] is True

    registry = report["sections"]["repository_trust_registry"]
    aethos = next(r for r in registry if r["repository"] == PHASE_1_REPOSITORY)
    assert aethos["trust_state"] == "CONDITIONALLY_TRUSTED"
    assert aethos["trust_inherited_from"] is None

    pilotos = next(r for r in registry if r["repository"] == PHASE_2_REPOSITORY_ORDER[0])
    assert pilotos["trust_state"] == "UNPROVEN"
    reqs = pilotos["expansion_requirements"]["requirements"]
    if not reqs.get("operator_expansion_approval_recorded"):
        assert pilotos["expansion_requirements"]["eligible_for_pilot_entry"] is False

    section_keys = set(report["sections"])
    assert not section_keys.intersection(UPSTREAM_SECTIONS_OWNED_BY_FIX_186)


def test_phase2_repo_not_trusted_from_aethos_success():
    _trust_expansion_stack()
    result = build_independent_repository_trust_expansion(session_id="fix-187-test")
    registry = result.independent_repository_trust_expansion["sections"]["repository_trust_registry"]
    for repo in PHASE_2_REPOSITORY_ORDER:
        row = next(r for r in registry if r["repository"] == repo)
        assert row["trust_state"] != "CONDITIONALLY_TRUSTED"
        assert row["trust_inherited_from"] is None


def test_repo_expansion_approval_enables_pilotos_eligibility():
    _trust_expansion_stack()
    append_independent_repository_trust_expansion_record(
        session_id="fix-187-test",
        kind="repo_expansion_approval",
        content="Operator approves pilotmain/pilot-os-ui for independent pilot arc",
        repository=PHASE_2_REPOSITORY_ORDER[0],
    )
    result = build_independent_repository_trust_expansion(session_id="fix-187-test")
    registry = result.independent_repository_trust_expansion["sections"]["repository_trust_registry"]
    pilotos = next(r for r in registry if r["repository"] == PHASE_2_REPOSITORY_ORDER[0])
    assert pilotos["expansion_requirements"]["requirements"]["operator_expansion_approval_recorded"] is True


def test_chat_route_show_repository_trust_expansion():
    _trust_expansion_stack(session_id="fix-187-chat")
    turn = resolve_chat_turn("show repository trust expansion", session_id="fix-187-chat")
    assert turn.intent == "mission_control_independent_repository_trust_expansion"
    assert (turn.meta or {}).get("route_id") == INDEPENDENT_REPOSITORY_TRUST_EXPANSION_ROUTE_ID


def test_trust_expansion_api():
    _trust_expansion_stack(session_id="fix-187-api")
    client = TestClient(app)
    response = client.get(
        "/api/v1/mission-control/independent-repository-trust-expansion",
        params={"session_id": "fix-187-api", "format": "both"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["trust_transfer_enabled"] is False
    assert payload["independent_repository_trust_expansion"]["phase_1_complete"] is True
