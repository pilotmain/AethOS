# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.credentials.credential_guidance import (
    build_credential_requirements_for_job,
    compose_missing_credential_reply,
    detect_missing_credential,
    find_latest_credential_blocked_preflight,
    rerun_mutation_preflight_for_job,
)
from aethos_core.operations.mutations.preflight import run_mutation_preflight
from aethos_core.runtime.authority import authority
from aethos_core.runtime.jobs import job_store
from tests.job_test_utils import drain_job_executor


@pytest.fixture
def mutation_enabled(monkeypatch):
    monkeypatch.setenv("MUTATION_EXECUTION_ENABLED", "true")
    monkeypatch.setenv("MUTATION_T3_PRODUCTION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _railway_preflight_params(**overrides):
    base = {
        "user_request": "restart MongoDB on Railway",
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "MongoDB",
        "target_status": "resolved",
        "target_resolved": True,
        "target": {
            "service_name": "MongoDB",
            "project_name": "pilotcore-sales-engine",
            "environment": "production",
            "resolved": True,
        },
    }
    base.update(overrides)
    return base


def test_detect_missing_credential_railway_token():
    preflight = {
        "preflight_status": "needs_credential",
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "MongoDB",
        "target": {
            "project_name": "pilotcore-sales-engine",
            "environment": "production",
            "service_name": "MongoDB",
        },
        "user_request": "restart MongoDB",
    }
    guidance = detect_missing_credential(preflight)
    assert guidance is not None
    assert guidance["missing_credentials"] == ["RAILWAY_API_TOKEN"]
    assert "pilotcore-sales-engine / production / MongoDB" in guidance["target_path"]
    assert "Railway restart mutation" in guidance["why_needed"]


def test_compose_missing_credential_reply_includes_setup_steps():
    preflight = {
        "preflight_status": "needs_credential",
        "provider": "railway",
        "operation_type": "restart",
        "target_name": "MongoDB",
        "target": {
            "project_name": "pilotcore-sales-engine",
            "environment": "production",
            "service_name": "MongoDB",
        },
        "user_request": "restart MongoDB",
    }
    reply = compose_missing_credential_reply(preflight)
    assert reply is not None
    assert "RAILWAY_API_TOKEN" in reply
    assert ".env: RAILWAY_API_TOKEN" in reply
    assert "Credential Center" in reply
    assert "Restart the AethOS API" in reply
    assert "restart MongoDB" in reply
    assert "No mutation has been performed yet." in reply


def test_mutation_preflight_attaches_credential_guidance(mutation_enabled):
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        outcome = run_mutation_preflight(
            job_type="mutation_preflight",
            params=_railway_preflight_params(),
        )
    assert outcome.preflight_status == "needs_credential"
    assert outcome.credential_guidance is not None
    assert outcome.credential_guidance["missing_credentials"] == ["RAILWAY_API_TOKEN"]
    assert outcome.credential_requirements_reply
    assert "RAILWAY_API_TOKEN" in outcome.full_result


def test_why_cant_approve_returns_credential_guidance(mutation_enabled):
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        job = authority.create_job(
            title="Restart MongoDB",
            job_type="mutation_preflight",
            params=_railway_preflight_params(),
            auto_run=True,
        )
        drain_job_executor()

    from aethos_core.chat.mutation_target_chat import compose_why_not_approvable_reply

    reply = compose_why_not_approvable_reply(
        f"why can't I approve {job.id}?",
        session_id="default",
    )
    assert reply is not None
    text, intent, meta = reply
    assert intent == "credential_requirement_guidance"
    assert "RAILWAY_API_TOKEN" in text
    assert meta["job_id"] == job.id


def test_credential_question_without_job_id_uses_latest_blocked_preflight(mutation_enabled):
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        job = authority.create_job(
            title="Restart MongoDB",
            job_type="mutation_preflight",
            params=_railway_preflight_params(),
            auto_run=True,
        )
        drain_job_executor()

    latest = find_latest_credential_blocked_preflight(session_id="default")
    assert latest is not None
    assert latest[0] == job.id

    from aethos_core.chat.mutation_target_chat import compose_why_not_approvable_reply

    reply = compose_why_not_approvable_reply("what credential is missing?", session_id="default")
    assert reply is not None
    assert "RAILWAY_API_TOKEN" in reply[0]


def test_build_credential_requirements_for_job(mutation_enabled):
    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        job = authority.create_job(
            title="Restart MongoDB",
            job_type="mutation_preflight",
            params=_railway_preflight_params(),
            auto_run=True,
        )
        drain_job_executor()

    payload = build_credential_requirements_for_job(job.id)
    assert payload is not None
    assert payload["ok"] is True
    assert payload["mutation_approvable"] is False
    assert payload["guidance"]["missing_credentials"] == ["RAILWAY_API_TOKEN"]


def test_refresh_credentials_keeps_mutation_blocked_without_token(mutation_enabled, monkeypatch):
    monkeypatch.delenv("RAILWAY_API_TOKEN", raising=False)
    get_settings.cache_clear()

    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        job = authority.create_job(
            title="Restart MongoDB",
            job_type="mutation_preflight",
            params=_railway_preflight_params(),
            auto_run=True,
        )
        drain_job_executor()

    with patch(
        "aethos_core.operations.mutations.preflight._mutation_provider_auth_block",
        return_value="needs_credential",
    ):
        rerun = rerun_mutation_preflight_for_job(job.id)

    assert rerun["ok"] is True
    assert rerun["preflight_status"] == "needs_credential"
    assert rerun["mutation_approvable"] is False

    stored = job_store.get(job.id)
    assert stored is not None
    assert stored.params.get("preflight_status") == "needs_credential"
    assert stored.params.get("credential_guidance", {}).get("missing_credentials") == ["RAILWAY_API_TOKEN"]
