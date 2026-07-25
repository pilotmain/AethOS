# SPDX-License-Identifier: Apache-2.0
"""Expand mutation execution failure metadata for operational truth."""

from __future__ import annotations

from typing import Any

from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason
from aethos_core.provider_skills.railway.railway_failure_classifier import classify_railway_failure
from aethos_core.provider_topology.source_binding_resolver import resolve_source_binding_for_service


def expand_failure_truth(job: Any) -> dict[str, Any] | None:
    if job is None:
        return None
    params = getattr(job, "params", None) or {}
    artifact = dict(params.get("mutation_execution") or {})
    provider_result = artifact.get("provider_result") or {}
    railway_result = artifact.get("railway_mutation_result") or {}

    base = extract_failure_reason(job)
    if base is None and params.get("executed") is not False:
        return None

    reason = str(
        (base or {}).get("failure_reason")
        or params.get("error")
        or artifact.get("error")
        or provider_result.get("detail")
        or railway_result.get("error")
        or "Provider mutation execution failed."
    )
    classify_reason = " ".join(
        filter(
            None,
            [
                reason,
                str(params.get("error") or ""),
                str(provider_result.get("detail") or ""),
                str(artifact.get("error") or ""),
            ],
        )
    )
    provider = str(params.get("provider") or artifact.get("provider") or "railway")
    operation = str(params.get("operation_type") or artifact.get("operation_type") or "mutation")
    target_payload = dict(params.get("target") or {})
    project = str(target_payload.get("project_name") or params.get("project_name") or "")
    environment = str(target_payload.get("environment") or params.get("environment") or "production")
    service = str(params.get("target_name") or target_payload.get("service_name") or "")

    binding = resolve_source_binding_for_service(
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        service_id=target_payload.get("service_id"),
        session_id=str(getattr(job, "session_id", None) or params.get("session_id") or ""),
        job_params=params,
        refresh=True,
    )

    classified = classify_railway_failure(
        reason=classify_reason,
        provider_result=provider_result if isinstance(provider_result, dict) else {},
        artifact=artifact,
        params=params,
    )
    stage = classified
    base_stage = str((base or {}).get("failure_stage") or "")
    if base_stage in {"source_binding", "verification", "logs", "target_resolution"}:
        stage = base_stage
    elif base_stage == "cli":
        stage = "railway_cli"

    execution_mode = str(
        params.get("execution_mode")
        or artifact.get("execution_mode")
        or provider_result.get("execution_mode")
        or ""
    )
    command = str(params.get("command") or artifact.get("command") or "")
    graphql_operation = str(
        provider_result.get("graphql_operation")
        or artifact.get("graphql_operation")
        or railway_result.get("graphql_operation")
        or ""
    )

    provider_error = str(
        provider_result.get("detail")
        or railway_result.get("error")
        or artifact.get("error")
        or params.get("error")
        or reason
    )
    from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding

    if binding and binding.verified and binding.github_repo and _is_superseded_source_binding_error(provider_error, binding.github_repo):
        provider_error = (
            "Historical GitHub source binding error superseded by confirmed binding. "
            "Inspect the latest Railway execution evidence for the current failure."
        )
        if stage == "source_binding" and not requires_source_binding(provider, operation):
            stage = classified if classified != "source_binding" else "railway_api"

    expanded = {
        "failure_stage": stage,
        "failure_reason": reason,
        "provider_error": provider_error,
        "raw_error_excerpt": str(
            (base or {}).get("raw_error_excerpt")
            or provider_result.get("stderr")
            or provider_result.get("detail")
            or artifact.get("error")
            or params.get("error")
            or ""
        )[:300],
        "operation": operation,
        "provider": provider,
        "target": {
            "project": project,
            "environment": environment,
            "service": service,
            "service_id": target_payload.get("service_id") or (binding.service_id if binding else None),
            "environment_id": target_payload.get("environment_id"),
            "project_id": target_payload.get("project_id"),
        },
        "source_binding": {
            "repo": binding.github_repo if binding else params.get("source_binding"),
            "verified": bool(binding.verified) if binding else False,
            "resolution_source": binding.resolution_source if binding else None,
        },
        "execution_mode": execution_mode or None,
        "graphql_operation": graphql_operation or None,
        "command": command or None,
        "next_recommended_action": (base or {}).get("next_recommended_action") or _next_action(stage, reason),
        "execution_job_id": str(getattr(job, "id", "") or params.get("mutation_execution_job_id") or ""),
    }
    return expanded


def compose_expanded_failure_reply(truth: dict[str, Any]) -> str:
    target = dict(truth.get("target") or {})
    binding = dict(truth.get("source_binding") or {})
    lines = [
        "The Railway restart failed after the source binding was corrected."
        if binding.get("verified")
        else "The Railway operation failed.",
        "",
    ]
    if binding.get("repo"):
        lines.extend(["Current binding:", f"- **{binding.get('repo')}** {'verified' if binding.get('verified') else 'unverified'}", ""])
    lines.extend(
        [
            "Failure stage:",
            f"- **{truth.get('failure_stage')}**",
            "",
            "Provider error:",
            f"- {truth.get('provider_error') or truth.get('failure_reason')}",
            "",
            "Target used:",
            f"- project: {target.get('project') or 'unknown'}",
            f"- environment: {target.get('environment') or 'unknown'}",
            f"- service: {target.get('service') or 'unknown'}",
        ]
    )
    if target.get("service_id"):
        lines.append(f"- service_id: `{target.get('service_id')}`")
    if truth.get("execution_mode"):
        lines.extend(["", f"Execution mode: `{truth.get('execution_mode')}`"])
    if truth.get("command"):
        lines.append(f"Command: `{truth.get('command')}`")
    lines.extend(["", "Next recommended action:", f"- {truth.get('next_recommended_action')}"])
    return "\n".join(lines)


def _next_action(stage: str, reason: str) -> str:
    if stage == "credentials":
        return "Verify Railway API token and mutation credentials, then retry."
    if stage == "target_resolution":
        return "Resolve exact Railway project/environment/service IDs before retrying."
    if stage == "railway_api" or stage == "provider_rejected":
        return "Inspect Railway GraphQL/API response and provider diagnostics before retrying."
    if stage == "railway_cli":
        return "Check Railway CLI auth, installation, and command output."
    if stage == "source_binding":
        return "Confirm GitHub source binding only if the operation requires source context."
    if stage == "verification":
        return "Collect Railway restart transition and log evidence after approval."
    if stage == "evidence_collection":
        return "Retry provider evidence collection and log retrieval."
    return "Review the latest execution job evidence before retrying."


def _is_superseded_source_binding_error(error: str, confirmed_repo: str) -> bool:
    import re

    text = (error or "").lower()
    if "github installation" not in text and "source binding" not in text:
        return False
    match = re.search(r"repo:\s*([a-z0-9][a-z0-9._-]*/[a-z0-9][a-z0-9._-]*)", error or "", re.I)
    if not match:
        return False
    return match.group(1).lower() != confirmed_repo.lower()
