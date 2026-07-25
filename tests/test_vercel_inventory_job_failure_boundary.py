# SPDX-License-Identifier: Apache-2.0

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from aethos_core.runtime.browser_profile_store import browser_profile_store
from aethos_core.runtime.browser_profiles import PersistenceMode
from aethos_core.runtime.browser_runtime import BrowserRuntimeBoundaryError
from tests.browser_test_utils import reset_browser_test_state
from tests.job_test_utils import drain_job_executor


@pytest.fixture(autouse=True)
def _run_browser_sync_inline(monkeypatch: pytest.MonkeyPatch):
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

    get_settings.cache_clear()
    browser_profile_store.clear_all_for_tests()
    yield
    browser_profile_store.clear_all_for_tests()
    get_settings.cache_clear()


def test_inventory_exception_becomes_structured_job_failure(profiles_env):
    os.environ["BROWSER_AUTOMATION_ENABLED"] = "true"
    profile_id = browser_profile_store.save_from_session(
        session_id="bsess-fail",
        site="vercel.com",
        storage_state={"cookies": [], "origins": []},
        persistence_mode=PersistenceMode.PERSISTENT.value,
    ).profile_id
    try:
        from aethos_core.config import get_settings
        from aethos_core.runtime.authority import authority
        from aethos_core.runtime.jobs import job_store

        get_settings.cache_clear()
        with patch(
            "aethos_core.runtime.vercel_readonly_inspector.run_readonly_inspection",
            side_effect=BrowserRuntimeBoundaryError("sync/async boundary"),
        ):
            job = authority.create_job(
                title="Vercel projects inventory",
                job_type="vercel_projects_inventory",
                params={"profile_id": profile_id, "user_request": "show my Vercel apps"},
                source="test",
                session_id="test",
                auto_run=True,
            )
            drain_job_executor()
            updated = job_store.get(job.id)
            assert updated is not None
            assert updated.status.value == "failed"
            failure = updated.params.get("failure") or {}
            assert failure.get("code") == "BROWSER_RUNTIME_FAILED"
            assert failure.get("profile_id") == profile_id
            assert failure.get("runtime_ready") is False
            assert "browser runtime" in (updated.failure_reason or "").lower()
    finally:
        reset_browser_test_state()
