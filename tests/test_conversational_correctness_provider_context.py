# SPDX-License-Identifier: Apache-2.0
"""Regression tests for the conversational-correctness handoff.

Reproduces the exact Railway conversation that produced wrong answers:

  1. Railway health turn → "give me 10 top logs for both"
       expect: Railway, both services (aethos-api + aethos-ui) — never Vercel,
       never a literal project named "both".
  2. "check why we see this issue in aethos railway?"
       expect: no email/IMAP path — the email tool is not even advertised.
  3. "list all projects in vercel" after an unfinished Railway redeploy
       expect: Vercel, not a stale Railway redeploy prompt.

These guard §2 (explicit email intent), §3 (stale continuations yield),
§4 (entity/quantifier inheritance) and §5 (explicit provider wins + honest
ambiguity). They are deterministic unit-level checks (no LLM) so they stay green.
"""

from __future__ import annotations

import pytest

from aethos_core.execution_brain.agent_tool_executor import (
    agent_tool_schemas,
    is_explicit_email_intent,
)
from aethos_core.execution_brain.goal_planner import _infer_provider_from_subject
from aethos_core.operational_session.active_subject_resolver import resolve_active_subject
from aethos_core.operational_session.operational_session import (
    load_operational_session,
    save_operational_session,
)
from aethos_core.operational_session.session_store import clear_operational_sessions_for_tests
from aethos_core.operational_session.session_subject import SessionSubject
from aethos_core.task_frame.railway_redeploy_continuation import (
    _redeploy_frame_should_yield,
    compose_railway_redeploy_continuation_reply,
)
from aethos_core.task_frame.railway_redeploy_intent import (
    RailwayRedeployIntent,
    clear_railway_redeploy_intents_for_tests,
    get_railway_redeploy_intent,
    save_railway_redeploy_intent,
)


@pytest.fixture(autouse=True)
def _reset_state():
    clear_operational_sessions_for_tests()
    clear_railway_redeploy_intents_for_tests()
    yield
    clear_operational_sessions_for_tests()
    clear_railway_redeploy_intents_for_tests()


def _establish_railway_health_turn(session_id: str) -> None:
    """Simulate the prior Railway health turn that set the active subject."""
    session = load_operational_session(session_id=session_id)
    session.subject = SessionSubject(
        provider="railway",
        project="aethos",
        services=["aethos-api", "aethos-ui"],
        environment="production",
        subject_source="session",
    )
    session.context.last_operation = "health_check"
    save_operational_session(session)


# ─────────────────────────────── §4 ────────────────────────────────────────


def test_logs_for_both_inherits_railway_and_both_services():
    sid = "tcc-both"
    _establish_railway_health_turn(sid)

    resolved = resolve_active_subject("give me 10 top logs for both", session_id=sid)

    assert resolved.subject.provider == "railway"
    assert "aethos-api" in resolved.subject.services
    assert "aethos-ui" in resolved.subject.services
    # "both" must never be treated as a literal Vercel/Railway project name.
    assert resolved.subject.vercel_project == ""
    assert resolved.subject.project != "both"


def test_quantifier_them_those_resolve_to_prior_entities():
    sid = "tcc-them"
    _establish_railway_health_turn(sid)
    for phrase in ("logs for them", "logs for those"):
        resolved = resolve_active_subject(phrase, session_id=sid)
        assert resolved.subject.provider == "railway", phrase
        assert resolved.subject.vercel_project == "", phrase


# ─────────────────────────────── §5 ────────────────────────────────────────


def test_explicit_vercel_wins_for_project_list():
    sid = "tcc-vercel"
    # Even with a prior Railway context, an explicit Vercel ask resolves to Vercel.
    _establish_railway_health_turn(sid)
    resolved = resolve_active_subject("list all projects in vercel", session_id=sid)
    assert resolved.subject.provider == "vercel"


def test_logs_for_both_without_context_is_ambiguous_not_vercel():
    # No prior context: "both" must not become "No Vercel project named both".
    resolved = resolve_active_subject("give me 10 top logs for both", session_id="tcc-fresh")
    assert resolved.subject.provider == ""
    assert resolved.subject.vercel_project == ""
    assert resolved.subject.project == ""
    assert resolved.needs_clarification is True


def test_infer_provider_never_picks_vercel_from_garbage_hint():
    garbage = SessionSubject(provider="", vercel_project="both")
    assert _infer_provider_from_subject(garbage) == "railway"
    real = SessionSubject(provider="", vercel_project="killit")
    assert _infer_provider_from_subject(real) == "vercel"


