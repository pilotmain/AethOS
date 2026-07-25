# SPDX-License-Identifier: Apache-2.0

from aethos_core.runtime.job_artifacts import build_artifact_bundle, chat_completion_event_message
from aethos_core.runtime.jobs import TrackedJob, JobStatus


def test_build_artifact_bundle_splits_summary_and_preview():
    full = "# Competitors\n\n- LangGraph — graphs\n- CrewAI — crews\n- AutoGen — agents"
    bundle = build_artifact_bundle(full, job_type="comparison_brief", title="Competitors")
    assert bundle.full_result == full
    assert bundle.preview
    assert "LangGraph" in bundle.preview or "Competitors" in bundle.preview
    assert bundle.summary.startswith("- ")
    assert "Mission Control" in bundle.summary


def test_chat_completion_message_excludes_full_markdown():
    full = "# Report\n\n" + "\n".join(f"- Point {i}" for i in range(40))
    bundle = build_artifact_bundle(full, job_type="research_plan", title="Research")
    msg = chat_completion_event_message("research_plan", "Research", bundle.summary, fallback=False)
    assert "Summary:" in msg
    assert full not in msg
    assert "Open Mission Control" in msg


def test_provider_runner_success_has_three_artifact_fields():
    from unittest.mock import patch

    from aethos_core.provider.completion import ProviderResult
    from aethos_core.runtime.provider_job_runner import run_provider_job

    job = TrackedJob(
        id="job-art",
        title="Competitors",
        job_type="comparison_brief",
        status=JobStatus.QUEUED,
        source="test",
        session_id="s",
        params={},
    )
    prov = ProviderResult(
        text="# Brief\n\n- Alpha\n- Beta",
        provider="anthropic",
        model="claude-test",
        used_llm=True,
    )
    with (
        patch("aethos_core.runtime.provider_job_runner.provider_configured", return_value=True),
        patch("aethos_core.runtime.provider_job_runner._call_provider", return_value=prov),
    ):
        out = run_provider_job(job, timeout_sec=30)
    assert out.full_result
    assert out.summary
    assert out.preview
    assert out.summary != out.full_result
