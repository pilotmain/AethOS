# SPDX-License-Identifier: Apache-2.0
"""Reuse readonly workflow runs artifacts for mutation discovery convergence."""

from __future__ import annotations

from typing import Any


def _normalize_repo_key(value: str) -> set[str]:
    raw = (value or "").strip().lower()
    if not raw:
        return set()
    keys = {raw}
    if "/" in raw:
        keys.add(raw.split("/")[-1])
    return keys


def find_recent_readonly_workflow_runs_artifact(
    *,
    repository: str | None = None,
    target_hints: list[str] | None = None,
) -> dict[str, Any] | None:
    """Return the newest completed readonly workflow_runs payload matching the target."""
    from aethos_core.runtime.job_types import uses_readonly_execution
    from aethos_core.runtime.jobs import job_store

    wanted: set[str] = set()
    if repository:
        wanted |= _normalize_repo_key(repository)
    for hint in target_hints or []:
        wanted |= _normalize_repo_key(str(hint))

    for job in job_store.list_all():
        if job.status.value != "completed" or not uses_readonly_execution(job.job_type):
            continue
        params = job.params or {}
        if str(params.get("provider") or "") != "github":
            continue
        if str(params.get("operation_type") or "") != "workflow_runs":
            continue
        target = str(params.get("target_name") or "")
        if wanted and not (wanted & _normalize_repo_key(target)):
            continue
        readonly = params.get("readonly_execution") or {}
        if not isinstance(readonly, dict):
            continue
        findings = readonly.get("findings") or []
        for finding in findings:
            if not isinstance(finding, dict):
                continue
            if finding.get("action") != "github_api_workflow_runs":
                continue
            runs = finding.get("runs")
            if isinstance(runs, list) and runs:
                return {
                    "ok": True,
                    "repository": finding.get("repository") or target,
                    "runs": runs,
                    "run_count": len(runs),
                    "source_job_id": job.id,
                    "discovery_source": "readonly_execution_artifact",
                }
    return None
