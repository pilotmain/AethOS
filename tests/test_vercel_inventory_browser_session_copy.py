# SPDX-License-Identifier: Apache-2.0

from aethos_core.connections.adapters import (
    vercel_inspection_completion_message,
    vercel_inspection_progress_message,
)
from aethos_core.runtime.job_artifacts import chat_completion_event_message
from aethos_core.runtime.jobs import TrackedJob, JobStatus, message_for_job_event


def test_browser_session_progress_copy():
    msg = vercel_inspection_progress_message("browser")
    assert "saved browser session" in msg
    assert "api token" not in msg.lower()


def test_browser_session_completion_copy():
    msg = vercel_inspection_completion_message("browser")
    assert "saved browser session" in msg
    assert "browser automation" not in msg.lower()


def test_browser_session_chat_completion_event():
    msg = chat_completion_event_message(
        "vercel_projects_inventory",
        "Vercel projects inventory",
        "- demo",
        fallback=False,
        auth_method="browser",
    )
    assert "saved browser session" in msg
    assert "api token" not in msg.lower()


def test_browser_session_job_event_from_params():
    job = TrackedJob(
        id="job-browser",
        title="Vercel projects inventory",
        job_type="vercel_projects_inventory",
        status=JobStatus.COMPLETED,
        source="test",
        session_id="s",
        params={"auth_method": "browser", "profile_id": "bprof-test"},
        result_summary="- demo",
    )
    msg = message_for_job_event(job, "job_completed")
    assert "saved browser session" in msg
    assert "api token" not in msg.lower()
