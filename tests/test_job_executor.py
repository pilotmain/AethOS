# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from tests.job_test_utils import drain_job_executor


def test_executor_runs_one_job_at_a_time():
    from aethos_core.runtime.job_executor import job_executor
    from aethos_core.runtime.jobs import job_store
    from tests.job_test_utils import mock_provider_job_result

    job_store._jobs.clear()
    job_store._events.clear()

    mock_result = mock_provider_job_result("done")
    with patch(
        "aethos_core.runtime.job_executor.run_provider_job",
        return_value=mock_result,
    ):
        j1 = job_store.create(title="A", job_type="research_plan", auto_run=True)
        j2 = job_store.create(title="B", job_type="research_plan", auto_run=True)
        assert j1.status.value == "queued"
        assert j2.status.value == "queued"
        drain_job_executor()
        assert job_store.get(j1.id).status.value == "completed"
        assert job_store.get(j2.id).status.value == "completed"
