# SPDX-License-Identifier: Apache-2.0
"""GitHub read-only execution adapter."""

from __future__ import annotations

from typing import Any

from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter
from aethos_core.providers.github.operations.workflow_runs_api import (
    fetch_workflow_runs,
    format_workflow_runs_output,
)
from aethos_core.providers.github.operations.workflow_diagnostics_api import (
    fetch_workflow_diagnostic,
    format_workflow_diagnostic_output,
)
from aethos_core.providers.github.operations.workflow_jobs_api import (
    fetch_workflow_jobs,
    format_workflow_jobs_output,
)


class GitHubReadonlyExecutionAdapter(ReadonlyExecutionAdapter):
    provider = "github"

    def __init__(self, token: str, *, credential_id: str = "") -> None:
        self._token = token
        self._credential_id = credential_id

    def get_deployments(self, *, project_name: str, limit: int = 20) -> dict[str, Any]:
        _ = project_name, limit
        return {"ok": False, "source": "provider_api", "error": "GitHub deployments read is not enabled yet.", "deployments": []}

    def get_domains(self, *, project_name: str) -> dict[str, Any]:
        _ = project_name
        return {"ok": False, "source": "provider_api", "error": "GitHub domains read is not enabled yet.", "domains": []}

    def get_project_details(self, *, project_name: str) -> dict[str, Any]:
        _ = project_name
        return {"ok": False, "source": "provider_api", "error": "GitHub project details read is not enabled yet.", "details": {}}

    def get_deployment_logs(
        self,
        *,
        project_name: str,
        deployment_id: str | None = None,
        project_id: str | None = None,
        team_id: str | None = None,
    ) -> dict[str, Any]:
        _ = project_name, deployment_id, project_id, team_id
        return {"ok": False, "source": "provider_api", "error": "GitHub deployment logs read is not enabled yet."}

    def get_workflow_runs(self, *, repository: str, limit: int = 20) -> dict[str, Any]:
        payload = fetch_workflow_runs(self._token, repository=repository, limit=limit)
        payload["output"] = format_workflow_runs_output(payload)
        return payload

    def get_workflow_diagnostic(self, *, repository: str, run_limit: int = 30) -> dict[str, Any]:
        payload = fetch_workflow_diagnostic(self._token, repository=repository, run_limit=run_limit)
        payload["output"] = format_workflow_diagnostic_output(payload)
        return payload

    def get_workflow_jobs(self, *, repository: str, run_limit: int = 30) -> dict[str, Any]:
        payload = fetch_workflow_jobs(self._token, repository=repository, run_limit=run_limit)
        payload["output"] = format_workflow_jobs_output(payload)
        return payload

    def inspect_repo(self, *, repository: str) -> dict[str, Any]:
        from aethos_core.providers.github.operations.repo_readonly_api import inspect_repo

        return inspect_repo(self._token, repository=repository)

    def get_branch_status(self, *, repository: str, branch: str | None = None) -> dict[str, Any]:
        from aethos_core.providers.github.operations.repo_readonly_api import fetch_branch_status

        return fetch_branch_status(self._token, repository=repository, branch=branch)

    def get_recent_commits(self, *, repository: str, limit: int = 10) -> dict[str, Any]:
        from aethos_core.providers.github.operations.repo_readonly_api import fetch_recent_commits

        return fetch_recent_commits(self._token, repository=repository, limit=limit)

    def get_failed_checks(self, *, repository: str, ref: str | None = None) -> dict[str, Any]:
        from aethos_core.providers.github.operations.repo_readonly_api import fetch_failed_checks

        return fetch_failed_checks(self._token, repository=repository, ref=ref)

    def get_workflow_logs(self, *, repository: str, run_limit: int = 10) -> dict[str, Any]:
        payload = fetch_workflow_jobs(self._token, repository=repository, run_limit=run_limit)
        payload["operation"] = "workflow_logs"
        payload["output"] = format_workflow_jobs_output(payload)
        return payload


def adapter_from_credential(credential_id: str) -> GitHubReadonlyExecutionAdapter | None:
    from aethos_core.providers.github.auth import GitHubAuthAdapter

    token = GitHubAuthAdapter().get_api_token(credential_id)
    if not token:
        return None
    return GitHubReadonlyExecutionAdapter(token, credential_id=credential_id)
