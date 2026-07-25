# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor


def test_provider_job_completes_via_chat():
    from aethos_core.api.main import app
    from tests.job_test_utils import mock_provider_job_result

    mock_result = mock_provider_job_result(
        "# Brief\n\n- LangGraph\n- CrewAI",
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
        r = client.post(
            "/api/v1/chat",
            json={
                "message": "research the top competitors to AethOS",
                "session_id": "prov-job-1",
            },
        )
        body = r.json()
        jid = body["meta"]["proposed_job_id"]
        assert jid.startswith("job-")
        assert "Created tracked job" in body["reply"]
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{jid}").json()["job"]
        assert job["status"] == "completed"
        assert job["provider_used"] == "anthropic"
        assert "LangGraph" in (job.get("full_result") or job["result"] or "")
        assert job["result_summary"]
        assert job["result_preview"]


def test_provider_job_stores_preview():
    from aethos_core.api.main import app
    from tests.job_test_utils import mock_provider_job_result

    mock_result = mock_provider_job_result(
        "Line one\nLine two",
        provider="none",
        model="template",
        used_llm=False,
        fallback=True,
        job_type="roadmap_generation",
        title="Roadmap",
    )
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        client = TestClient(app)
        created = client.post(
            "/api/v1/jobs",
            json={
                "title": "Roadmap",
                "job_type": "roadmap_generation",
                "params": {"user_request": "generate an MVP roadmap"},
            },
        ).json()
        drain_job_executor()
        job = client.get(f"/api/v1/jobs/{created['id']}").json()["job"]
        assert job["result_preview"]
        assert job["status"] == "completed"
