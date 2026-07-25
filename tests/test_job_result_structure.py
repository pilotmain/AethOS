# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor, mock_provider_job_result


def test_completed_job_has_artifact_fields():
    from aethos_core.api.main import app

    long_body = "# Competitor brief\n\n" + "\n".join(f"- Item {i}" for i in range(20))
    mock_result = mock_provider_job_result(
        long_body,
        provider="anthropic",
        model="claude-test",
        used_llm=True,
        fallback=False,
        job_type="comparison_brief",
        title="Competitors",
    )
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Competitors", "job_type": "comparison_brief"},
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]

    assert job["status"] == "completed"
    assert job.get("full_result") or job.get("result")
    assert job["result_preview"]
    assert job["result_summary"]
    assert "Open Mission Control" in (job["result_summary"] or "")
    assert job["provider_used"] == "anthropic"
    assert len(job["result_summary"]) < len(job.get("full_result") or job["result"] or "")


def test_job_completed_chat_event_is_summary_only():
    from aethos_core.api.main import app

    long_body = "# Huge report\n\n" + "\n".join(f"## Section {i}\n\nParagraph {i}.\n" for i in range(30))
    mock_result = mock_provider_job_result(
        long_body,
        provider="anthropic",
        model="claude-test",
        used_llm=True,
        fallback=False,
        job_type="comparison_brief",
        title="Competitors",
    )
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={"title": "Competitors", "job_type": "comparison_brief"},
        ).json()
        drain_job_executor()
        events = client.get(f"/api/v1/jobs/events?ids={created['id']}").json()["events"]
    completed = [e for e in events if e["event_type"] == "job_completed"][0]
    msg = completed["message"]
    assert "Summary:" in msg
    assert "Mission Control" in msg
    assert "## Section 29" not in msg
    assert len(msg) < len(long_body)
