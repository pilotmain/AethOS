# SPDX-License-Identifier: Apache-2.0
"""Deterministic replies for operational thread follow-ups."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.mission_control.visible_navigation_registry import resolve_visible_navigation_path, INTERNAL_SURFACE_MUTATION_APPROVAL

# Introspective platform questions that belong to the agent tool loop (email, multi-agent
# status), NOT the operational mutation-thread follow-up lane. Without this guard a verb
# like "check" makes them look like a vague thread follow-up and they dead-end.
_AGENT_INTROSPECTION_RX = re.compile(
    r"\b(e-?mails?|inbox(?:es)?|mailbox(?:es)?)\b"
    r"|\b(?:multi[-\s]?agent|agents?)\b[^.\n]{0,30}\b(?:status|doing|progress|working)\b"
    r"|\b(?:status|progress)\b[^.\n]{0,20}\b(?:multi[-\s]?agent|agents?)\b",
    re.I,
)
from aethos_core.operational_thread_memory.failure_reason_extractor import extract_failure_reason
from aethos_core.operational_thread_memory.followup_resolver import is_vague_operational_followup, resolve_followup_intent
from aethos_core.operational_thread_memory.mutation_thread_memory import find_execution_job_for_service, sync_thread_from_execution_job
from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired


def _active_thread_conflicts_with_request(text: str, *, session_id: str) -> bool:
    """Do not hijack Vercel/killit requests with a stale Railway greenfield thread."""
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import (
        request_overrides_stale_operational_thread,
    )

    return request_overrides_stale_operational_thread(text, session_id=session_id)


def compose_operational_thread_followup(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.task_frame.confirmation_continuation import is_action_confirmation
    from aethos_core.task_frame.pending_action import get_pending_action

    if is_action_confirmation(text) and get_pending_action(session_id=session_id) is not None:
        return None

    # Email / multi-agent-status asks go to the agent tool loop, not the mutation-thread lane.
    if _AGENT_INTROSPECTION_RX.search(text or ""):
        return None

    from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question

    if is_runtime_provider_config_question(text):
        return None

    from aethos_core.provider_readonly_intent.readonly_intent_classifier import should_yield_active_thread_for_readonly

    if should_yield_active_thread_for_readonly(text):
        return None

    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        should_yield_active_thread_for_workflow_discovery,
    )

    if should_yield_active_thread_for_workflow_discovery(text, session_id=session_id):
        return None

    from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request

    if is_provider_followup_request(text, session_id=session_id):
        return None

    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(text):
        return None

    from aethos_core.task_frame.retry_active_operation import is_retry_intent

    if is_retry_intent(text, session_id=session_id):
        return None

    if not is_vague_operational_followup(text):
        return None

    if _active_thread_conflicts_with_request(text, session_id=session_id):
        return None

    from aethos_core.provider_topology.source_binding_correction import should_handle_binding_correction

    if should_handle_binding_correction(text, session_id=session_id):
        return None

    intent = resolve_followup_intent(text)
    kind = intent.get("kind")
    thread = get_active_thread(session_id=session_id)

    if kind == "why_service_failed":
        service_phrase = str(intent.get("service_phrase") or "")
        job = find_execution_job_for_service(session_id=session_id, service_phrase=service_phrase)
        if job:
            thread = sync_thread_from_execution_job(job=job)
        elif thread is None:
            return _stale_reply(session_id)
        return _why_service_failed_reply(thread, service_phrase, session_id=session_id, job=job)

    if thread is None:
        job = _latest_execution_job(session_id)
        if job is not None:
            failure = extract_failure_reason(job)
            if failure or kind in {"thread_recall", "check_and_report", "status_check", "did_it_work"}:
                thread = sync_thread_from_execution_job(job=job)
        if thread is None:
            from aethos_core.aethos_identity.continuity_decision import compose_continuity_operational_reply

            continuity = compose_continuity_operational_reply(text, session_id=session_id)
            if continuity is not None:
                return continuity
            if kind in {"thread_recall", "check_and_report", "status_check"}:
                return _stale_reply(session_id)
            return None
    if is_thread_expired(thread):
        return _stale_reply(session_id)

    if kind == "thread_recall":
        return _thread_recall_reply(thread)
    if kind == "why_failed":
        return _why_failed_reply(thread, session_id=session_id)
    if kind == "did_it_work":
        return _did_it_work_reply(thread, session_id=session_id)
    if kind in {"check_and_report", "status_check"}:
        return _check_and_report_reply(thread, session_id=session_id)

    return _check_and_report_reply(thread, session_id=session_id)


def _runtime_path() -> str:
    return resolve_visible_navigation_path(internal_surface=INTERNAL_SURFACE_MUTATION_APPROVAL, mode="operator")


def _latest_execution_job(session_id: str):
    from aethos_core.runtime.jobs import job_store

    for row in reversed(job_store.list_all()):
        if row.job_type != "mutation_execution":
            continue
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        return row
    return None


def _refresh_thread(thread, *, session_id: str):
    job = None
    if thread.execution_job_id:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(thread.execution_job_id)
    if job is None:
        job = _latest_execution_job(session_id)
    if job is not None:
        return sync_thread_from_execution_job(job=job)
    return thread


def _check_and_report_reply(thread, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    if thread.active_thread == "railway_greenfield_deployment":
        from aethos_core.operational_thread_memory.solo_greenfield_thread_memory import (
            compose_greenfield_deployment_status_reply,
        )

        return compose_greenfield_deployment_status_reply(thread=thread)

    thread = _refresh_thread(thread, session_id=session_id)
    path = thread.service_path()
    op = str(thread.operation or "mutation").replace("_", " ")
    job_id = thread.execution_job_id or "unknown"
    failure = thread.failure_reason or {}
    lines = [
        f"Yes — I'll check the latest Railway **{op}** thread for **{path}**.",
        "",
        "Current state:",
        f"- Operation: {op}",
        f"- Service: {path}",
        f"- Execution job: `{job_id}`",
        f"- Result: **{thread.status}**",
    ]
    if failure.get("failure_reason"):
        lines.extend(
            [
                "",
                "Failure reason:",
                f"- {failure.get('failure_reason')}",
                f"- Stage: {failure.get('failure_stage')}",
            ]
        )
    lines.extend(
        [
            "",
            "Next check:",
            thread.next_check or "Collect Railway restart evidence, recent logs, and service health.",
            "",
            f"Review full evidence in **{_runtime_path()}**.",
        ]
    )
    return (
        "\n".join(lines),
        "operational_thread_followup",
        {"execution_job_id": str(job_id), "status": thread.status, "provider": thread.provider},
    )


def _thread_recall_reply(thread) -> tuple[str, str, dict[str, str]]:
    path = thread.service_path()
    op = str(thread.operation or "mutation").replace("_", " ")
    body = (
        f"We were working on a governed Railway **{op}** for **{path}**.\n\n"
        f"Latest result: **{thread.status}** — {thread.last_system_result or 'execution updated'}.\n\n"
    )
    if thread.status in {"restart_unverified", "service_online_but_restart_unproven", "execution_failed"}:
        body += "The restart execution was attempted, but AethOS could not verify provider-side restart evidence yet."
    elif thread.execution_job_id:
        body += f"Execution job: `{thread.execution_job_id}`."
    return (body, "operational_thread_recall", {"execution_job_id": str(thread.execution_job_id or "")})


def _why_failed_reply(thread, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    thread = _refresh_thread(thread, session_id=session_id)
    return _failure_reply(thread)


def _why_service_failed_reply(thread, service_phrase: str, *, session_id: str, job) -> tuple[str, str, dict[str, str]]:
    if job is None:
        thread = _refresh_thread(thread, session_id=session_id)
    else:
        thread = sync_thread_from_execution_job(job=job)
    path = thread.service_path()
    body_lines = [f"The **{service_phrase}** restart execution failed." if thread.status == "execution_failed" else f"The **{service_phrase}** operation did not complete as expected."]
    failure = thread.failure_reason or extract_failure_reason(job) if job else thread.failure_reason
    if failure:
        body_lines.extend(
            [
                "",
                "Reason:",
                str(failure.get("failure_reason") or "Unknown provider failure."),
                "",
                f"Stage: `{failure.get('failure_stage')}`",
                "",
                "Next recommended action:",
                str(failure.get("next_recommended_action") or thread.next_check or "Review Railway logs."),
            ]
        )
    else:
        body_lines.append(f"\nCurrent status: **{thread.status}**. No restart was confirmed. I can check Railway logs and provider diagnostics next.")
    if job:
        body_lines.append(f"\nExecution job: `{job.id}`.")
    return (
        "\n".join(body_lines),
        "operational_thread_why_failed",
        {"service": service_phrase, "execution_job_id": str(thread.execution_job_id or "")},
    )


def _failure_reply(thread) -> tuple[str, str, dict[str, str]]:
    failure = thread.failure_reason or {}
    job = None
    if thread.execution_job_id:
        from aethos_core.runtime.jobs import job_store

        job = job_store.get(thread.execution_job_id)
    if job is not None:
        from aethos_core.provider_topology.failure_truth_expander import compose_expanded_failure_reply, expand_failure_truth

        truth = job.params.get("failure_truth") or expand_failure_truth(job)
        if truth:
            return (
                compose_expanded_failure_reply(truth),
                "operational_thread_why_failed",
                {"execution_job_id": str(thread.execution_job_id or ""), "failure_stage": str(truth.get("failure_stage") or "")},
            )

    path = thread.service_path()
    if not failure.get("failure_reason"):
        return (
            f"I checked the latest Railway thread for **{path}**, but no structured failure reason is stored yet.\n\n"
            f"Current status: **{thread.status}**.\n\n"
            f"Execution job: `{thread.execution_job_id or 'unknown'}`.",
            "operational_thread_why_failed",
            {"execution_job_id": str(thread.execution_job_id or "")},
        )
    return (
        f"The latest Railway **{thread.operation or 'mutation'}** for **{path}** did not succeed.\n\n"
        f"Reason:\n{failure.get('failure_reason')}\n\n"
        f"Stage: `{failure.get('failure_stage')}`\n\n"
        f"Next recommended action:\n{failure.get('next_recommended_action')}",
        "operational_thread_why_failed",
        {"execution_job_id": str(thread.execution_job_id or ""), "failure_stage": str(failure.get("failure_stage") or "")},
    )


def _did_it_work_reply(thread, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    thread = _refresh_thread(thread, session_id=session_id)
    path = thread.service_path()
    if thread.status in {"restart_transition_detected", "log_restart_detected", "verified"}:
        return (
            f"Yes — provider evidence indicates the Railway **{thread.operation or 'mutation'}** for **{path}** verified successfully.",
            "operational_thread_followup",
            {"verified": "true", "execution_job_id": str(thread.execution_job_id or "")},
        )
    if thread.status in {"restart_unverified", "service_online_but_restart_unproven"}:
        return (
            f"No — I cannot confirm the Railway restart for **{path}** worked. The service may be online, but restart evidence is missing.",
            "operational_thread_followup",
            {"verified": "false", "execution_job_id": str(thread.execution_job_id or "")},
        )
    if thread.failure_reason:
        return _failure_reply(thread)
    return _check_and_report_reply(thread, session_id=session_id)


def _stale_reply(session_id: str) -> tuple[str, str, dict[str, str]]:
    return (
        "I don't have an active operational mutation thread in this session anymore.\n\n"
        "The previous thread may have expired or no governed execution job was recorded yet.\n\n"
        "Start a new governed operation (for example: **Restart the Railway worker service**) or reference a job ID directly.",
        "operational_thread_stale",
        {"session_id": session_id},
    )
