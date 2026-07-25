# SPDX-License-Identifier: Apache-2.0
"""Mutation preflight chat routing — design-only, no execution."""

from __future__ import annotations

from typing import Any

from aethos_core.chat.mutation_target_chat import gate_railway_mutation_preflight
from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.operations.execution.execution_permissions import is_mutating_operation
from aethos_core.operations.intents import infer_operation_preflight_intent
from aethos_core.operations.mutations.secrets import parse_env_var_from_request
from aethos_core.operations.mutations.taxonomy import (
    CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
    is_mutation_operation,
)
from aethos_core.providers.railway.target_resolver import TARGET_APPROVAL_THRESHOLD
from aethos_core.runtime.authority import authority


def _mutation_preflight_job_title(title: str, *, operation_type: str) -> str:
    if operation_type == "workflow_rerun":
        return title if title.endswith("preflight") else f"{title} preflight"
    if " mutation preflight" in title:
        return title
    return title.replace(" preflight", " mutation preflight")


def _github_workflow_rerun_noop_reply(
    text: str,
    *,
    session_id: str,
    params: dict[str, Any],
) -> tuple[str, str, dict[str, str]] | None:
    if str(params.get("provider") or "") != "github" or str(params.get("operation_type") or "") != "workflow_rerun":
        return None
    from aethos_core.providers.github.context.github_context_store import (
        compose_no_failed_workflow_guidance,
        resolve_rerun_repository,
    )
    from aethos_core.providers.github.mutations.workflow_rerun_preflight import prepare_workflow_rerun_preflight

    repo_resolution = resolve_rerun_repository(
        session_id=session_id,
        user_request=text,
        target_hints=list(params.get("target_hints") or []),
        repository=str(params.get("target_name") or ""),
    )
    if not repo_resolution.get("repo"):
        return None
    discovery = prepare_workflow_rerun_preflight(
        session_id=session_id,
        target_name=str(repo_resolution["repo"]),
        user_request=text,
        target_hints=list(params.get("target_hints") or []),
    )
    if not discovery.get("no_failed_workflow"):
        return None
    repo = str(discovery.get("repository") or repo_resolution["repo"])
    body = "\n".join(compose_no_failed_workflow_guidance(repository=repo))
    return (
        body,
        "github_workflow_rerun_no_action",
        {
            "route_id": "github_workflow_rerun",
            "provider": "github",
            "operation_type": "workflow_rerun",
            "preflight_status": "no_action_available",
            "repository": repo,
        },
    )


