# SPDX-License-Identifier: Apache-2.0

import pytest
from unittest.mock import patch

from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor
from aethos_core.runtime.jobs import job_store, message_for_job_event
from aethos_core.runtime.railway_readonly_inspector import (
    RailwayInventoryError,
    build_chat_summary,
    build_empty_inventory_summary,
    build_inventory_error_summary,
    run_railway_services_inventory,
)


def test_railway_inventory_chat_summary_lists_services():
    summary = build_chat_summary(
        [
            {"name": "api-worker", "project_name": "AethOS"},
            {"name": "backend", "project_name": "ProposalPilot"},
        ]
    )
    assert "Railway services found" in summary
    assert "api-worker" in summary
    assert "AethOS" in summary
    assert "Found **2** services" in summary
    assert "across **2** projects" in summary


def test_railway_inventory_project_count_uses_full_inventory_not_preview():
    """Preview shows 8 services but project count must include all rows."""
    items = [{"name": f"svc-{i}", "project_name": f"project-{i // 4}"} for i in range(12)]
    summary = build_chat_summary(items)
    assert "Found **12** services" in summary
    assert "across **3** projects" in summary
    assert "+ 4 more services" in summary


def test_railway_inventory_empty_state_copy():
    summary = build_empty_inventory_summary()
    assert "no services were returned" in summary
    assert "token account scope" in summary


def test_railway_inventory_error_summary_is_safe():
    summary = build_inventory_error_summary("Unauthorized")
    assert "could not retrieve services" in summary
    assert "Unauthorized" in summary
    assert "token validity" in summary


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
    assert "backend" in outcome.full_result
    assert outcome.evidence
    assert outcome.evidence[0]["confidence"] == "confirmed"


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_graphql_failure_raises_safe_error(mock_list, _mock_token):
    mock_list.return_value = {"ok": False, "services": [], "error": "Unauthorized"}
    with pytest.raises(RailwayInventoryError) as exc:
        run_railway_services_inventory(credential_id="cred-1")
    assert "could not retrieve services" in str(exc.value)
    assert "Unauthorized" in str(exc.value)


@patch("aethos_core.providers.railway.auth.RailwayAuthAdapter.get_api_token", return_value="tok")
@patch("aethos_core.providers.railway.api_client.list_services_with_status")
def test_railway_inventory_auto_run_uses_executor_not_manual_note(mock_list, _mock_token):
    mock_list.return_value = {
        "ok": True,
        "services": [
            {
                "service_id": "svc-1",
                "service_name": "api-worker",
                "project_id": "proj-1",
                "project_name": "AethOS",
            }
        ],
        "error": None,
    }
    job_executor.drain_queue_for_tests()
    job = authority.create_job(
        title="Railway services inventory",
        job_type="railway_services_inventory",
        params={
            "user_request": "show my Railway apps",
            "provider": "railway",
            "credential_id": "cred-1",
            "auth_method": "api_token",
        },
        auto_run=True,
    )
    job_executor.drain_once_for_tests()
    completed = job_store.get(job.id)
    assert completed is not None
    assert completed.status.value == "completed"
    assert "api-worker" in (completed.result_summary or "")
    assert "Tracked note recorded" not in (completed.result_summary or "")
    event = message_for_job_event(completed, "job_completed")
    assert "api-worker" in event
    assert "saved Railway API token" in event
