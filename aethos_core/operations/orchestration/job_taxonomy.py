# SPDX-License-Identifier: Apache-2.0
"""Canonical orchestration job taxonomy — Phase 9.3M Slice F."""

from __future__ import annotations

from typing import Any

CANONICAL_PREFLIGHT_JOB_TYPE = "operation_preflight"
CANONICAL_READONLY_EXECUTION_JOB_TYPE = "readonly_execution"

LEGACY_READONLY_EXECUTION_BY_PROVIDER: dict[str, str] = {
    "vercel": "readonly_execution_vercel",
    "railway": "readonly_execution_railway",
    "github": "readonly_execution_github",
    "local": "readonly_execution_local",
}


def resolve_preflight_provider(job_type: str, params: dict[str, Any]) -> str:
    """Resolve provider for preflight routing — metadata first, legacy job_type fallback."""
    provider = str(params.get("provider") or "").strip().lower()
    if provider:
        return provider
    if job_type.startswith("railway_"):
        return "railway"
    if job_type.startswith("github_"):
        return "github"
    if job_type.startswith("vercel_"):
        return "vercel"
    if job_type.startswith("local_"):
        return "local"
    return "unknown"


def resolve_readonly_execution_provider(job_type: str, params: dict[str, Any]) -> str:
    """Resolve provider for readonly execution dispatch."""
    provider = str(params.get("provider") or "").strip().lower()
    if provider:
        return provider
    if job_type == "readonly_execution_local":
        return "local"
    if job_type == "readonly_execution_railway":
        return "railway"
    if job_type == "readonly_execution_github":
        return "github"
    if job_type == "readonly_execution_vercel":
        return "vercel"
    if job_type == CANONICAL_READONLY_EXECUTION_JOB_TYPE:
        return provider or "vercel"
    return "unknown"


def canonical_readonly_execution_job_type(provider: str) -> str:
    """Return canonical execution job type for new jobs; local stays specialized."""
    if provider == "local":
        return LEGACY_READONLY_EXECUTION_BY_PROVIDER["local"]
    return CANONICAL_READONLY_EXECUTION_JOB_TYPE


def is_canonical_preflight_job(job_type: str) -> bool:
    return job_type == CANONICAL_PREFLIGHT_JOB_TYPE


def is_canonical_readonly_execution_job(job_type: str) -> bool:
    return job_type == CANONICAL_READONLY_EXECUTION_JOB_TYPE
