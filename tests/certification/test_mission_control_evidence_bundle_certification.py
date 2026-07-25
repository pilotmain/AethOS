# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — Mission Control evidence bundle export certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.evidence_bundle.evidence_bundle_contract import (
    EVIDENCE_BUNDLE_FIX,
    EVIDENCE_BUNDLE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_136,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-evidence-cert-136"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    yield
    clear_for_tests()


class TestMissionControlEvidenceBundleCertification:
    def test_fix_136_contract(self) -> None:
        assert EVIDENCE_BUNDLE_FIX == "FIX 136"
        assert EVIDENCE_BUNDLE_SCHEMA_VERSION == "mission_control_evidence_bundle_v1"
        assert MUTATION_PERFORMED_FIX_136 is False

    def test_evidence_bundle_readonly_aggregate(self) -> None:
        _full_stack(SESSION)
        result = build_evidence_bundle(session_id=SESSION)
        assert result.ok is True
        bundle = result.bundle
        assert bundle["read_only"] is True
        assert bundle["mutation_performed"] is False
        assert bundle["timeline"] is not None
        assert bundle["approvals"]["pending_inbox"]["ok"] is True
        assert "software_delivery" in bundle["lane_drilldowns"]

    def test_operator_api_includes_evidence_bundle_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/evidence-bundle" in paths
