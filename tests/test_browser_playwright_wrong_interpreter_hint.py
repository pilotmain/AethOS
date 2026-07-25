# SPDX-License-Identifier: Apache-2.0

import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.browser_test_utils import reset_browser_test_state, use_mock_browser_driver


def test_chat_shows_runtime_python_when_package_missing():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=False)
    try:
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={
                "message": "open vercel.com in browser automation",
                "session_id": "diag-hint",
            },
        )
        reply = r.json()["reply"]
        assert "AethOS runtime" in reply or "runtime" in reply.lower()
        assert ".venv" in reply or sys.executable in reply or "python -m pip install playwright" in reply
        assert "bare `pip`" in reply or "same Python" in reply
    finally:
        reset_browser_test_state()


def test_runtime_not_ready_message_distinguishes_package():
    from aethos_core.runtime.browser_diagnostics import probe_playwright_runtime, runtime_not_ready_message

    fake = {
        "playwright_package": "missing",
        "chromium_browser": "missing",
        "install_hint": f"{sys.executable} -m pip install playwright",
        "recommended_install_commands": [f"{sys.executable} -m pip install playwright"],
        "recommended_install_command": f"{sys.executable} -m pip install playwright",
    }
    msg = runtime_not_ready_message(fake)
    assert "Playwright package" in msg
    assert "runtime environment" in msg


def test_approve_failure_message_package_missing():
    from aethos_core.api.main import app

    use_mock_browser_driver(installed=False)
    try:
        client = TestClient(app)
        proposed = client.post(
            "/api/v1/actions/propose",
            json={
                "action_type": "browser_navigation_plan",
                "params": {"target": "vercel.com"},
            },
        ).json()
        approved = client.post(f"/api/v1/actions/{proposed['id']}/approve").json()
        assert approved["status"] == "failed"
        events = client.get(f"/api/v1/actions/events?ids={proposed['id']}").json()["events"]
        failed = [e for e in events if e["event_type"] == "action_failed"][-1]
        assert "runtime environment" in failed["message"].lower()
    finally:
        reset_browser_test_state()
