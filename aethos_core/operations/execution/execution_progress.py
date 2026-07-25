# SPDX-License-Identifier: Apache-2.0
"""Read-only execution progress labels — provider-agnostic steps."""

from __future__ import annotations

from typing import Any, Callable

ProgressFn = Callable[[str], None]

ACTION_PROGRESS: dict[str, str] = {
    "auth": "Resolving auth",
    "vercel_api_deployments": "Fetching deployments",
    "vercel_api_domains": "Fetching domains",
    "vercel_api_project_details": "Fetching project details",
    "vercel_logs_inspect": "Fetching deployment events",
    "vercel_deployment_inspect": "Inspecting deployment",
    "url_reachability": "Checking URL reachability",
    "git_status": "Reading git status",
    "git_branch": "Reading git branch",
    "package_scripts": "Reading package scripts",
}


def progress_emitter(job_id: str | None) -> ProgressFn | None:
    if not job_id:
        return None
    from aethos_core.runtime.jobs import job_store

    def emit(message: str) -> None:
        job_store.emit_progress(job_id, message)

    return emit


def emit_step(progress: ProgressFn | None, step: str) -> None:
    if progress:
        progress(step)
