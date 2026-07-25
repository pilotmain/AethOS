# SPDX-License-Identifier: Apache-2.0
"""Agent provider cloud delegation — agent tool loop follow-ups."""

from __future__ import annotations

from unittest.mock import patch

from aethos_core.chat.job_result_followup_router import is_job_result_followup_intent
from aethos_core.execution_brain.agent_provider_cloud import is_agent_provider_cloud_request
from aethos_core.execution_brain.agent_tool_executor import (
    agent_tool_schemas,
    execute_agent_tool,
)


def test_restart_named_service_is_agent_cloud_request():
    assert is_agent_provider_cloud_request("can you restart influencer-crm and report back on the status")


def test_health_check_named_service_is_agent_cloud_request():
    assert is_agent_provider_cloud_request("Run a health check for influencer-crm and report back")


def test_list_vercel_health_still_agent_cloud():
    assert is_agent_provider_cloud_request("list all vercel projects and show deployment health for each")


def test_mc_provider_catalog_is_agent_cloud():
    assert is_agent_provider_cloud_request(
        "List all providers in Mission Control Provider Inventory and tell me which ones support health checks vs validate-only"
    )


def test_full_provider_scan_is_agent_cloud():
    assert is_agent_provider_cloud_request(
        "Scan all Mission Control providers in full mode and give me an operational report"
    )


def test_job_artifact_followup_not_agent_cloud():
    assert not is_agent_provider_cloud_request("tell me the health status here in chat please")


def test_job_result_followup_skips_restart_report_back():
    assert not is_job_result_followup_intent("can you restart influencer-crm and report back on the status")


def test_job_result_followup_skips_health_check_report_back():
    assert not is_job_result_followup_intent("Run a health check for influencer-crm and report back")


def test_operational_fast_path_defers_restart_when_agent_runtime_enabled(monkeypatch):
    from aethos_core.config import get_settings
    from aethos_core.chat.chat_turn_steps import try_operational_fast_path_turn

    monkeypatch.setattr(get_settings(), "agent_runtime_enabled", True)
    result = try_operational_fast_path_turn(
        "can you restart influencer-crm and report back on the status",
        session_id="agent-cloud-test",
        channel="chat",
        emotional_context=None,
    )
    assert result is None


def test_agent_tool_schemas_include_cloud_followup_tools():
    names = {t["name"] for t in agent_tool_schemas()}
    assert "provider_health" in names
    assert "provider_logs" in names
    assert "provider_create_mutation_preflight" in names


def test_mutation_preflight_tool_returns_job_payload():
    fake = (
        "Created mutation preflight job `job-123` (**no mutation performed yet**).",
        "mutation_preflight_job_created",
        {"proposed_job_id": "job-123", "provider": "vercel", "operation_type": "restart"},
    )
    with patch(
        "aethos_core.chat.mutation_preflight_prompts.create_mutation_preflight_job_reply",
        return_value=fake,
    ):
        out = execute_agent_tool(
            "provider_create_mutation_preflight",
            {"user_text": "restart influencer-crm on vercel"},
            session_id="preflight-test",
        )
    assert "job-123" in out
    assert "mutation_preflight_job_created" in out
