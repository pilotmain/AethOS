# SPDX-License-Identifier: Apache-2.0
"""Operational follow-up continuity lock — prevent provider drift."""

from __future__ import annotations

import re
from typing import Any

_THREAD_CONTINUATION_RX = re.compile(
    r"\b("
    r"what\s+do\s+you\s+need\s+from\s+me"
    r"|what\s+do\s+i\s+need\s+to\s+do"
    r"|what\s+should\s+i\s+do"
    r"|how\s+can\s+i\s+help"
    r"|what\s+do\s+you\s+need\s+(?:for|to)"
    r"|what\s+is\s+blocking"
    r"|what\s+is\s+still\s+missing"
    r"|fix\s+the\s+repo\s+binding"
    r"|update\s+the\s+repo\s+binding"
    r"|retry\s+the\s+(?:restart|redeploy|mutation)"
    r")\b",
    re.I,
)
_EXPLICIT_PROVIDER_SWITCH_RX = re.compile(
    r"\b(?:switch\s+to|use|on)\s+(?:vercel|railway|github|docker|kubernetes)\b|"
    r"\b(?:vercel|railway|github)\s+(?:restart|redeploy|deploy)\b",
    re.I,
)


def is_thread_continuation_followup(text: str) -> bool:
    return bool(_THREAD_CONTINUATION_RX.search(text or ""))


def has_explicit_provider_switch(text: str) -> bool:
    from aethos_core.provider_readonly_intent.readonly_intent_classifier import should_yield_active_thread_for_readonly

    if should_yield_active_thread_for_readonly(text):
        return True
    return bool(_EXPLICIT_PROVIDER_SWITCH_RX.search(text or ""))


def get_locked_thread_context(*, session_id: str):
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired

    thread = get_active_thread(session_id=session_id)
    if thread is None or is_thread_expired(thread):
        return None
    if thread.status in {"completed", "cancelled", "superseded"}:
        return None
    return thread


def should_block_unrelated_preflight(text: str, *, session_id: str) -> bool:
    from aethos_core.chat.explicit_mutation_intent import detect_explicit_mutation_intent
    from aethos_core.repair_memory.repair_outcome_router import is_repair_outcome_question

    if is_repair_outcome_question(text):
        return False

    intent = detect_explicit_mutation_intent(text, session_id=session_id)
    if intent is not None and intent.confidence >= 0.75:
        return False

    thread = get_locked_thread_context(session_id=session_id)
    if thread is None:
        return False
    if has_explicit_provider_switch(text):
        return False
    return True


def infer_locked_provider_operation(text: str, *, session_id: str) -> dict[str, Any] | None:
    thread = get_locked_thread_context(session_id=session_id)
    if thread is None:
        return None
    return {
        "provider": thread.provider,
        "project": thread.project,
        "environment": thread.environment,
        "service": thread.service,
        "operation": thread.operation,
        "status": thread.status,
        "execution_job_id": thread.execution_job_id,
    }


def compose_thread_continuation_reply(text: str, *, session_id: str = "default") -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_followup_router import (
        should_yield_active_thread_for_workflow_discovery,
    )

    if should_yield_active_thread_for_workflow_discovery(text, session_id=session_id):
        return None

    from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request

    if is_provider_followup_request(text, session_id=session_id):
        return None

    if not is_thread_continuation_followup(text) and not should_block_unrelated_preflight(text, session_id=session_id):
        return None

    thread = get_locked_thread_context(session_id=session_id)
    if thread is None:
        return None

    if not is_thread_continuation_followup(text):
        return None

    from aethos_core.provider_topology.binding_verifier import compose_binding_mismatch_reply, verify_source_binding
    from aethos_core.provider_topology.repair_loop import compose_repair_proposal

    path = thread.service_path()
    op = str(thread.operation or "mutation").replace("_", " ")
    binding = verify_source_binding(
        provider=thread.provider,
        project=str(thread.project or ""),
        environment=str(thread.environment or "production"),
        service_name=str(thread.service or ""),
        user_text=text,
        operation_type=str(thread.operation or "restart"),
    )

    if "fix" in (text or "").lower() and "binding" in (text or "").lower():
        repair = compose_repair_proposal(
            provider=thread.provider,
            project=str(thread.project or ""),
            environment=str(thread.environment or "production"),
            service_name=str(thread.service or ""),
            user_text=text,
            failure_reason=(thread.failure_reason or {}).get("failure_reason") if thread.failure_reason else None,
            operation_type=str(thread.operation or "restart"),
        )
        return (repair["reply"], "provider_repair_proposal", repair.get("meta", {}))

    if not binding.ok:
        body = (
            f"I need confirmation of the correct source binding before executing the Railway **{op}**.\n\n"
            + compose_binding_mismatch_reply(binding)
        )
        return (
            body,
            "operational_thread_continuation",
            {
                "provider": thread.provider,
                "service": str(thread.service or ""),
                "stored_repo": str(binding.stored_github_repo or ""),
                "referenced_repo": str(binding.referenced_github_repo or ""),
            },
        )

    failure = thread.failure_reason or {}
    if failure.get("failure_reason"):
        body = (
            f"To complete the Railway **{op}** for **{path}**, I still need governed execution to succeed.\n\n"
            f"Last failure: {failure.get('failure_reason')}\n\n"
            f"Next recommended action: {failure.get('next_recommended_action') or thread.next_check or 'Review execution evidence.'}"
        )
    else:
        body = (
            f"I'm continuing the active Railway **{op}** thread for **{path}**.\n\n"
            f"Current status: **{thread.status}**.\n\n"
            "If source binding is confirmed, approve the governed preflight in Mission Control or ask me to refresh provider topology."
        )
    return (
        body,
        "operational_thread_continuation",
        {"provider": thread.provider, "service": str(thread.service or ""), "status": thread.status},
    )
