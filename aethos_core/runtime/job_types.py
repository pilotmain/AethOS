# SPDX-License-Identifier: Apache-2.0
"""Tracked job type registry — local vs provider-backed vs external."""

from __future__ import annotations

LOCAL_JOB_TYPES = frozenset(
    {
        "manual_note",
        "checklist_generation",
        "runtime_action_followup",
        "governed_observation_cycle",
    }
)

PROVIDER_JOB_TYPES = frozenset(
    {
        "research_plan",
        "comparison_brief",
        "roadmap_generation",
        "architecture_summary",
        "planning_document",
    }
)

EXTERNAL_JOB_TYPES = frozenset(
    {
        "external_health_report",
    }
)

VERCEL_READONLY_JOB_TYPES = frozenset(
    {
        "vercel_projects_inventory",
        "vercel_service_health_summary",
        "vercel_deployment_status_summary",
    }
)

RAILWAY_READONLY_JOB_TYPES = frozenset(
    {
        "railway_services_inventory",
    }
)

GITHUB_READONLY_JOB_TYPES = frozenset(
    {
        "github_repositories_inventory",
    }
)

OPERATION_PREFLIGHT_JOB_TYPES = frozenset(
    {
        "operation_preflight",
        "vercel_redeploy_preflight",
        "vercel_restart_preflight",
        "vercel_logs_preflight",
        "vercel_env_var_preflight",
        "vercel_down_diagnostic_preflight",
        "vercel_domains_preflight",
        "vercel_deployments_preflight",
        "vercel_project_details_preflight",
        "local_workspace_fix_preflight",
        "railway_redeploy_preflight",
        "railway_restart_preflight",
        "railway_logs_preflight",
        "railway_env_var_preflight",
        "railway_down_diagnostic_preflight",
        "railway_deployments_preflight",
        "railway_project_details_preflight",
        "github_workflow_runs_preflight",
        "github_workflow_diagnostic_preflight",
        "github_workflow_jobs_preflight",
    }
)

MUTATION_PREFLIGHT_JOB_TYPES = frozenset(
    {
        "mutation_preflight",
    }
)

MUTATION_EXECUTION_JOB_TYPES = frozenset(
    {
        "mutation_execution",
    }
)

READONLY_EXECUTION_JOB_TYPES = frozenset(
    {
        "readonly_execution",
        "readonly_execution_vercel",
        "readonly_execution_local",
        "readonly_execution_railway",
        "readonly_execution_github",
    }
)

BROWSER_EVIDENCE_JOB_TYPES = frozenset(
    {
        "browser_capture_execution",
        "browser_evidence_list",
    }
)

AGENT_COORDINATION_JOB_TYPES = frozenset(
    {
        "agent_coordination",
    }
)

ENGINEERING_JOB_TYPES = frozenset(
    {
        "engineering_preflight",
        "engineering_execution",
        "engineering_validation",
        "engineering_pr_draft",
    }
)

PROVIDER_E2E_ORCHESTRATION_JOB_TYPES = frozenset({"provider_e2e_orchestration"})

RAILWAY_GREENFIELD_JOB_TYPES = frozenset(
    {
        "railway_greenfield_deployment_preflight",
    }
)

VERCEL_GREENFIELD_JOB_TYPES = frozenset(
    {
        "vercel_greenfield_deployment_preflight",
    }
)

SUPABASE_ENV_COMPLETION_JOB_TYPES = frozenset(
    {
        "supabase_env_completion",
    }
)


def uses_railway_greenfield(job_type: str) -> bool:
    return job_type in RAILWAY_GREENFIELD_JOB_TYPES


def uses_provider_e2e_orchestration(job_type: str) -> bool:
    return job_type in PROVIDER_E2E_ORCHESTRATION_JOB_TYPES


def uses_supabase_env_completion(job_type: str) -> bool:
    return job_type in SUPABASE_ENV_COMPLETION_JOB_TYPES


JOB_TYPES = (
    LOCAL_JOB_TYPES
    | PROVIDER_JOB_TYPES
    | EXTERNAL_JOB_TYPES
    | VERCEL_READONLY_JOB_TYPES
    | RAILWAY_READONLY_JOB_TYPES
    | GITHUB_READONLY_JOB_TYPES
    | OPERATION_PREFLIGHT_JOB_TYPES
    | MUTATION_PREFLIGHT_JOB_TYPES
    | MUTATION_EXECUTION_JOB_TYPES
    | READONLY_EXECUTION_JOB_TYPES
    | BROWSER_EVIDENCE_JOB_TYPES
    | AGENT_COORDINATION_JOB_TYPES
    | ENGINEERING_JOB_TYPES
    | PROVIDER_E2E_ORCHESTRATION_JOB_TYPES
    | RAILWAY_GREENFIELD_JOB_TYPES
    | VERCEL_GREENFIELD_JOB_TYPES
    | SUPABASE_ENV_COMPLETION_JOB_TYPES
)


def uses_provider(job_type: str) -> bool:
    return job_type in PROVIDER_JOB_TYPES


def uses_external(job_type: str) -> bool:
    return job_type in EXTERNAL_JOB_TYPES


def uses_vercel_readonly(job_type: str) -> bool:
    return job_type in VERCEL_READONLY_JOB_TYPES


def uses_railway_readonly(job_type: str) -> bool:
    return job_type in RAILWAY_READONLY_JOB_TYPES


def uses_github_readonly(job_type: str) -> bool:
    return job_type in GITHUB_READONLY_JOB_TYPES


def uses_operation_preflight(job_type: str) -> bool:
    return job_type in OPERATION_PREFLIGHT_JOB_TYPES


def uses_readonly_execution(job_type: str) -> bool:
    return job_type in READONLY_EXECUTION_JOB_TYPES


def uses_mutation_preflight(job_type: str) -> bool:
    return job_type in MUTATION_PREFLIGHT_JOB_TYPES


def uses_mutation_execution(job_type: str) -> bool:
    return job_type in MUTATION_EXECUTION_JOB_TYPES


def uses_browser_evidence(job_type: str) -> bool:
    return job_type in BROWSER_EVIDENCE_JOB_TYPES


def uses_agent_coordination(job_type: str) -> bool:
    return job_type in AGENT_COORDINATION_JOB_TYPES


def uses_engineering(job_type: str) -> bool:
    return job_type in ENGINEERING_JOB_TYPES
