# SPDX-License-Identifier: Apache-2.0
"""FIX 127 — multi-agent certification."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.software_delivery.multi_agent.multi_agent_contract import (
    AGENT_FORBIDDEN_SCOPES,
    SELF_AUTHORIZING_FIX_127,
)
from aethos_core.software_delivery.multi_agent.multi_agent_receipts import clear_for_tests as clear_receipts
from aethos_core.software_delivery.multi_agent.multi_agent_store import clear_for_tests as clear_store
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.test_software_delivery_pr_draft import _full_stack

pytestmark = pytest.mark.certification

SESSION = "software-delivery-cert-127"


@pytest.fixture(autouse=True)
def _clean():
    from aethos_core.software_delivery.issue_plan_store import clear_for_tests

    reset_certification_runtime()
    clear_for_tests()
    clear_store()
    clear_receipts()
    get_settings.cache_clear()
    yield
    clear_for_tests()
    clear_store()
    clear_receipts()
    get_settings.cache_clear()
    reset_certification_runtime()


class TestSoftwareDeliveryMultiAgentCertification:
    def test_advisory_collaboration_lane(self) -> None:
        _full_stack(SESSION)
        result = resolve_chat_turn(
            "run software delivery agent collaboration",
            session_id=SESSION,
            apply_relational_layer=False,
        )
        assert_route_owns(result, route_id="software_delivery_issue_plan")
        assert result.intent == "software_delivery_agent_collaboration_completed"
        assert "merge" in " ".join(AGENT_FORBIDDEN_SCOPES)
        assert SELF_AUTHORIZING_FIX_127 is False
        assert result.meta.get("mutation_scope") == "multi_agent_advisory_only"
