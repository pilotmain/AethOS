# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from aethos_core.runtime.browser_intents import classify_operational_intent
from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.vercel_readonly_inspector import TOOL_USED
from tests.browser_test_utils import drain_browser_executor, use_mock_browser_driver
from tests.job_test_utils import drain_job_executor


@pytest.fixture(autouse=True)
def _run_browser_sync_inline(monkeypatch: pytest.MonkeyPatch):
    """Avoid blocking on browser executor thread during job_executor tests."""
    from aethos_core.runtime.browser_executor import browser_executor

    monkeypatch.setattr(
        browser_executor,
        "run_sync",
        lambda fn, timeout=90.0: fn(),
    )


@pytest.fixture
def profiles_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path))
    from aethos_core.config import get_settings
    from tests.browser_test_utils import reset_browser_test_state

    get_settings.cache_clear()
    reset_browser_test_state()
    yield
    reset_browser_test_state()
    get_settings.cache_clear()


def _seed_vercel_profile() -> str:
    from aethos_core.runtime.browser_profiles import PersistenceMode

    return browser_profile_store.save_from_session(
        session_id="bsess-vercel",
        site="vercel.com",
        storage_state={"cookies": [{"name": "s", "value": "1", "domain": ".vercel.com", "path": "/"}]},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    ).profile_id


def test_follow_up_saved_session_routes_to_inspection():
    text = "give me the list of services deployed in vercel using saved session"
    assert classify_operational_intent(text) == "vercel_inspection"


def test_vercel_inspection_job_uses_browser_inspector(profiles_env):
    use_mock_browser_driver(installed=True)
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    profile_id = _seed_vercel_profile()
    try:
        from aethos_core.config import get_settings
        from aethos_core.api.main import app
        from aethos_core.runtime.authority import authority

        get_settings.cache_clear()
        with patch(
            "aethos_core.runtime.job_executor.run_provider_job",
        ) as provider_run:
            provider_run.side_effect = AssertionError("provider runner must not run for vercel readonly")
            job = authority.create_job(
                title="Vercel projects inventory",
                job_type="vercel_projects_inventory",
                params={"profile_id": profile_id, "user_request": "show my Vercel apps"},
                source="test",
                session_id="test",
                auto_run=True,
            )
            drain_job_executor()
            drain_browser_executor()
            from aethos_core.runtime.jobs import job_store

            updated = job_store.get(job.id)
            assert updated is not None
            assert updated.status.value == "completed"
            assert updated.params.get("tool_used") == TOOL_USED
            assert updated.params.get("browser_used") is True
            assert updated.params.get("profile_id") == profile_id
            assert updated.params.get("provider_used") == "none"
            assert provider_run.call_count == 0
            assert "my-app" in (updated.result_summary or "").lower() or "Found" in (
                updated.result_summary or ""
            )
    finally:
        reset = __import__("tests.browser_test_utils", fromlist=["reset_browser_test_state"]).reset_browser_test_state
        reset()


def test_missing_profile_fails_with_explicit_message(profiles_env):
    use_mock_browser_driver(installed=True)
    try:
        from aethos_core.runtime.vercel_readonly_inspector import run_readonly_inspection
        from aethos_core.runtime.browser_executor import browser_executor

        browser_executor.drain_queue_for_tests()
        try:
            run_readonly_inspection(
                job_type="vercel_projects_inventory",
                title="Test",
                profile_id="bprof-doesnotexist",
            )
            assert False, "expected failure"
        except RuntimeError as exc:
            assert "not found" in str(exc).lower()
    finally:
        from tests.browser_test_utils import reset_browser_test_state

        reset_browser_test_state()


def test_chat_with_profile_creates_job_not_llm(profiles_env):
    use_mock_browser_driver(installed=True)
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    profile_id = _seed_vercel_profile()
    try:
        from aethos_core.config import get_settings
        from aethos_core.chat.vercel_readonly_prompts import create_vercel_readonly_job_reply

        get_settings.cache_clear()
        handled = create_vercel_readonly_job_reply(
            "inspect my vercel account read-only using saved session",
            session_id="insp-chat",
        )
        assert handled is not None
        body, _intent, meta = handled
        assert "job-" in body
        assert profile_id in body
        assert "don't have access" not in body.lower()
    finally:
        os.environ.pop("BROWSER_AUTOMATION_ENABLED", None)
        from tests.browser_test_utils import reset_browser_test_state

        reset_browser_test_state()
