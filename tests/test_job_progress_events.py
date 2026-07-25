# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from tests.job_test_utils import drain_job_executor


def test_job_progress_event_emitted():
    from aethos_core.api.main import app
    from tests.job_test_utils import mock_provider_job_result

    mock_result = mock_provider_job_result(
        "ok",
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
        jid = created["id"]
        drain_job_executor()
        events = client.get(f"/api/v1/jobs/events?ids={jid}").json()["events"]
        types = [e["event_type"] for e in events]
        assert "job_started" in types
        assert "job_progress" in types
        assert "job_completed" in types
        progress = [e for e in events if e["event_type"] == "job_progress"][0]
        assert "🧠" in progress["message"]
