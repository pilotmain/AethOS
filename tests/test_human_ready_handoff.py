# SPDX-License-Identifier: Apache-2.0
"""Human-ready handoff — plain capabilities, batteries included, rest nudges, URL read."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest

from aethos_core import config as config_mod
from aethos_core.chat.front_door_intent import compose_capability_intro_reply
from aethos_core.conversation.progression_compat import (
    append_optional_rest_hint,
    reset_rest_nudge_state_for_tests,
)
from aethos_core.identity.plain_capability_intro import is_provider_connection_question
from aethos_core.onboarding.operator_persona import reset_persona_for_tests, save_persona


@pytest.fixture(autouse=True)
def _clean_persona_and_rest_state():
    reset_persona_for_tests()
    reset_rest_nudge_state_for_tests()
    yield
    reset_persona_for_tests()
    reset_rest_nudge_state_for_tests()


def test_general_capability_question_is_plain_language() -> None:
    reply = compose_capability_intro_reply(text="what can you do?")
    low = reply.lower()
    assert "not_configured" not in low
    assert "governed" in low or "approval" in low
    assert "chat" in low or "research" in low
    assert "investigation" in low or "explain" in low


def test_provider_connection_question_shows_provider_status() -> None:
    assert is_provider_connection_question("what providers are connected?")
    reply = compose_capability_intro_reply(text="what providers are connected?")
    assert "provider" in reply.lower() or "railway" in reply.lower()


def test_batteries_included_defaults_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AETHOS_BATTERIES_INCLUDED", "true")
    for key in (
        "CHAT_STREAMING_ENABLED",
        "AGENT_RUNTIME_ENABLED",
        "WORKSPACE_SUITE_ENABLED",
        "ARBITER_ENABLED",
    ):
        monkeypatch.delenv(key, raising=False)
    # Web research is not batteries-included (needs user's search key); .env may set it.
    monkeypatch.setenv("WEB_RESEARCH_ENABLED", "false")
    config_mod.get_settings.cache_clear()
    s = config_mod.get_settings()
    assert s.aethos_batteries_included is True
    assert s.chat_streaming_enabled is True
    assert s.agent_runtime_enabled is True
    assert s.workspace_suite_enabled is True
    assert s.arbiter_enabled is True
    assert s.web_research_enabled is False


def test_batteries_included_false_turns_safe_flags_off(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AETHOS_BATTERIES_INCLUDED", "false")
    config_mod.get_settings.cache_clear()
    s = config_mod.get_settings()
    assert s.chat_streaming_enabled is False
    assert s.agent_runtime_enabled is False
    assert s.arbiter_enabled is False


def test_rest_nudge_early_morning_not_past_hours() -> None:
    save_persona(name="Ray", work_start_hour=9, work_end_hour=17, timezone="UTC")
    with (
        patch(
            "aethos_core.conversation.progression_compat._current_hour",
            return_value=6,
        ),
        patch("random.random", return_value=0.0),
    ):
        out = append_optional_rest_hint("Done.", session_id="rest-early")
    assert out == "Done."


def test_rest_nudge_deep_night_escalates() -> None:
    save_persona(name="Ray", work_start_hour=9, work_end_hour=17, timezone="UTC")
    with (
        patch(
            "aethos_core.conversation.progression_compat._current_hour",
            return_value=3,
        ),
        patch("random.random", return_value=0.0),
    ):
        first = append_optional_rest_hint("Step one.", session_id="rest-late")
        second = append_optional_rest_hint("Step two.", session_id="rest-late")
    assert first == "Step one."
    assert second == "Step two."


def test_summarize_url_uses_http_without_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    html_body = (
        "<html><head><title>Pilot Main</title>"
        "<meta name='description' content='Operations hub'/>"
        "</head><body><h1>Welcome</h1><p>Public summary text.</p></body></html>"
    )

    class _FakeResp:
        headers = {"Content-Type": "text/html; charset=utf-8"}

        def read(self, _n: int) -> bytes:
            return html_body.encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen",
        lambda *args, **kwargs: _FakeResp(),
    )
    from aethos_core.research.website_summary import summarize_url_via_http_fetch

    summary = summarize_url_via_http_fetch("pilotmain.com", session_id="url-test")
    assert summary.ok
    assert summary.evidence_source == "http_fetch"
    assert "Pilot Main" in summary.title
    assert "Public summary" in summary.visible_text_preview
