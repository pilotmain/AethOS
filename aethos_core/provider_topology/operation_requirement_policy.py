# SPDX-License-Identifier: Apache-2.0
"""Decide whether source binding is required for provider operations."""

from __future__ import annotations


def requires_source_binding(provider: str, operation: str, *, execution_mode: str | None = None) -> bool:
    provider = (provider or "").strip().lower()
    operation = (operation or "").strip().lower().replace("-", "_")
    mode = (execution_mode or "").strip().lower()

    if provider == "railway":
        if operation in {"restart", "set_env_var", "env_change"}:
            return False
        if operation in {"redeploy", "redeploy_latest"}:
            return mode in {"deploy_from_source", "source_linked"}
        if operation in {"deploy", "deploy_latest", "deploy_from_git", "deploy_from_source"}:
            return True
        return False

    if provider == "vercel":
        if operation in {"deploy", "deploy_from_git", "redeploy", "deploy_latest"}:
            return True
        return False

    if provider == "github":
        return operation in {"workflow_rerun", "deploy", "workflow_dispatch"}

    if provider in {"docker", "kubernetes"}:
        return operation in {"deploy", "rollout", "redeploy"}

    return False


def binding_required_message(provider: str, operation: str) -> str:
    if requires_source_binding(provider, operation):
        return f"Operation `{operation}` on `{provider}` requires a verified source binding."
    return f"Operation `{operation}` on `{provider}` does not require GitHub source binding."
