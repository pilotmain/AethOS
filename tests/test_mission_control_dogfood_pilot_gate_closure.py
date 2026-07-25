# SPDX-License-Identifier: Apache-2.0
"""FIX 181–186 — dogfood pilot gate closure tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.dogfood_pilot_gate_closure.dogfood_pilot_gate_closure_service import (
    build_dogfood_pilot_gate_closure,
)
from aethos_core.mission_control.dogfood_pilot_trust_report_freeze.dogfood_pilot_trust_report_freeze_store import (
    append_dogfood_pilot_trust_report_freeze_record,
    clear_dogfood_pilot_trust_report_freeze_records_for_tests,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    clear_end_to_end_repo_development_pilot_harness_records_for_tests,
    persist_pilot_run_audit,
)
from tests.test_mission_control_dogfood_pilot_trust_report_freeze import _seed_dogfood_pilot_audits
from tests.test_mission_control_pilot_validation_trust_board import _validation_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.dogfood_pilot_gate_closure.dogfood_pilot_gate_closure_service import (
        clear_dogfood_pilot_gate_closure_cache_for_tests,
    )
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()
    clear_dogfood_pilot_gate_closure_cache_for_tests()
    yield
    clear_dogfood_pilot_gate_closure_cache_for_tests()
    clear_dogfood_pilot_trust_report_freeze_records_for_tests()
    clear_end_to_end_repo_development_pilot_harness_records_for_tests()
    get_settings.cache_clear()


def test_gate_closure_partial_without_records():
    _seed_dogfood_pilot_audits()
    result = build_dogfood_pilot_gate_closure(session_id="operator")
    assert result.ok is False
    checklist = result.dogfood_pilot_gate_closure.get("checklist") or []
    assert len(checklist) == 6
    fix186 = next(row for row in checklist if row.get("fix") == "FIX 186")
    assert fix186.get("passed") is False
    assert "trust_report_freeze_not_recorded" in fix186.get("blockers", [])


def test_gate_closure_complete_with_freeze_and_review():
    _validation_stack("operator")
    _seed_dogfood_pilot_audits()
    persist_pilot_run_audit(
        {
            "session_id": "operator",
            "repo_issue": "pilotmain/AethOS#1",
            "outcome": "complete",
            "stages_completed": ["pr_open"],
            "blockers": [],
        }
    )
    append_dogfood_pilot_trust_report_freeze_record(
        session_id="operator",
        kind="trust_report_freeze_artifact",
        content="Pilots 1–3 baseline for AethOS dogfood",
    )
    append_dogfood_pilot_trust_report_freeze_record(
        session_id="operator",
        kind="operator_review_note",
        content="Operator reviewed freeze",
    )
    result = build_dogfood_pilot_gate_closure(session_id="operator")
    checklist = result.dogfood_pilot_gate_closure.get("checklist") or []
    passed = [row for row in checklist if row.get("passed")]
    assert len(passed) >= 4
    fix181 = next(row for row in checklist if row.get("fix") == "FIX 181")
    assert fix181.get("passed") is True
    fix186 = next(row for row in checklist if row.get("fix") == "FIX 186")
    assert fix186.get("passed") is True


def test_gate_closure_api():
    client = TestClient(app)
    r = client.get("/api/v1/mission-control/dogfood-pilot-gate-closure", params={"session_id": "gate-api"})
    assert r.status_code == 200
    body = r.json()
    assert body.get("read_only") is True
    assert body.get("dogfood_pilot_gate_closure", {}).get("gates_total") == 6
