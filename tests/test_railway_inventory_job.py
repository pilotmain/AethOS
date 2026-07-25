# SPDX-License-Identifier: Apache-2.0

from unittest.mock import patch

from fastapi.testclient import TestClient

from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.job_types import uses_railway_readonly
from aethos_core.runtime.railway_readonly_inspector import run_railway_services_inventory
from aethos_core.runtime.railway_readonly_jobs import infer_railway_readonly_job, is_railway_inventory_request


def test_railway_inventory_request_detector():
    assert is_railway_inventory_request("show my Railway apps")
    assert is_railway_inventory_request("list railway services")
    assert not is_railway_inventory_request("show railway deployments for api-worker")


def test_infer_railway_services_inventory_job():
    out = infer_railway_readonly_job("show my Railway apps")
    assert out is not None
    _, job_type, params = out
    assert job_type == "railway_services_inventory"
    assert params["provider"] == "railway"


def test_railway_inventory_job_type_registered():
    assert uses_railway_readonly("railway_services_inventory")


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_inspector_builds_report(mock_list, _mock_token):
    mock_list.return_value = {
        "ok": True,
        "services": [
            {
                "service_id": "svc-1",
                "service_name": "api-worker",
                "project_id": "proj-1",
                "project_name": "backend",
            }
        ],
        "error": None,
    }
    outcome = run_railway_services_inventory(credential_id="cred-1", user_request="show my Railway apps")
    assert "api-worker" in outcome.summary
    assert outcome.evidence
    assert outcome.evidence[0]["confidence"] == "confirmed"


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.resolve_best_auth_method")
def test_chat_creates_railway_inventory_job(mock_auth):
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-rw"}

    from aethos_core.api.main import app
    from aethos_core.config import get_settings
    from aethos_core.security.credential_vault import reset_credential_vault_for_tests

    reset_credential_vault_for_tests()
    get_settings.cache_clear()
    job_executor.drain_queue_for_tests()
    try:
        client = TestClient(app)
        r = client.post(
            "/api/v1/chat",
            json={"message": "show my Railway apps", "session_id": "rw-inv"},
        )
        body = r.json()
        assert body["used_llm"] is False
        assert body["meta"]["proposed_job_type"] == "railway_services_inventory"
        assert body["meta"]["provider"] == "railway"
    finally:
        reset_credential_vault_for_tests()
        get_settings.cache_clear()
        job_executor.drain_queue_for_tests()


@patch("aethos_core.runtime.operational_memory.operational_memory.record_railway_inventory")
@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_writes_operational_memory(mock_list, _mock_token, mock_record):
    mock_list.return_value = {
        "ok": True,
        "services": [
            {
                "service_id": "svc-1",
                "service_name": "api-worker",
                "project_id": "proj-1",
                "project_name": "backend",
            }
        ],
        "error": None,
    }
    from aethos_core.runtime.jobs import job_store

    job = job_store.create(
        title="Railway services inventory",
        job_type="railway_services_inventory",
        params={
            "user_request": "show my Railway apps",
            "provider": "railway",
            "credential_id": "cred-1",
            "auth_method": "api_token",
        },
        auto_run=False,
    )
    job_executor.drain_queue_for_tests()
    job_executor.enqueue(job.id)
    assert job_executor.drain_once_for_tests()
    completed = job_store.get(job.id)
    assert completed is not None
    assert completed.status.value == "completed"
    mock_record.assert_called_once()
    assert completed.params.get("railway_inventory") is not None
    assert "api-worker" in (completed.result_summary or "")
    assert "vercel_inventory" not in (completed.params or {})
