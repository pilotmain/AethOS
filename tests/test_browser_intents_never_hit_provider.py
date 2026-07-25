# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.chat.lanes import is_deterministic_lane
from aethos_core.runtime.browser_jobs import infer_browser_intent_from_text


@patch("aethos_core.provider.completion.complete_chat")
def test_operational_prompts_never_invoke_provider(mock_complete):
    from aethos_core.provider.completion import ProviderResult

    mock_complete.side_effect = AssertionError("provider lane must not run")

    from aethos_core.api.main import app

    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    prompts = [
        "Open supervised Vercel session",
        "open Vercel dashboard",
        "tell me all my Vercel apps",
        "redeploy my app",
    ]
    try:
        from aethos_core.config import get_settings

        get_settings.cache_clear()
        get_settings()
        client = TestClient(app)
        for msg in prompts:
            assert is_deterministic_lane(msg), msg
            r = client.post("/api/v1/chat", json={"message": msg, "session_id": "no-prov"})
            assert r.json()["used_llm"] is False, msg
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from aethos_core.config import get_settings

        get_settings.cache_clear()


def test_deterministic_lane_covers_session_open():
    assert is_deterministic_lane("Open supervised Vercel session")
    assert infer_browser_intent_from_text("Open supervised Vercel session")[0] == "browser_navigation_plan"
