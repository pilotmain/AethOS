# SPDX-License-Identifier: Apache-2.0
"""FIX 185 — Mission Control issue intake scope fidelity API."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.software_delivery.issue_plan_store import clear_for_tests, save_issue_plan


def test_issue_intake_scope_fidelity_api_without_plan():
    clear_for_tests()
    client = TestClient(app)
    r = client.get("/api/v1/mission-control/issue-intake-scope-fidelity", params={"session_id": "f185-api"})
    assert r.status_code == 503
    assert "no_issue_plan" in str(r.json())


def test_issue_intake_scope_fidelity_api_with_plan():
    clear_for_tests()
    save_issue_plan(
        {
            "plan_id": "plan-f185-api",
            "session_id": "f185-api",
            "issue_title": "Add pilot execution log section",
            "issue_body": "# Scope\n- `docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md`\n",
            "governed_plan": {"goal": "Add pilot execution log section to dogfood doc"},
            "affected_files": ["docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"],
            "issue_intake_scope_fidelity": {
                "intended_goal": "Add pilot execution log section",
                "expected_files": ["docs/AETHOS_DOGFOOD_AND_PILOT_VALIDATION_PRINCIPLE.md"],
                "explicit_bounded_scope": True,
                "scope_confidence": "high",
                "forbidden_file_prefixes": [],
                "out_of_scope_constraints": [],
            },
        }
    )
    client = TestClient(app)
    r = client.get("/api/v1/mission-control/issue-intake-scope-fidelity", params={"session_id": "f185-api"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["fix"] == "FIX 185"
    assert body["assessment"]["fidelity_score"] >= 70
    clear_for_tests()
