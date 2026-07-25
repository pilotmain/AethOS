# SPDX-License-Identifier: Apache-2.0

import pytest

from aethos_core.operations.preflight import run_operation_preflight
from aethos_core.operations.preflight_supersede import supersede_previous_preflights
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


@pytest.fixture
def job_env(tmp_path, monkeypatch):
    monkeypatch.setenv("BROWSER_PROFILES_DIR", str(tmp_path / "browser_profiles"))
    job_executor.drain_queue_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()
    yield
    job_executor.drain_queue_for_tests()
    job_store._jobs.clear()
    job_store._events.clear()


def _run_env_preflight(session: str) -> str:
    outcome = run_operation_preflight(
        job_type="vercel_env_var_preflight",
        params={
            "user_request": "set NEXT_PUBLIC_API_URL for quotepilot",
            "provider": "vercel",
            "operation_type": "set_env_var",
            "target_hints": [],
        },
    )
    job = job_store.create(
        title="Env preflight",
        job_type="vercel_env_var_preflight",
        params={
            "user_request": "set NEXT_PUBLIC_API_URL for quotepilot",
            "provider": "vercel",
            "operation_type": "set_env_var",
            "target_hints": [],
            "operation_preflight": outcome.preflight.to_dict(),
            "preflight_status": outcome.preflight.preflight_status,
        },
        session_id=session,
        auto_run=False,
    )
    job_store.complete_with_result(
        job.id,
        full_result=outcome.full_result,
        summary=outcome.summary,
        preview=outcome.preview,
        provider="preflight",
        model="deterministic",
        used_llm=False,
        fallback=False,
    )
    supersede_previous_preflights(new_job_id=job.id)
    return job.id


def test_newer_preflight_supersedes_older_same_operation(job_env):
    old_id = _run_env_preflight("s1")
    new_id = _run_env_preflight("s2")
    assert old_id != new_id
    old = job_store.get(old_id)
    new = job_store.get(new_id)
    assert old and new
    assert old.params.get("is_current") is False
    assert old.params.get("superseded_by") == new_id
    assert old.params.get("preflight_status") == "superseded"
    assert new.params.get("is_current") is True
