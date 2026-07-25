# SPDX-License-Identifier: Apache-2.0
"""Front-door intent classification tests."""

from __future__ import annotations

import pytest

from aethos_core.chat.front_door_intent import (
    classify_front_door_intent,
    is_casual_greeting,
    is_capability_question,
    should_skip_operational_cognition,
)
from aethos_core.operational_planner.provider_wide_health_store import clear_provider_wide_health_for_tests
from aethos_core.response_composition.response_composer import store_provider_wide_health_result
from aethos_core.world_model.world_state_store import clear_world_model_for_tests


@pytest.fixture(autouse=True)
def _clean():
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()
    yield
    clear_provider_wide_health_for_tests()
    clear_world_model_for_tests()


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Hi", "casual_greeting"),
        ("hello", "casual_greeting"),
        ("what are you capable of?", "capability_intro"),
        ("what can you do", "capability_intro"),
        ("help", "general_help"),
        ("why is MongoDB failed", "operational_query"),
        ("restart MongoDB", "mutation_request"),
        ("what do we know so far about MongoDB", "investigation_followup"),
    ],
)
def test_classify_front_door_intent(text: str, expected: str) -> None:
    assert classify_front_door_intent(text) == expected


def test_is_casual_greeting() -> None:
    assert is_casual_greeting("Hi")
    assert is_casual_greeting("hello!")
    assert not is_casual_greeting("why is MongoDB failed")


def test_is_capability_question() -> None:
    assert is_capability_question("what are you capable of?")
    assert is_capability_question("what can you do")
    assert not is_capability_question("restart MongoDB")


def test_should_skip_operational_cognition_for_casual_prompts() -> None:
    assert should_skip_operational_cognition("Hi")
    assert should_skip_operational_cognition("what are you capable of?")
    assert should_skip_operational_cognition("help")
    assert not should_skip_operational_cognition("why is MongoDB failed")
    assert not should_skip_operational_cognition("what do we know so far about MongoDB")
