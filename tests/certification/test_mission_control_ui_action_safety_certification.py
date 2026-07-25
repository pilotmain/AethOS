# SPDX-License-Identifier: Apache-2.0
"""FIX 134 — Mission Control UI action safety certification."""

from __future__ import annotations

import pytest

from aethos_core.config import get_settings
from aethos_core.mission_control.approval_inbox.action_safety_contract import (
    FORBIDDEN_DIRECT_PROVIDER_CALLS,
    REQUIRED_UI_APPROVAL_ENTRYPOINT,
)
from aethos_core.mission_control.approval_inbox.action_safety_review import review_mission_control_ui_action_safety

pytestmark = pytest.mark.certification


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


class TestMissionControlUiActionSafetyCertification:
    def test_no_direct_provider_mutation_in_ui_path(self) -> None:
        review = review_mission_control_ui_action_safety()
        assert review["ok"] is True
        assert review["chat_governance_entrypoint"] == REQUIRED_UI_APPROVAL_ENTRYPOINT
        for sym in FORBIDDEN_DIRECT_PROVIDER_CALLS:
            assert sym not in review.get("execution_path_violations", [])
            assert sym not in review.get("api_route_violations", [])
