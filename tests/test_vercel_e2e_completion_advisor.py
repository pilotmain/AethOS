# SPDX-License-Identifier: Apache-2.0
"""Tests for Vercel build env criticality and E2E completion advisor."""

from __future__ import annotations

from aethos_core.provider_e2e_orchestration.e2e_completion_advisor import (
    build_e2e_completion_advisory,
    compose_completion_advisory_report,
)
from aethos_core.provider_e2e_orchestration.job_model import ProviderE2EJobModel
from aethos_core.providers.vercel.greenfield_deployment.build_env_criticality import list_build_critical_env_names


def test_next_public_vars_are_build_critical() -> None:
    names = list_build_critical_env_names(
        ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "LOG_LEVEL"],
        framework="nextjs",
    )
    assert "NEXT_PUBLIC_SUPABASE_URL" in names
    assert "NEXT_PUBLIC_SUPABASE_ANON_KEY" in names
    assert "LOG_LEVEL" not in names


def test_completion_advisory_for_missing_supabase_env() -> None:
    model = ProviderE2EJobModel(provider="vercel", project_name="killit")
    params = {
        "env_var_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY", "ANTHROPIC_API_KEY"],
        "target_plan": {"framework": "nextjs", "project_name": "killit"},
    }
    env_report = {
        "applied_names": ["ANTHROPIC_API_KEY"],
        "failed_names": ["NEXT_PUBLIC_SUPABASE_URL", "NEXT_PUBLIC_SUPABASE_ANON_KEY"],
        "all_required_names": params["env_var_names"],
    }
    advisory = build_e2e_completion_advisory(
        model=model,
        params=params,
        env_report=env_report,
        poll_report={"detail": "Deployment failed."},
        redeploy_report={},
        execution_status="env_failed",
    )
    report = compose_completion_advisory_report(advisory)
    assert "Supabase" in report
    assert "What I need from you" in report
    assert "supabase" in (advisory.get("integration_gaps") or {})
