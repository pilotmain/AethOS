# SPDX-License-Identifier: Apache-2.0
"""Provider-generic follow-up intent classifier tests."""

from __future__ import annotations

from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent, parse_log_limit
from aethos_core.operational_thread_memory.thread_state import OperationalThreadState


def _thread() -> OperationalThreadState:
    return OperationalThreadState(
        session_id="classifier-test",
        provider="railway",
        project="pilotos",
        environment="production",
        service="pilotos-api",
        operation="restart",
        status="stabilizing",
    )


def test_did_restart_actually_happened_is_verify_operation():
    intent = classify_followup_intent("did the restart actually happened?", _thread())
    assert intent is not None
    assert intent.intent == "verify_operation"
    assert intent.include_verification is True


def test_did_it_really_go_through_is_verify_operation():
    intent = classify_followup_intent("did it really go through?", _thread())
    assert intent is not None
    assert intent.intent == "verify_operation"


def test_top_5_latest_logs_is_fetch_top_n_logs():
    intent = classify_followup_intent("give me top 5 latest logs", _thread())
    assert intent is not None
    assert intent.intent == "fetch_top_n_logs"
    assert intent.log_limit == 5


def test_show_recent_logs_is_fetch_logs():
    intent = classify_followup_intent("show recent logs", _thread())
    assert intent is not None
    assert intent.intent == "fetch_logs"
    assert intent.include_logs is True


def test_check_if_restarted_is_verify_operation():
    intent = classify_followup_intent("check if it restarted", _thread())
    assert intent is not None
    assert intent.intent == "verify_operation"


def test_update_me_when_done_is_watch_until_done():
    intent = classify_followup_intent("update me when done", _thread())
    assert intent is not None
    assert intent.intent == "watch_until_done"


def test_why_failed_is_explain_failure():
    intent = classify_followup_intent("why did it fail?", _thread())
    assert intent is not None
    assert intent.intent == "explain_failure"


def test_combined_verify_and_top_logs():
    intent = classify_followup_intent(
        "i want you to check if actually restart happend and give me top 5 latest logs",
        _thread(),
    )
    assert intent is not None
    assert intent.intent == "fetch_top_n_logs"
    assert intent.log_limit == 5
    assert intent.include_verification is True


def test_parse_log_limit_top_10():
    assert parse_log_limit("show me top 10 logs") == 10
