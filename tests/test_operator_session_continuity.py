# SPDX-License-Identifier: Apache-2.0
"""Operator session continuity — shared session id and follow-up routing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.cli.operator_cli import OPERATOR_DEFAULT_SESSION_ID
from aethos_core.operational_session import clear_operational_sessions_for_tests
from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
from aethos_core.operational_session.operational_readonly_goal import is_operational_kernel_candidate
from aethos_core.operational_session.operational_runtime import run_operational_turn


@pytest.fixture(autouse=True)
def _clean_sessions():
    clear_operational_sessions_for_tests()
    yield
    clear_operational_sessions_for_tests()


def test_operator_default_session_id_is_shared() -> None:
    assert OPERATOR_DEFAULT_SESSION_ID == "operator"


def test_what_about_api_resolves_explicit_railway_service() -> None:
    resolved = resolve_active_subject("what about api?", session_id="cold")
    assert resolved.subject.provider == "railway"
    assert resolved.subject.service == "aethos-api"
    assert is_operational_kernel_candidate("what about api?", session_id="cold")


def test_continuity_no_match_explains_session_id() -> None:
    with patch(
        "aethos_core.operational_session.kernel_router.route_operational_conversation_kernel_turn",
        return_value=None,
    ):
        result = run_operational_turn("what about api?", session_id="empty-session", channel="cli")
    assert result.ok is False
    assert "same session" in result.reply.lower()
    assert OPERATOR_DEFAULT_SESSION_ID in result.reply


def test_inventory_subject_label_helpers() -> None:
    from aethos_core.operational_session.session_subject import format_inventory_subject_label, inventory_session_subject

    label = format_inventory_subject_label(provider="railway", project_count=14, environment_count=9, service_count=31)
    assert label == "railway / 14 projects · 9 environments · 31 services"
    subject = inventory_session_subject(provider="vercel", project_count=15)
    assert subject.path_label() == "vercel / 15 projects"


def test_follow_up_after_inventory_same_session(monkeypatch) -> None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )

    monkeypatch.setattr(
        "aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks.safe_run_deployment_readiness_checks",
        lambda **kwargs: {
            "railway_credential_ok": True,
            "railway_api_connection_ok": True,
            "inventory": {
                "ok": True,
                "project_count": 1,
                "environment_count": 1,
                "service_count": 1,
                "projects": [{"name": "pilotos", "environments": [{"name": "production", "services": ["aethos-api"]}]}],
            },
        },
    )
    sid = OPERATOR_DEFAULT_SESSION_ID
    first = run_operational_turn("show Railway projects", session_id=sid, channel="cli")
    assert first.ok is True
    from aethos_core.operational_session.operational_session import operational_session_meta

    meta = operational_session_meta(session_id=sid)
    assert "railway /" in str(meta.get("last_subject_label"))
    assert meta.get("continue_hint")
    second = run_operational_turn("what about api?", session_id=sid, channel="cli")
    assert second.ok is True
    assert "operational_kernel" in second.intent
