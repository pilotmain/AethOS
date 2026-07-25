# SPDX-License-Identifier: Apache-2.0
"""FIX 89 — Browser observation direct execution lane."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.browser_observation.browser_observation_router import (
    compose_browser_blocked_reply,
    extract_target_url,
    is_browser_observation_intent,
    route_browser_observation,
)
from aethos_core.chat.service import resolve_chat_turn
from aethos_core.identity.capability_language import build_capability_overview
from aethos_core.provider_readonly_intent.readonly_provider_router import compose_readonly_provider_route_reply
from aethos_core.runtime.authority import authority


def test_screenshot_intent_detection() -> None:
    positives = [
        "take a screenshot of pilotmain.com",
        "capture pilotmain.com",
        "snapshot https://pilotmain.com",
        "inspect pilotmain.com",
        "open pilotmain.com",
        "check homepage",
        "inspect the landing page",
        "capture the landing page",
    ]
    for phrase in positives:
        assert is_browser_observation_intent(phrase), f"expected intent: {phrase!r}"


def test_followup_not_capture_intent() -> None:
    assert not is_browser_observation_intent("open the screenshot")
    assert not is_browser_observation_intent("show me the screenshot")


def test_intent_negatives() -> None:
    negatives = [
        "what can you do",
        "click submit on pilotmain.com",
        "restart pilotos-api in railway",
        "check github workflows",
    ]
    for phrase in negatives:
        assert not is_browser_observation_intent(phrase), f"false positive: {phrase!r}"


def test_url_extraction() -> None:
    assert extract_target_url("take a screenshot of pilotmain.com") == "https://pilotmain.com"
    assert extract_target_url("open pilotmain.com") == "https://pilotmain.com"
    assert extract_target_url("inspect https://example.org/page") == "https://example.org/page"


@patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
@patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=False)
def test_blocked_runtime_exact_blocker(_ready, mock_inspect) -> None:
    mock_inspect.return_value = {
        "canonical_env_var": "BROWSER_AUTOMATION_ENABLED",
        "ignored_env_vars": ["PLAYWRIGHT_ENABLED", "BROWSER_ENABLED"],
        "env_flag_loaded": True,
        "env_raw_process_value": "true",
        "settings_value": True,
        "playwright_python_package_installed": False,
        "chromium_binary_installed": False,
        "browser_launch_test": "fail (package missing)",
        "worker_enabled": False,
        "execution_ready": False,
        "remediation_notes": ["Restart the AethOS API process."],
        "recommended_install_commands": [],
    }
    result = route_browser_observation("take a screenshot of pilotmain.com", session_id="blocked")
    assert result is not None
    body, intent, meta = result
    assert intent == "browser_observation_blocked"
    assert "Browser observation is available, but execution is currently blocked." in body
    assert "Runtime checks (this API process):" in body
    assert "playwright python package installed: no" in body
    assert "worker enabled: no" in body
    assert "Playwright runtime unavailable" not in body
    assert "No mutation has been performed." in body
    assert "How I can help" not in body
    assert meta["route_id"] == "browser_observation"


@patch("aethos_core.browser.runtime.browser_runtime.run_browser_evidence_capture")
@patch("aethos_core.browser_observation.browser_observation_router._runtime_is_ready", return_value=True)
@patch("aethos_core.browser_observation.browser_observation_router.inspect_browser_observation_runtime")
def test_successful_capture_reply(mock_inspect, _ready, mock_capture) -> None:
    mock_inspect.return_value = {"execution_ready": True, "browser_launch_test": "pass"}
    mock_capture.return_value = {
        "ok": True,
        "summary": "Browser evidence captured for `pilotmain.com` (screenshot) — 2 artifact(s).",
        "artifacts": [
            {
                "artifact_id": "bart-test-1",
                "artifact_type": "browser_screenshot",
                "artifact_file_url": "/api/v1/browser/artifacts/bart-test-1/file",
            },
            {"artifact_id": "bart-meta-1", "artifact_type": "browser_page_metadata"},
        ],
    }
    result = route_browser_observation("take a screenshot of pilotmain.com", session_id="cap-ok")
    assert result is not None
    body, intent, meta = result
    assert intent == "browser_observation_captured"
    assert "Screenshot captured" in body
    assert "https://pilotmain.com" in body
    assert "bart-test-1" in body
    assert meta["artifact_id"] == "bart-test-1"
    mock_capture.assert_called_once()


@patch("aethos_core.browser_observation.browser_observation_router.route_browser_observation_lane")
def test_resolve_chat_turn_prefers_observation_lane(mock_route) -> None:
    mock_route.return_value = (
        "Screenshot captured.",
        "browser_observation_captured",
        {"route_id": "browser_observation"},
    )
    result = resolve_chat_turn(
        "take a screenshot of pilotmain.com",
        session_id="chat-obs",
        apply_relational_layer=False,
    )
    assert result.intent == "browser_observation_captured"
    assert "How I can help" not in result.reply
    mock_route.assert_called_once()


def test_no_capability_prose_fallback() -> None:
    overview = build_capability_overview(authority.capabilities, generative_configured=False)
    assert "How I can help" in overview
    assert not is_browser_observation_intent("what can you do")


def test_provider_readonly_still_routes_github() -> None:
    routed = compose_readonly_provider_route_reply("list github workflows for pilotmain/aethos")
    assert routed is not None
    _reply, intent, meta = routed
    assert intent
    assert meta.get("route_id") or meta.get("provider")


def test_no_mutation_preflight_for_observation() -> None:
    from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

    assert create_mutation_preflight_job_reply("take a screenshot of pilotmain.com") is None
