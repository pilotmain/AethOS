# SPDX-License-Identifier: Apache-2.0
"""HOTFIX 122B — production policy commands without enrollment."""

from __future__ import annotations

import pytest

from aethos_core.chat.service import resolve_chat_turn
from aethos_core.config import get_settings
from aethos_core.providers.railway.execution_contract.production_canary_shadow_policy_store import (
    clear_for_tests as clear_policy,
)
from aethos_core.providers.railway.execution_contract.production_policy_operator_views import (
    render_unenrolled_policy_view,
)
from aethos_core.providers.railway.execution_contract.production_rollout_journal import (
    clear_for_tests as clear_rollout_journal,
)
from tests.certification.helpers import assert_route_owns, reset_certification_runtime
from tests.certification.test_railway_production_verification_certification import (
    SESSION,
    _bootstrap_production_plan,
)


@pytest.fixture(autouse=True)
def _clean():
    reset_certification_runtime()
    clear_policy()
    clear_rollout_journal()
    get_settings.cache_clear()
    yield
    reset_certification_runtime()
    clear_policy()
    clear_rollout_journal()
    get_settings.cache_clear()


def test_static_unenrolled_policy_render():
    body = render_unenrolled_policy_view("canary_shadow_policy")
    assert "not enrolled" in body
    assert "execution_id: **none**" in body
    assert "live traffic mutation: **blocked**" in body
    assert "simulate production railway deployment" in body
    assert "No production mutation has been performed" in body


@pytest.mark.parametrize(
    "command,intent",
    [
        ("show railway production canary shadow policy", "railway_production_canary_shadow_policy"),
        (
            "show railway production rollout percentage governance",
            "railway_production_rollout_percentage_governance",
        ),
        (
            "show railway production canary health evidence",
            "railway_production_canary_health_evidence",
        ),
        (
            "show railway production canary rollback recommendation",
            "railway_production_canary_rollback_recommendation",
        ),
        ("show railway production rollout status", "railway_production_rollout_status"),
    ],
)
def test_policy_commands_without_enrollment(command: str, intent: str):
    session = "unenrolled-policy-122b"
    result = resolve_chat_turn(command, session_id=session, apply_relational_layer=False)
    assert result.intent == intent
    assert result.meta.get("enrollment") == "missing"
    assert result.meta.get("mutation_performed") in {None, "false"}
    assert "not enrolled" in result.reply
    assert "No production mutation has been performed" in result.reply


def test_enrolled_execution_renders_execution_specific_policy(monkeypatch):
    _bootstrap_production_plan(monkeypatch, SESSION)
    result = resolve_chat_turn(
        "show railway production canary shadow policy",
        session_id=SESSION,
        apply_relational_layer=False,
    )
    assert_route_owns(result, route_id="railway_production_canary_shadow_policy")
    assert "execution_id:" in result.reply
    assert "not enrolled" not in result.reply.lower() or "`rexec-" in result.reply
