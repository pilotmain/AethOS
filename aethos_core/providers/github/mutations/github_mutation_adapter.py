# SPDX-License-Identifier: Apache-2.0
"""GitHub mutation adapter — governed workflow rerun."""

from __future__ import annotations

from typing import Any

from aethos_core.config import get_settings
from aethos_core.providers.base.mutation_adapter import MutationAdapter, MutationNotEnabledError
from aethos_core.providers.github.mutations.workflow_rerun import execute_workflow_rerun
from aethos_core.providers.github.operations.git_write_api import (
    cancel_workflow,
    commit_changes,
    create_branch,
    open_pr,
    push_branch,
    redeploy,
)


class GitHubMutationAdapter(MutationAdapter):
    provider = "github"

    @property
    def enabled(self) -> bool:
        return get_settings().mutation_execution_enabled

    def supported_mutations(self) -> list[str]:
        return [
            "workflow_rerun",
            "create_branch",
            "cancel_workflow",
            "redeploy",
            "commit_changes",
            "push_branch",
            "open_pr",
        ]

    def dry_run(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        target = str(params.get("target_name") or "(unknown)")
        if operation == "create_branch":
            new_branch = str(params.get("new_branch") or "(new-branch)")
            base = str(params.get("base_branch") or "the default branch")
            return {
                "ok": True,
                "dry_run": True,
                "operation": operation,
                "target_name": target,
                "detail": f"Would create branch `{new_branch}` from `{base}` in `{target}` — no mutation performed.",
            }
        if operation == "cancel_workflow":
            run = str(params.get("run_id") or "the latest in-flight run")
            return {
                "ok": True,
                "dry_run": True,
                "operation": operation,
                "target_name": target,
                "detail": f"Would cancel workflow run `{run}` in `{target}` — no mutation performed.",
            }
        if operation == "redeploy":
            return {
                "ok": True,
                "dry_run": True,
                "operation": operation,
                "target_name": target,
                "detail": f"Would redeploy `{target}` by re-running its latest workflow run — no mutation performed.",
            }
        if operation in ("commit_changes", "push_branch", "open_pr"):
            details = {
                "commit_changes": f"Would commit {len(params.get('files') or {})} file(s) to `{params.get('branch') or '(branch)'}` in `{target}` — no mutation performed.",
                "push_branch": f"Would update branch `{params.get('branch') or '(branch)'}` to `{str(params.get('sha') or '(sha)')[:7]}` in `{target}` — no mutation performed.",
                "open_pr": f"Would open a PR `{params.get('head') or '(head)'}` → `{params.get('base') or '(base)'}` in `{target}` — no mutation performed.",
            }
            return {"ok": True, "dry_run": True, "operation": operation, "target_name": target, "detail": details[operation]}
        resolution = params.get("workflow_resolution") if isinstance(params.get("workflow_resolution"), dict) else {}
        workflow = resolution.get("workflow_name") or resolution.get("workflow_id") or "latest workflow"
        return {
            "ok": True,
            "dry_run": True,
            "operation": operation,
            "target_name": target,
            "detail": f"Would rerun failed workflow `{workflow}` for `{target}` — no mutation performed.",
        }

    def execute(self, *, operation: str, params: dict[str, Any]) -> dict[str, Any]:
        self.assert_enabled()
        if operation not in self.supported_mutations():
            raise MutationNotEnabledError(f"Unsupported GitHub mutation: {operation}")
        from aethos_core.operations.orchestration.provider_runtime import get_provider_api_token, resolve_execution_auth

        auth = resolve_execution_auth(provider="github", operation_type=operation, params=params)
        token = get_provider_api_token(provider="github", auth=auth)
        if not token:
            return {
                "ok": False,
                "detail": "GitHub credential not configured for mutation execution.",
                "failure_type": "provider_auth_failure",
                "failure_classification": "provider_auth_failure",
            }
        target = str(params.get("target_name") or "")
        if not target:
            return {"ok": False, "detail": "Target repository required.", "failure_type": "target_unresolved"}

        if operation == "create_branch":
            return create_branch(
                token,
                repository=target,
                new_branch=str(params.get("new_branch") or ""),
                base_branch=(str(params.get("base_branch")) if params.get("base_branch") else None),
            )

        if operation == "cancel_workflow":
            return cancel_workflow(
                token,
                repository=target,
                run_id=(params.get("run_id") if params.get("run_id") else None),
            )

        if operation == "redeploy":
            return redeploy(token, repository=target)

        if operation == "commit_changes":
            files = params.get("files") if isinstance(params.get("files"), dict) else {}
            return commit_changes(
                token,
                repository=target,
                branch=str(params.get("branch") or ""),
                message=str(params.get("message") or ""),
                files={str(k): str(v) for k, v in files.items()},
            )
        if operation == "push_branch":
            return push_branch(
                token,
                repository=target,
                branch=str(params.get("branch") or ""),
                sha=str(params.get("sha") or ""),
                force=bool(params.get("force")),
            )
        if operation == "open_pr":
            return open_pr(
                token,
                repository=target,
                head=str(params.get("head") or ""),
                base=str(params.get("base") or ""),
                title=str(params.get("title") or ""),
                body=str(params.get("body") or ""),
            )

        workflow_resolution = params.get("workflow_resolution")
        return execute_workflow_rerun(
            token,
            repository=target,
            workflow_resolution=workflow_resolution if isinstance(workflow_resolution, dict) else None,
        )
