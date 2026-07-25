# SPDX-License-Identifier: Apache-2.0

from aethos_core.connections.adapters import (
    vercel_inspection_completion_message,
    vercel_inspection_progress_message,
)
from aethos_core.runtime.job_artifacts import chat_completion_event_message
from aethos_core.runtime.jobs import TrackedJob, JobStatus, message_for_job_event


def test_api_token_progress_copy():
    msg = vercel_inspection_progress_message("api_token")
    assert "saved Vercel API token" in msg
    assert "browser session" not in msg.lower()


def test_api_token_completion_copy():
    msg = vercel_inspection_completion_message("api_token")
    assert "saved Vercel API token" in msg
    assert "browser automation" in msg
    assert "browser session" not in msg.lower()


def test_api_token_chat_completion_event():
    msg = chat_completion_event_message(
        "vercel_projects_inventory",
        "Vercel projects inventory",
        "- demo",
        fallback=False,
        auth_method="api_token",
    )
    assert "saved Vercel API token" in msg
    assert "browser session" not in msg.lower()


def test_api_token_job_event_from_params():
    job = TrackedJob(
        id="job-api",
        title="Vercel projects inventory",
        job_type="vercel_projects_inventory",
        status=JobStatus.COMPLETED,
        source="test",
        session_id="s",
        params={"auth_method": "api_token", "auth_method_label": "Vercel API token"},
        result_summary="- demo",
    )
    msg = message_for_job_event(job, "job_completed")
    assert "saved Vercel API token" in msg
    assert "browser session" not in msg.lower()
