# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.runtime.browser_intents import (
    classify_operational_intent,
    is_browser_session_request,
)
from aethos_core.runtime.browser_jobs import infer_browser_intent_from_text


def test_open_supervised_vercel_session_is_navigation_plan():
    text = "Open supervised Vercel session"
    assert is_browser_session_request(text)
    assert classify_operational_intent(text) == "browser_session_open"
    intent = infer_browser_intent_from_text(text)
    assert intent is not None
    assert intent[0] == "browser_navigation_plan"
    assert intent[1]["target"] == "vercel.com"


def test_open_vercel_dashboard_is_navigation_plan():
    intent = infer_browser_intent_from_text("open Vercel dashboard")
    assert intent is not None
    assert intent[0] == "browser_navigation_plan"


@pytest.mark.parametrize(
    "phrase",
    [
        "start Vercel browser session",
        "launch browser for Vercel",
        "connect to Vercel dashboard",
        "open browser automation for Vercel",
    ],
)
def test_session_open_variants(phrase: str):
    intent = infer_browser_intent_from_text(phrase)
    assert intent is not None, phrase
    assert intent[0] == "browser_navigation_plan"


def test_login_to_vercel_is_login_notice():
    intent = infer_browser_intent_from_text("login to Vercel")
    assert intent is not None
    assert intent[0] == "browser_login_required_notice"
