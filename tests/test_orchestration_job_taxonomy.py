# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.orchestration.job_taxonomy import (
    CANONICAL_PREFLIGHT_JOB_TYPE,
    CANONICAL_READONLY_EXECUTION_JOB_TYPE,
    canonical_readonly_execution_job_type,
    resolve_preflight_provider,
    resolve_readonly_execution_provider,
)


def test_canonical_preflight_job_type_constant():
    assert CANONICAL_PREFLIGHT_JOB_TYPE == "operation_preflight"


def test_canonical_readonly_execution_job_type_constant():
    assert CANONICAL_READONLY_EXECUTION_JOB_TYPE == "readonly_execution"


def test_canonical_readonly_execution_job_type_for_cloud_providers():
    assert canonical_readonly_execution_job_type("railway") == "readonly_execution"
    assert canonical_readonly_execution_job_type("github") == "readonly_execution"
    assert canonical_readonly_execution_job_type("vercel") == "readonly_execution"
    assert canonical_readonly_execution_job_type("local") == "readonly_execution_local"


def test_resolve_preflight_provider_metadata_first():
    assert (
        resolve_preflight_provider(
            "operation_preflight",
            {"provider": "github", "operation_type": "workflow_runs"},
        )
        == "github"
    )


def test_resolve_preflight_provider_legacy_job_type_fallback():
    assert resolve_preflight_provider("railway_deployments_preflight", {}) == "railway"
    assert resolve_preflight_provider("github_workflow_runs_preflight", {}) == "github"
    assert resolve_preflight_provider("vercel_domains_preflight", {}) == "vercel"


def test_resolve_readonly_execution_provider_canonical_and_legacy():
    assert (
        resolve_readonly_execution_provider(
            "readonly_execution",
            {"provider": "railway"},
        )
        == "railway"
    )
    assert resolve_readonly_execution_provider("readonly_execution_railway", {}) == "railway"
    assert resolve_readonly_execution_provider("readonly_execution_github", {}) == "github"
    assert resolve_readonly_execution_provider("readonly_execution_vercel", {}) == "vercel"