def create_mutation_preflight_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.chat.informational_turn_classifier import should_block_mutation_routing

    if should_block_mutation_routing(text, session_id=session_id):
        return None

    from aethos_core.devops_intent_planner.devops_request_classifier import should_block_mutation_preflight

    if should_block_mutation_preflight(text, session_id=session_id):
        return None

    from aethos_core.providers.railway.greenfield_deployment.deployment_status_followup_router import (
        is_railway_deployment_status_followup,
    )
    from aethos_core.operational_thread_memory.solo_greenfield_thread_memory import (
        resolve_greenfield_deployment_thread,
    )

    if is_railway_deployment_status_followup(text) and resolve_greenfield_deployment_thread(session_id=session_id):
        return None

    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(text):
        return None

    from aethos_core.chat.local_system_guidance import is_local_aethos_api_restart_intent

    if is_local_aethos_api_restart_intent(text):
        return None

    from aethos_core.chat.explicit_mutation_intent import has_explicit_mutation_verb
    from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request
    from aethos_core.provider_topology.repo_reference_parser import is_railway_restart_with_repo_target
    from aethos_core.provider_topology.source_binding_chat import compose_source_binding_correction_reply

    if is_provider_followup_request(text, session_id=session_id) and not has_explicit_mutation_verb(text):
        return None

    if is_railway_restart_with_repo_target(text):
        correction = compose_source_binding_correction_reply(text, session_id=session_id)
        if correction is not None:
            return correction

    from aethos_core.operations.mutations.stop_mutation import compose_stop_mutation_preflight_reply

    stop_reply = compose_stop_mutation_preflight_reply(text, session_id=session_id)
    if stop_reply is not None:
        return stop_reply

    from aethos_core.provider_topology.followup_lock import (
        compose_thread_continuation_reply,
        get_locked_thread_context,
        should_block_unrelated_preflight,
    )

    if should_block_unrelated_preflight(text, session_id=session_id):
        from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request

        if is_provider_followup_request(text, session_id=session_id):
            return None
        cont = compose_thread_continuation_reply(text, session_id=session_id)
        if cont is not None:
            return cont
        inferred_probe = infer_operation_preflight_intent(text, session_id=session_id)
        if inferred_probe is not None:
            probe_provider = str(inferred_probe[2].get("provider") or "")
            thread = get_locked_thread_context(session_id=session_id)
            if thread and probe_provider and probe_provider != thread.provider:
                return (
                    f"I'm continuing the active **{thread.provider}** {thread.operation or 'operation'} thread for **{thread.service_path()}** — not creating a **{probe_provider}** preflight.\n\n"
                    "Tell me what you need for this Railway operation, or explicitly switch provider if you want a different target.",
                    "operational_thread_lock",
                    {"provider": thread.provider, "blocked_provider": probe_provider, "service": str(thread.service or "")},
                )

    inferred = infer_operation_preflight_intent(text, session_id=session_id)
    if inferred is None:
        return None
    title, _job_type, params = inferred
    operation_type = str(params.get("operation_type") or "")
    if not is_mutating_operation(operation_type) and not is_mutation_operation(operation_type):
        return None

    from aethos_core.operation_lifecycle.lifecycle_resolver import compose_duplicate_mutation_reply, is_duplicate_mutation_request

    duplicate, dup_state = is_duplicate_mutation_request(
        text,
        session_id=session_id,
        provider=str(params.get("provider") or "") or None,
        operation=operation_type,
        service=str(params.get("target_name") or "") or None,
    )
    if duplicate and dup_state:
        return (
            compose_duplicate_mutation_reply(dup_state),
            "operation_lifecycle_duplicate_blocked",
            {"match_key": dup_state.match_key, "preflight_job_id": dup_state.preflight_job_id or ""},
        )

    env_meta = parse_env_var_from_request(text)
    if env_meta:
        params = {**params, **env_meta}

    gated_params, clarification = gate_railway_mutation_preflight(
        text=text,
        params=params,
        operation_type=operation_type,
    )
    if clarification:
        from aethos_core.providers.railway.target_resolver import resolve_railway_provider_target
        from aethos_core.task_frame.clarification_state import (
            candidates_from_target_resolution,
            store_target_selection_task,
        )

        target = resolve_railway_provider_target(
            user_request=text,
            target_hints=list(params.get("target_hints") or []),
            operation_type=operation_type,
        )
        candidates = candidates_from_target_resolution(list(target.candidates or []))
        if candidates:
            store_target_selection_task(
                session_id=session_id,
                provider=str(params.get("provider") or "railway"),
                operation=operation_type,
                original_request=text,
                candidates=candidates,
                params=params,
            )
        return (clarification, "mutation_target_clarification", {"provider": str(params.get("provider") or "")})
    params = gated_params or params

    provider = str(params.get("provider") or "unknown")
    target_name = params.get("target_name")
    target = dict(params.get("target") or {})

    from aethos_core.deployment_targets.mutation_resolver import apply_target_resolution_to_params

    if operation_type in {"stop", "restart", "redeploy", "set_env_var", "remove_env_var", "deploy_from_git"}:
        params, resolution = apply_target_resolution_to_params(params, user_text=text)
        target_name = params.get("target_name")
        target = dict(params.get("target") or {})
        provider = str(params.get("provider") or provider)
        if resolution is not None and not resolution.resolved and resolution.detail:
            return (
                resolution.detail + "\n\nNo mutation preflight has been created yet.",
                "mutation_target_clarification",
                {"operation": operation_type, "provider": provider},
            )

    if provider == "railway" and target_name:
        from aethos_core.provider_topology.source_binding_resolver import refresh_params_source_binding

        params, _resolution, _regression = refresh_params_source_binding(params, session_id=session_id)
        target = dict(params.get("target") or {})

    if provider == "railway" and target_name and target.get("resolved"):
        from aethos_core.provider_topology.binding_verifier import compose_binding_mismatch_reply, verify_source_binding
        from aethos_core.provider_topology.operation_requirement_policy import requires_source_binding

        if requires_source_binding(provider, operation_type):
            binding = verify_source_binding(
                provider="railway",
                project=str(target.get("project_name") or ""),
                environment=str(target.get("environment") or "production"),
                service_name=str(target_name),
                user_text=text,
                operation_type=operation_type,
            )
            if not binding.ok:
                return (
                    compose_binding_mismatch_reply(binding),
                    "provider_binding_mismatch",
                    {
                        "provider": provider,
                        "target_name": str(target_name),
                        "stored_repo": str(binding.stored_github_repo or ""),
                        "referenced_repo": str(binding.referenced_github_repo or ""),
                    },
                )

    noop = _github_workflow_rerun_noop_reply(text, session_id=session_id, params=params)
    if noop is not None:
        return noop

    job = authority.create_job(
        title=_mutation_preflight_job_title(title, operation_type=operation_type),
        job_type=CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
        params={**params, "session_id": session_id},
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    from aethos_core.operational_thread_memory.mutation_thread_memory import sync_thread_from_preflight

    sync_thread_from_preflight(job=job, user_request=text)
    op = operation_type.replace("_", " ")
    settings_hint = ""
    from aethos_core.config import get_settings

    approval_path = mutation_approval_surface()
    if target_name and target.get("resolved"):
        project = target.get("project_name")
        environment = target.get("environment") or "production"
        path = f"**{project} / {environment} / {target_name}**" if project else f"**{target_name}**"
        body = (
            f"I found Railway target: {path}.\n\n"
            f"I created a governed {op} preflight `{job.id}` (**no {op} has been performed yet**).\n\n"
            f"Review it in **{approval_path}**, then approve if the blast radius and rollback plan look correct."
        )
        return (
            body,
            "mutation_preflight_job_created",
            {
                "proposed_job_id": job.id,
                "proposed_job_type": CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
                "operation_type": operation_type,
                "provider": provider,
                "target_name": str(target_name),
            },
        )

    if operation_type == "workflow_rerun" and provider == "github":
        body = (
            f"Created GitHub workflow rerun preflight `{job.id}` (**no rerun performed yet**).\n\n"
            f"Review target, blast radius, rollback plan, and correlation advisory in **{approval_path}**, "
            "then click **Approve Governed Mutation**."
        )
        return (
            body,
            "mutation_preflight_job_created",
            {
                "proposed_job_id": job.id,
                "proposed_job_type": CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
                "operation_type": operation_type,
                "provider": provider,
            },
        )

    if get_settings().mutation_execution_enabled:
        settings_hint = (
            "\n\nWhen the preflight completes, review **blast radius**, **rollback plan**, and **risk tier** "
            f"in **{approval_path}**, then click **Approve Governed Mutation**."
        )
    else:
        settings_hint = (
            "\n\nWhen the preflight completes, review **risk tier**, **rollback plan**, and **audit requirements** "
            f"in **{approval_path}**. Enable `MUTATION_EXECUTION_ENABLED=true` for governed real execution."
        )
    body = (
        f"Created mutation preflight job `{job.id}` (**no mutation performed yet**).\n\n"
        f"**Operation:** {op} · **Provider:** {provider}\n\n"
        f"{settings_hint.strip()}\n\n"
        "**Required steps:** approval · staged execution · verification · rollback acknowledgment · audit record."
    )
    return (
        body,
        "mutation_preflight_job_created",
        {
            "proposed_job_id": job.id,
            "proposed_job_type": CANONICAL_MUTATION_PREFLIGHT_JOB_TYPE,
            "operation_type": operation_type,
            "provider": provider,
        },
    )
