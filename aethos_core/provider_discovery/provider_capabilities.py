# SPDX-License-Identifier: Apache-2.0
"""Provider capability matrix — supported operations per provider."""

from __future__ import annotations

from typing import Any

_RAILWAY_READONLY = ["list_services", "list_deployments", "check_health", "read_logs", "read_variables", "show_domains", "show_latest_change"]
_RAILWAY_MUTATING = ["restart", "redeploy", "deploy_latest", "set_env_var", "rollback"]
_RAILWAY_DIAGNOSTIC = ["diagnose_failure", "what_changed", "missing_config", "deploy_failure_analysis"]

_PROVIDER_CAPABILITIES: dict[str, dict[str, list[str]]] = {
    "railway": {
        "readonly": _RAILWAY_READONLY,
        "mutating": _RAILWAY_MUTATING,
        "diagnostic": _RAILWAY_DIAGNOSTIC,
    },
    "vercel": {
        "readonly": ["list_projects", "list_deployments", "read_build_logs", "domain_status"],
        "mutating": ["redeploy", "rollback", "set_env_var"],
        "diagnostic": ["diagnose_failure", "build_failure_analysis"],
    },
    "github": {
        "readonly": ["list_workflows", "list_runs", "read_logs", "list_prs", "list_commits"],
        "mutating": ["rerun_workflow", "rollback_pr"],
        "diagnostic": ["workflow_failure_analysis"],
    },
    "docker": {
        "readonly": ["list_containers", "read_logs", "health_check"],
        "mutating": ["restart", "rebuild"],
        "diagnostic": ["container_failure_analysis"],
    },
    "kubernetes": {
        "readonly": ["list_deployments", "list_pods", "read_logs", "read_events"],
        "mutating": ["rollout_restart", "rollback"],
        "diagnostic": ["pod_failure_analysis"],
    },
}


def provider_capabilities(provider: str) -> dict[str, list[str]]:
    return dict(_PROVIDER_CAPABILITIES.get((provider or "").strip().lower(), {}))


def service_supported_operations(*, provider: str, service_type: str = "web") -> list[str]:
    caps = provider_capabilities(provider)
    ops = list(caps.get("readonly") or []) + list(caps.get("mutating") or [])
    if provider == "railway":
        base = ["restart", "redeploy", "logs", "variables", "health_check"]
        if service_type in {"worker", "cron", "scheduler"}:
            return base
        return base + ["deploy_latest"]
    return ops


def capabilities_public_dict(provider: str) -> dict[str, Any]:
    caps = provider_capabilities(provider)
    return {
        "provider": provider,
        "readonly": list(caps.get("readonly") or []),
        "mutating": list(caps.get("mutating") or []),
        "diagnostic": list(caps.get("diagnostic") or []),
        "mutation_requires_approval": True,
    }
