# SPDX-License-Identifier: Apache-2.0
"""Stop follow-up questions route to mutation execution truth."""

from __future__ import annotations

from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent, is_readonly_operational_request
from aethos_core.chat.mutation_execution_chat import compose_mutation_execution_truth_reply, is_mutation_execution_truth_intent


def test_did_you_stop_is_readonly_not_new_stop_intent():
    text = "did you stop the projects.service?"
    assert is_readonly_operational_request(text)
    assert is_mutation_execution_truth_intent(text)
    assert detect_explicit_mutation_intent(text) is None


def test_stop_outcome_truth_without_execution_job():
    reply, intent, _meta = compose_mutation_execution_truth_reply(
        "did you stop the projects?",
        session_id="truth-stop-empty",
    )
    assert intent == "mutation_execution_truth"
    assert "couldn't find" in reply.lower() or "execution job" in reply.lower()
