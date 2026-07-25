# SPDX-License-Identifier: Apache-2.0
"""Extract structured failure reasons from mutation execution jobs."""

from __future__ import annotations

from typing import Any


def extract_failure_reason(job: Any) -> dict[str, Any] | None:
    if job is None:
        return None
    params = getattr(job, "params", None) or {}
    artifact = dict(params.get("mutation_execution") or {})
    exec_state = str(params.get("execution_state") or artifact.get("execution_state") or "")
    executed = params.get("executed")
    provider_result = artifact.get("provider_result") or {}
    railway_result = artifact.get("railway_mutation_result") or {}

    if executed is not False and exec_state != "execution_failed":
        restart_state = str(
            params.get("restart_verification_state")
            or (params.get("verification_artifact") or {}).get("evidence", {}).get("restart_verification_state")
            or ""
        )
        if restart_state in {"restart_unverified", "service_online_but_restart_unproven", "verification_failed"}:
            logs_unavailable = _logs_unavailable(params, artifact)
            if logs_unavailable:
                return {
                    "failure_reason": "Restart verification failed — Railway logs are unavailable for post-approval evidence.",
                    "failure_stage": "logs",
                    "provider_error": restart_state,
                    "raw_error_excerpt": str(params.get("lifecycle_summary") or artifact.get("error") or "")[:300],
                    "next_recommended_action": "Retry log collection or inspect Railway deployment history directly.",
                }
            return {
                "failure_reason": "Restart command submitted but provider-side restart evidence is missing.",
                "failure_stage": "verification",
                "provider_error": restart_state,
                "raw_error_excerpt": str(params.get("lifecycle_summary") or artifact.get("error") or "")[:300],
                "next_recommended_action": "Collect Railway logs and runtime evidence after approval.",
            }
        if params.get("restart_command_submitted") is False:
            return {
                "failure_reason": str(
                    provider_result.get("detail")
                    or artifact.get("error")
                    or railway_result.get("error")
                    or "Railway did not confirm the restart command."
                ),
                "failure_stage": _infer_stage(provider_result, artifact),
                "provider_error": str(provider_result.get("detail") or railway_result.get("error") or ""),
                "raw_error_excerpt": _raw_excerpt(provider_result, artifact, railway_result),
                "next_recommended_action": "Review Railway credentials, target resolution, and provider diagnostics.",
            }
        return None

    reason = str(
        artifact.get("error")
        or provider_result.get("detail")
        or railway_result.get("error")
        or params.get("error")
        or "Provider mutation execution failed."
    )
    lower_reason = reason.lower()
    if "credential" in lower_reason or "token missing" in lower_reason or "api token" in lower_reason:
        reason = "Railway mutation credentials are not configured."
        stage = "credentials"
    else:
        stage = _infer_stage(provider_result, artifact)
    if "service id" in lower_reason or "service_id" in lower_reason or "service not found" in lower_reason:
        stage = "target_resolution"
    elif "environment id" in lower_reason or "environment not found" in lower_reason:
        stage = "target_resolution"
    elif "project id" in lower_reason or "project not found" in lower_reason:
        stage = "target_resolution"
    if "github installation" in lower_reason or "installation found for repo" in lower_reason:
        stage = "source_binding"
        stored_repo = _extract_repo_from_installation_error(reason)
        if stored_repo:
            service = str(params.get("target_name") or "")
            example_repo = _suggest_replacement_repo(stored_repo, service)
            reason = (
                f"The restart failed before Railway mutation because the stored source binding still points to **{stored_repo}**."
            )
            next_action = (
                "If this repo moved, tell me the new repo, for example:\n"
                f'`use {example_repo} instead`\n\n'
                "I can then verify access, update the source binding, and retry the governed restart."
            )
            return {
                "failure_reason": reason,
                "failure_stage": stage,
                "provider_error": stored_repo,
                "raw_error_excerpt": _raw_excerpt(provider_result, artifact, railway_result),
                "next_recommended_action": next_action,
            }
    if params.get("target_resolved") is False or "target" in reason.lower():
        stage = "target_resolution"
    return {
        "failure_reason": reason,
        "failure_stage": stage,
        "provider_error": str(provider_result.get("detail") or railway_result.get("error") or reason),
        "raw_error_excerpt": _raw_excerpt(provider_result, artifact, railway_result),
        "next_recommended_action": _next_action(stage, reason),
    }


def _infer_stage(provider_result: dict[str, Any], artifact: dict[str, Any]) -> str:
    failure_type = str(provider_result.get("failure_type") or artifact.get("failure_type") or "")
    if failure_type == "provider_auth_failure":
        return "provider_api"
    mode = str(provider_result.get("execution_mode") or artifact.get("execution_mode") or "")
    if mode == "cli":
        return "cli"
    if provider_result.get("graphql_errors"):
        return "provider_api"
    if artifact.get("restart_command_submitted") is False:
        return "command_submission"
    return "provider_api"


def _raw_excerpt(
    provider_result: dict[str, Any],
    artifact: dict[str, Any],
    railway_result: dict[str, Any],
) -> str:
    for source in (provider_result, artifact, railway_result):
        for key in ("stderr", "detail", "error", "stdout"):
            val = source.get(key)
            if val:
                return str(val)[:300]
    return ""


def _extract_repo_from_installation_error(reason: str) -> str | None:
    import re

    match = re.search(r"repo:\s*([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)", reason, re.I)
    return match.group(1) if match else None


def _suggest_replacement_repo(stored_repo: str, service_name: str) -> str:
    if service_name:
        try:
            from aethos_core.deployment_targets.registry import find_target_by_alias

            row = find_target_by_alias(service_name)
            if row and row.get("repo"):
                return str(row["repo"])
        except Exception:
            pass
    if "/" not in stored_repo:
        return stored_repo if service_name and stored_repo else (f"{service_name}/{service_name}" if service_name else stored_repo)
    owner, repo = stored_repo.split("/", 1)
    if service_name and repo.lower() != service_name.lower():
        return f"{owner}/{service_name}"
    return stored_repo


def _next_action(stage: str, reason: str) -> str:
    if stage == "logs":
        return "Retry log collection or inspect Railway deployment history directly."
    if stage == "source_binding":
        return "Refresh provider topology and confirm the correct GitHub repository binding before retrying."
    if stage == "target_resolution":
        return "Resolve the exact Railway service target before retrying."
    if stage == "provider_api" or "credential" in reason.lower():
        return "Verify Railway API token and project/service IDs, then retry."
    if stage == "cli":
        return "Check Railway CLI installation, auth, and command output."
    if stage == "verification":
        return "Collect Railway logs and runtime evidence after approval."
    if stage == "command_submission":
        return "Inspect provider command response and mutation diagnostics."
    return "Review execution job evidence and Railway logs before retrying."


def _logs_unavailable(params: dict[str, Any], artifact: dict[str, Any]) -> bool:
    bundle = params.get("provider_evidence_bundle") or artifact.get("provider_evidence_bundle") or {}
    if isinstance(bundle, dict):
        if bundle.get("logs_unavailable") is True:
            return True
        logs = bundle.get("logs_excerpt")
        if logs is not None and not logs:
            return True
    if str(params.get("logs_status") or artifact.get("logs_status") or "").lower() in {"unavailable", "missing", "failed"}:
        return True
    return False
