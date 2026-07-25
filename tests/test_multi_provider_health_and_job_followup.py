# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.chat.job_result_followup_router import (
    compose_job_result_followup_reply,
    is_job_result_followup_intent,
)
from aethos_core.operational_session.railway_service_hints import (
    filter_railway_health_rows,
    is_railway_named_service_health_request,
    should_defer_vercel_only_external_health,
)
from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn
from aethos_core.runtime.external_jobs import infer_external_health_from_text
from aethos_core.runtime.jobs import JobStatus, TrackedJob, job_store
from aethos_core.world_model.fallback_context_resolver import resolve_fallback_context


@pytest.fixture
def sample_rows():
    return [
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
        },
        {
            "service": "aethos-ui",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
        },
        {
            "service": "influencer-crm",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
        },
    ]


def test_filter_rows_prefers_pilotos_staging_for_aethos_services():
    rows = [
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
        },
        {
            "service": "aethos-api",
            "project": "pilotos",
            "environment": "production",
            "status": "running",
            "health": "healthy",
        },
        {
            "service": "aethos-ui",
            "project": "pilotos",
            "environment": "staging",
            "status": "running",
            "health": "healthy",
        },
        {
            "service": "aethos-ui",
            "project": "pilotos",
            "environment": "production",
            "status": "running",
            "health": "healthy",
        },
    ]
    text = "can you please check health status of aethos-api and aethos-ui in railway"
    filtered = filter_railway_health_rows(rows, ["aethos-api", "aethos-ui"], text=text)
    assert len(filtered) == 2
    assert {row["environment"] for row in filtered} == {"staging"}
    assert {row["service"] for row in filtered} == {"aethos-api", "aethos-ui"}


def test_railway_only_health_request_is_recognized():
    text = "can you please check health status of aethos-api and aethos-ui in railway"
    assert is_railway_named_service_health_request(text)
    assert should_defer_vercel_only_external_health(text)
    assert not is_job_result_followup_intent(text)


def test_report_back_with_health_check_is_not_job_followup():
    text = "check the health of aethos-api and aethos-ui in railway and check it in vercel and report back"
    assert not is_job_result_followup_intent(text)
    assert should_defer_vercel_only_external_health(text)


def test_railway_only_health_reply(sample_rows):
    text = "can you please check health status of aethos-api and aethos-ui in railway"
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(sample_rows, None),
    ):
        result = route_operational_conversation_kernel_turn(text, session_id="health-session")
    assert result is not None
    assert "aethos-api" in result.reply
    assert "aethos-ui" in result.reply
    assert "Vercel" not in result.reply


def test_infer_external_health_defers_when_railway_services_named(sample_rows):
    text = "check the health of aethos-api and aethos-ui in railway and check it in vercel and report back"
    assert should_defer_vercel_only_external_health(text)
    assert infer_external_health_from_text(text) is None


def test_multi_provider_health_via_kernel(sample_rows):
    text = "check the health of aethos-api and aethos-ui in railway and check it in vercel and report back"
    with patch(
        "aethos_core.operational_planner.adapters.railway_wide_health.collect_railway_service_health_rows",
        return_value=(sample_rows, None),
    ):
        result = route_operational_conversation_kernel_turn(text, session_id="health-session")
    assert result is not None
    assert "aethos-api" in result.reply
    assert "aethos-ui" in result.reply
    assert "influencer-crm" not in result.reply


def test_job_result_followup_surfaces_completed_job():
    job_store._jobs.clear()
    job_store._jobs["job-ec8d8772403e"] = TrackedJob(
        id="job-ec8d8772403e",
        title="Vercel service health check",
        job_type="external_health_report",
        status=JobStatus.COMPLETED,
        source="chat",
        session_id="health-session",
        result_summary="Vercel external health report",
        full_result="# External health\n\n- Vercel Status — All Systems Operational",
    )
    reply, intent, meta = compose_job_result_followup_reply(
        "tell me the health status here in chat please",
        session_id="health-session",
    )
    assert intent == "job_result_followup"
    assert "job-ec8d8772403e" in reply
    assert "All Systems Operational" in reply
    assert meta["job_id"] == "job-ec8d8772403e"


def test_fallback_context_skips_stale_investigation_for_job_followup():
    ctx = resolve_fallback_context(
        text="tell me the health status here in chat please",
        session_id="default",
    )
    assert ctx is None
