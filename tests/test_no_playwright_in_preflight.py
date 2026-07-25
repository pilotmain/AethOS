# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.runtime.browser_executor import browser_executor
from aethos_core.runtime.operational_memory import operational_memory


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    monkeypatch.setenv("BROWSER_AUTOMATION_ENABLED", "true")
    operational_memory.clear_for_tests()
    yield
    operational_memory.clear_for_tests()
    browser_executor.drain_queue_for_tests()


def test_preflight_does_not_call_playwright_launch(monkeypatch, env):
    called = {"launch": False}

    def _fake_probe(*, timeout=45.0):
        called["launch"] = True
        raise AssertionError("preflight must not run Playwright launch probe")

    monkeypatch.setattr(
        "aethos_core.runtime.browser_diagnostics.probe_playwright_on_browser_thread",
        _fake_probe,
    )
    outcome = run_operation_preflight(
        job_type="vercel_logs_preflight",
        params={
            "user_request": "check logs for talking-avatar-agent",
            "provider": "vercel",
            "operation_type": "check_logs",
            "target_hints": [],
        },
    )
    assert outcome.preflight is not None
    assert called["launch"] is False
