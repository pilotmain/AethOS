# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — Mission Control evidence bundle export."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from aethos_core.api.main import app
from aethos_core.config import get_settings
from aethos_core.mission_control.evidence_bundle.evidence_bundle_redaction import redact_dict
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from tests.test_software_delivery_pr_draft import _full_stack


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.mission_control.approval_inbox.approval_execution_service import clear_ui_approval_audit_for_tests
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_ui_approval_audit_for_tests()
    get_settings.cache_clear()


def test_evidence_bundle_api_readonly_json():
    session = "mc-evidence-136"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/evidence-bundle",
        params={"session_id": session, "format": "json"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["read_only"] is True
    assert body["mutation_performed"] is False
    bundle = body["bundle"]
    assert bundle["schema_version"] == "mission_control_evidence_bundle_v1"
    assert bundle["session_id"] == session
    assert bundle["mission"]["correlation_id"]
    assert "snapshot" in bundle
    assert "timeline" in bundle
    assert "approvals" in bundle
    assert "lane_drilldowns" in bundle
    assert "software_delivery" in bundle["lane_drilldowns"]


def test_evidence_bundle_markdown_format():
    session = "mc-evidence-md-136"
    _full_stack(session)
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/evidence-bundle",
        params={"session_id": session, "format": "markdown"},
    )
    assert res.status_code == 200
    body = res.json()
    assert "Operator Evidence Bundle" in body["markdown"]
    assert body["read_only"] is True


def test_evidence_bundle_both_format():
    session = "mc-evidence-both-136"
    _full_stack(session)
    result = build_evidence_bundle(session_id=session)
    assert result.ok
    assert result.bundle["blockers"] is not None
    assert result.bundle["verification"] is not None
    assert result.bundle["receipts"] is not None


def test_redact_sensitive_keys():
    payload = {
        "api_key": "secret-value",
        "nested": {"github_token": "ghp_abcdefghijklmnopqrst"},
        "safe": "visible",
    }
    redacted = redact_dict(payload)
    assert redacted["api_key"] == "[REDACTED]"
    assert redacted["nested"]["github_token"] == "[REDACTED]"
    assert redacted["safe"] == "visible"


def test_evidence_bundle_unsupported_format():
    client = TestClient(app)
    res = client.get(
        "/api/v1/mission-control/evidence-bundle",
        params={"session_id": "default", "format": "pdf"},
    )
    assert res.status_code == 400
