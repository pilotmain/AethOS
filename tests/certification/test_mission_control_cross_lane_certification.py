# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control cross-lane certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "mission-control-cert-128"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    reset_certification_runtime()
    clear_for_tests()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestMissionControlCrossLaneCertification:
    def test_cross_lane_snapshot_readonly(self) -> None:
        _full_stack(SESSION)
        result = resolve_chat_turn(
            "show mission control snapshot",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="mission_control_cross_lane")
        assert result.meta.get("mutation_performed") == "false"
        assert "correlation_id" in result.reply
        assert "Attention queue" in result.reply or "attention" in result.reply.lower()
