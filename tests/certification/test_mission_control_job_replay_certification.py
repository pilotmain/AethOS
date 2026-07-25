# SPDX-License-Identifier: Apache-2.0
"""FIX 137 — Mission Control job replay certification."""

from __future__ import annotations

import pytest

from aethos_core.mission_control.job_replay.job_replay_contract import (
    JOB_REPLAY_FIX,
    JOB_REPLAY_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_137,
)
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from aethos_core.mission_control.mission_control_ui_freeze_review import review_mission_control_operator_api_surface
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mc-replay-cert-137"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    clear_for_tests()
    yield
    clear_for_tests()


class TestMissionControlJobReplayCertification:
    def test_fix_137_contract(self) -> None:
        assert JOB_REPLAY_FIX == "FIX 137"
        assert JOB_REPLAY_SCHEMA_VERSION == "mission_control_job_replay_v1"
        assert MUTATION_PERFORMED_FIX_137 is False

    def test_replay_readonly_from_evidence_bundle(self) -> None:
        _full_stack(SESSION)
        result = build_job_replay(session_id=SESSION)
        assert result.ok is True
        assert result.replay["read_only"] is True
        assert result.replay["mutation_performed"] is False
        assert result.replay["step_count"] >= 1

    def test_operator_api_includes_job_replay_route(self) -> None:
        review = review_mission_control_operator_api_surface()
        assert review["ok"] is True
        paths = [row["path"] for row in review["routes"]]
        assert "/mission-control/job-replay" in paths
        assert "/mission-control/job-replay/resolve" in paths

    def test_replay_steps_expose_link_keys(self) -> None:
        _full_stack(SESSION)
        result = build_job_replay(session_id=SESSION)
        step = result.replay["steps"][0]
        assert step.get("link_key")
        assert isinstance(result.replay.get("link_index"), dict)
