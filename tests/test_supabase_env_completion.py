# SPDX-License-Identifier: Apache-2.0
"""Tests for Supabase env completion routing and orchestration."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from aethos_core.config import get_settings
from aethos_core.provider_e2e_orchestration.env_completion.supabase_approval import (
    approve_supabase_env_completion,
    validate_supabase_env_completion_gate,
)
from aethos_core.provider_e2e_orchestration.env_completion.supabase_browser_phase import (
    _extract_supabase_values,
)
from aethos_core.provider_e2e_orchestration.env_completion.supabase_constants import (
    SUPABASE_ENV_COMPLETION_JOB_TYPE,
    is_supabase_env_completion_request,
)
from aethos_core.provider_e2e_orchestration.e2e_completion_advisor import build_e2e_completion_advisory
from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel
from aethos_core.providers.railway.env_value_readiness.deployment_env_store import (
    clear_deployment_env_store_for_tests,
)
from aethos_core.providers.railway.env_value_readiness.env_value_inventory import (
    clear_deployment_env_presence_for_tests,
)
from aethos_core.runtime.authority import authority
from aethos_core.runtime.job_executor import job_executor


@pytest.fixture(autouse=True)
def _clean():
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()
    job_executor.drain_queue_for_tests()
    get_settings.cache_clear()
    yield
    clear_deployment_env_store_for_tests()
    clear_deployment_env_presence_for_tests()
    job_executor.drain_queue_for_tests()
    get_settings.cache_clear()


def test_intent_detection() -> None:
    assert is_supabase_env_completion_request("complete killit env setup")
    assert is_supabase_env_completion_request("fix killit supabase deploy")
    assert not is_supabase_env_completion_request("show my vercel apps")


def test_extract_supabase_values_from_page_text() -> None:
    page = """
    Project URL
    https://xyzcompany.supabase.co
    anon public
    eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSJ9.sig
    """
    values = _extract_supabase_values(page)
    assert values["NEXT_PUBLIC_SUPABASE_URL"] == "https://xyzcompany.supabase.co"
    assert values["NEXT_PUBLIC_SUPABASE_ANON_KEY"].startswith("eyJ")


@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.resolve_best_auth_method")
@patch("aethos_core.providers.vercel.auth.VercelAuthAdapter.get_api_token")
@patch("aethos_core.deployment_targets.resolver.resolve_deployment_target")
def test_route_creates_preflight_job(mock_target, mock_token, mock_auth) -> None:
    from aethos_core.provider_e2e_orchestration.env_completion.supabase_routing import route_supabase_env_completion

    mock_target.return_value = {"ok": True, "project_name": "killit", "repo": "pilotmain/killit"}
    mock_auth.return_value = {"method": "api_token", "credential_id": "cred-vercel-1"}
    mock_token.return_value = "vercel-token-1234567890"

    with patch.dict(
        "os.environ",
        {
            "PROVIDER_E2E_ORCHESTRATION_ENABLED": "true",
            "MUTATION_EXECUTION_ENABLED": "true",
            "PROVIDER_ENV_VAR_MUTATIONS_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        result = route_supabase_env_completion("complete supabase env for killit", session_id="sess-1")

    assert result is not None
    body, intent, meta = result
    assert intent == "supabase_env_completion_preflight"
    assert "killit" in body
    assert meta.get("job_id")


@patch("aethos_core.provider_e2e_orchestration.env_completion.supabase_executor.execute_redeploy")
@patch("aethos_core.provider_e2e_orchestration.env_completion.supabase_executor.apply_env_vars")
@patch("aethos_core.provider_e2e_orchestration.env_completion.supabase_executor.poll_deployment_status")
@patch("aethos_core.provider_e2e_orchestration.env_completion.supabase_executor.verify_health")
@patch("aethos_core.provider_e2e_orchestration.env_completion.supabase_executor.collect_supabase_values_from_sources")
def test_executor_happy_path(
    mock_collect,
    mock_verify,
    mock_poll,
    mock_redeploy,
    mock_apply,
) -> None:
    mock_collect.return_value = (
        {
            "NEXT_PUBLIC_SUPABASE_URL": "https://abc.supabase.co",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.a.b",  # gitleaks:allow - invalid fixture
        },
        {"sources": ["submitted_params"]},
    )
    mock_apply.return_value = {
        "ok": True,
        "applied_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
        "failed_names": [],
    }
    mock_redeploy.return_value = {"ok": True, "deployment_id": "dpl_123"}
    mock_poll.return_value = {
        "ok": True,
        "final_state": "ready",
        "deployment_url": "https://killit.vercel.app",
        "timeline": [],
    }
    mock_verify.return_value = {"ok": True, "url": "https://killit.vercel.app", "status_code": 200}

    with patch.dict(
        "os.environ",
        {
            "MUTATION_EXECUTION_ENABLED": "true",
            "PROVIDER_ENV_VAR_MUTATIONS_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        job = authority.create_job(
            title="Supabase env completion: killit",
            job_type=SUPABASE_ENV_COMPLETION_JOB_TYPE,
            params={
                "provider": "vercel",
                "project_name": "killit",
                "referenced_github_repo": "pilotmain/killit",
                "credential_id": "cred-vercel-1",
                "missing_env_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
                "session_id": "default",
            },
            source="test",
            session_id="default",
            auto_run=False,
        )
        gate = validate_supabase_env_completion_gate(job, for_execution=False)
        assert gate.ok is True
        approve_supabase_env_completion(job.id)
        job_executor.drain_once_for_tests()

    from aethos_core.runtime.jobs import job_store

    finished = job_store.get(job.id)
    assert finished is not None
    assert finished.params.get("execution_status") in {"completed", "running", "approved"}
    assert mock_apply.called
    assert mock_redeploy.called


def test_completion_advisor_offers_autocomplete() -> None:
    model = ProviderE2EJobModel(provider="vercel", project_name="killit")
    with patch.dict(
        "os.environ",
        {
            "PROVIDER_E2E_ORCHESTRATION_ENABLED": "true",
            "MUTATION_EXECUTION_ENABLED": "true",
            "PROVIDER_ENV_VAR_MUTATIONS_ENABLED": "true",
        },
        clear=False,
    ):
        get_settings.cache_clear()
        advisory = build_e2e_completion_advisory(
            model=model,
            params={"env_var_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"]},
            env_report={
                "applied_names": [],
                "failed_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
            },
            poll_report={},
            redeploy_report={},
            execution_status="env_failed",
        )
    assert advisory.get("can_autocomplete") is True
    assert advisory.get("autocomplete_flow") == "supabase_env_completion"
