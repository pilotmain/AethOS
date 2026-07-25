# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
from aethos_core.operational_session.operational_session import record_operational_turn
from aethos_core.operational_session.provider_routing_proof import evaluate_provider_routing
from aethos_core.operational_session.session_subject import SessionSubject
from aethos_core.operational_session import clear_operational_sessions_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_operational_sessions_for_tests()
    yield
    clear_operational_sessions_for_tests()


def test_killit_on_railway_keeps_railway_provider_not_vercel_project():
    killit_row = {
        "target_id": "dt-killit",
        "alias": "killit",
        "vercel_project": "killit",
        "default_provider": "vercel",
    }
    with patch(
        "aethos_core.deployment_targets.registry.match_aliases_in_text",
        return_value=killit_row,
    ):
        resolved = resolve_active_subject("show logs for killit on railway", session_id="t1")

    assert resolved.subject.provider == "railway"
    assert resolved.subject.vercel_project == ""
    assert resolved.subject.service == "killit"


def test_invalid_project_overrides_stale_killit_session():
    record_operational_turn(
        session_id="t2",
        user_text="top 5 logs for killit",
        subject=SessionSubject(provider="vercel", vercel_project="killit", project="killit"),
        operation="fetch_logs",
        reply_intent="operational_kernel_fetch_logs",
        result_summary="ok",
    )
    resolved = resolve_active_subject("show logs for invalid-project-xyz", session_id="t2")
    assert resolved.subject.vercel_project == "invalid-project-xyz"
    assert resolved.subject.project == "invalid-project-xyz"
    assert resolved.subject.vercel_project != "killit"


def test_killit_on_railway_routing_marks_misroute_when_resolved_vercel():
    routing = evaluate_provider_routing(
        request="show logs for killit on railway",
        resolved_provider="vercel",
    )
    assert routing.requested_provider == "railway"
    assert routing.provider_misroute is True
