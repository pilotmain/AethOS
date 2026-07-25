# SPDX-License-Identifier: Apache-2.0
"""FIX 90 — Browser observation lifecycle and follow-up ownership."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.browser_observation.browser_observation_followup_router import (
    is_browser_observation_followup_intent,
    route_browser_observation_followup,
)
from aethos_core.browser_observation.browser_observation_lifecycle import (
    clear_lifecycle_for_tests,
    load_latest_browser_observation,
    persist_browser_observation,
)
from aethos_core.browser_observation.browser_observation_router import (
    is_browser_observation_capture_intent,
    is_browser_observation_intent,
    route_browser_observation,
    route_browser_observation_lane,
)
from aethos_core.chat.service import resolve_chat_turn


def setup_function() -> None:
    clear_lifecycle_for_tests()


def test_followup_intent_detection() -> None:
    for phrase in (
        "show me the screenshot",
        "open the screenshot",
        "where is the screenshot saved?",
        "what did the screenshot show?",
        "are you capable of taking screenshots?",
    ):
        assert is_browser_observation_followup_intent(phrase), phrase


def test_open_screenshot_not_capture_intent() -> None:
    assert is_browser_observation_followup_intent("open the screenshot")
    assert not is_browser_observation_capture_intent("open the screenshot")
    assert not is_browser_observation_intent("open the screenshot")


@patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
@patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=True)
def test_persist_and_followup_show(_ready, mock_inspect) -> None:
    mock_inspect.return_value = {
        "env_flag_loaded": True,
        "playwright_python_package_installed": True,
        "chromium_binary_installed": True,
        "browser_launch_test": "pass",
        "worker_enabled": True,
    }
    persist_browser_observation(
        "sess-90",
        {
            "artifact_id": "bart-19f5d290be01",
            "url": "https://pilotmain.com",
            "type": "screenshot",
            "timestamp": "2026-05-26T12:00:00+00:00",
            "artifacts": [],
            "status": "captured",
            "artifact_file_url": "/api/v1/browser/artifacts/bart-19f5d290be01/file",
        },
    )
    loaded = load_latest_browser_observation(session_id="sess-90")
    assert loaded is not None
    assert loaded["artifact_id"] == "bart-19f5d290be01"

    result = route_browser_observation_followup("show me the screenshot", session_id="sess-90")
    assert result is not None
    body, intent, meta = result
    assert intent == "browser_observation_show_artifact"
    assert "bart-19f5d290be01" in body
    assert meta.get("browser_observation_hydrated") == "true"
    assert meta.get("blocked_handlers")
    assert "front_door" in meta.get("blocked_handlers", "")


@patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture")
@patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=True)
@patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
def test_lane_capture_then_followup_via_chat(mock_inspect, _ready, mock_capture) -> None:
    mock_inspect.return_value = {"browser_launch_test": "pass", "execution_ready": True}
    mock_capture.return_value = {
        "ok": True,
        "summary": "ok",
        "artifacts": [
            {
                "artifact_id": "bart-lane-1",
                "artifact_type": "browser_screenshot",
                "artifact_file_url": "/api/v1/browser/artifacts/bart-lane-1/file",
            }
        ],
    }
    session = "chat-lifecycle-90"
    cap = resolve_chat_turn(
        "take a screenshot of pilotmain.com",
        session_id=session,
        apply_relational_layer=False,
    )
    assert cap.intent == "browser_observation_captured"

    show = resolve_chat_turn("show me the screenshot", session_id=session, apply_relational_layer=False)
    assert show.intent == "browser_observation_show_artifact"
    assert "bart-lane-1" in show.reply
    assert "How I can help" not in show.reply


@patch("aethos_core.browser_observation.browser_observation_router.route_browser_observation_lane")
def test_resolve_chat_turn_uses_lane_router(mock_lane) -> None:
    mock_lane.return_value = ("ok", "browser_observation_captured", {"route_id": "browser_observation"})
    result = resolve_chat_turn("take a screenshot of pilotmain.com", session_id="lane", apply_relational_layer=False)
    assert result.intent == "browser_observation_captured"
    mock_lane.assert_called_once()