# ─────────────────────────────── §3 ────────────────────────────────────────


def test_stale_redeploy_frame_yields_to_vercel_list():
    sid = "tcc-redeploy"
    save_railway_redeploy_intent(
        RailwayRedeployIntent(
            session_id=sid,
            original_request="redeploy aethos-api",
            environment="staging",
            service_hints=["aethos-api"],
        )
    )
    assert get_railway_redeploy_intent(session_id=sid) is not None

    out = compose_railway_redeploy_continuation_reply("list all projects in vercel", session_id=sid)

    # The continuation must yield (None) AND clear the stale frame.
    assert out is None
    assert get_railway_redeploy_intent(session_id=sid) is None


def test_redeploy_frame_does_not_yield_to_genuine_followups():
    # Environment reply / redeploy keyword must NOT be treated as a fresh request.
    assert _redeploy_frame_should_yield("lets do staging") is False
    assert _redeploy_frame_should_yield("staging") is False
    assert _redeploy_frame_should_yield("redeploying with latest changes?") is False
    assert _redeploy_frame_should_yield("retrigger the deployment") is False
    # Bare target selections mid-redeploy must NOT yield.
    assert _redeploy_frame_should_yield("both") is False
    assert _redeploy_frame_should_yield("aethos-api") is False
    assert _redeploy_frame_should_yield("1") is False
    # Fresh, unrelated requests must yield.
    assert _redeploy_frame_should_yield("list all projects in vercel") is True
    assert _redeploy_frame_should_yield("give me 10 top logs for both") is True


def test_redeploy_frame_yields_on_stop_redirect_and_other_provider():
    # §1 — explicit stop/redirect must be honored even when "railway" is named.
    assert _redeploy_frame_should_yield("don't talk about railway, I'm asking to list vercel projects") is True
    assert _redeploy_frame_should_yield("not railway — show me vercel") is True
    assert _redeploy_frame_should_yield("actually, show me the logs") is True
    # Bare fresh read-only verbs are a different operation.
    assert _redeploy_frame_should_yield("health") is True
    assert _redeploy_frame_should_yield("show me the status") is True


def test_stop_redirect_phrasing_clears_stale_redeploy_frame():
    sid = "tcc-redirect"
    save_railway_redeploy_intent(
        RailwayRedeployIntent(
            session_id=sid,
            original_request="redeploy aethos-api",
            environment="staging",
            service_hints=["aethos-api"],
        )
    )
    out = compose_railway_redeploy_continuation_reply(
        "don't talk about railway, I'm asking to list vercel projects", session_id=sid
    )
    assert out is None
    assert get_railway_redeploy_intent(session_id=sid) is None


def test_continuation_ttl_expires_stale_redeploy_frame():
    # §1 — an abandoned redeploy frame expires after the conversational TTL.
    from datetime import UTC, datetime, timedelta

    sid = "tcc-ttl"
    intent = RailwayRedeployIntent(
        session_id=sid,
        original_request="redeploy aethos-api",
        environment="staging",
        service_hints=["aethos-api"],
    )
    # Stamp creation well beyond the TTL window (default 30 min).
    intent.created_at = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    save_railway_redeploy_intent(intent)
    # Reading it back must treat it as stale and clear it.
    assert get_railway_redeploy_intent(session_id=sid) is None


# ─────────────────────────────── §2 ────────────────────────────────────────


def test_email_intent_only_on_explicit_email_prompts():
    assert is_explicit_email_intent("check why we see this issue in aethos railway?") is False
    assert is_explicit_email_intent("check this issue") is False
    assert is_explicit_email_intent("restart the api service") is False
    assert is_explicit_email_intent("check my email") is True
    assert is_explicit_email_intent("triage inbox") is True
    assert is_explicit_email_intent("any urgent mail") is True


def test_email_tool_withheld_on_non_email_prompt():
    from aethos_core.config import get_settings

    if not get_settings().workspace_suite_enabled:
        pytest.skip("workspace suite disabled in this environment")
    railway_tools = {t["name"] for t in agent_tool_schemas(for_prompt="check why we see this issue in aethos railway?")}
    email_tools = {t["name"] for t in agent_tool_schemas(for_prompt="check my email inbox")}
    assert "workspace_email" not in railway_tools
    assert "workspace_email" in email_tools
