# SPDX-License-Identifier: Apache-2.0
"""Actionable operational follow-up — delegates to provider-generic conversation memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FollowupAction:
    action_type: str
    user_text: str = ""
    log_limit: int = 5
    log_filter: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "user_text": self.user_text,
            "log_limit": self.log_limit,
            "log_filter": self.log_filter,
        }


@dataclass
class FollowupActionResult:
    action_type: str
    thread_path: str
    execution_job_id: str = ""
    status: str = ""
    conclusion: str = ""
    log_evidence: dict[str, Any] = field(default_factory=dict)
    watch_created: bool = False
    body: str = ""
    meta: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_type": self.action_type,
            "thread_path": self.thread_path,
            "execution_job_id": self.execution_job_id,
            "status": self.status,
            "conclusion": self.conclusion,
            "log_evidence": dict(self.log_evidence),
            "watch_created": self.watch_created,
            "body": self.body,
            "meta": dict(self.meta),
        }


_INTENT_TO_LEGACY_ACTION = {
    "verify_operation": "check_logs",
    "fetch_logs": "check_logs",
    "fetch_top_n_logs": "check_logs",
    "fetch_latest_logs": "get_latest_log_timestamp",
    "get_status": "check_status",
    "watch_until_done": "create_completion_watch",
    "explain_failure": "explain_failure",
    "retry_operation": "retry_operation",
    "reconcile_source_binding": "reconcile_source_binding",
    "what_changed": "thread_recall",
}


def is_actionable_operational_followup(text: str, *, session_id: str = "default") -> bool:
    from aethos_core.conversation.provider_memory.conversational_memory_router import is_provider_followup_request

    return is_provider_followup_request(text, session_id=session_id)


def classify_followup_action(text: str, active_thread: Any) -> FollowupAction | None:
    from aethos_core.conversation.provider_memory.followup_intent_classifier import classify_followup_intent

    intent = classify_followup_intent(text, active_thread)
    if intent is None:
        return None
    action_type = _INTENT_TO_LEGACY_ACTION.get(intent.intent, intent.intent)
    return FollowupAction(
        action_type=action_type,
        user_text=intent.user_text,
        log_limit=intent.log_limit,
        log_filter=intent.log_filter,
    )


def execute_followup_action(
    action: FollowupAction,
    thread: Any,
    *,
    session_id: str = "default",
) -> FollowupActionResult:
    from aethos_core.conversation.provider_memory.provider_followup_runtime import handle_provider_followup

    result = handle_provider_followup(session_id=session_id, user_text=action.user_text)
    if result is None:
        return FollowupActionResult(
            action_type=action.action_type,
            thread_path=thread.service_path(),
            execution_job_id=str(getattr(thread, "execution_job_id", "") or "unknown"),
            body="",
        )
    return FollowupActionResult(
        action_type=action.action_type,
        thread_path=result.thread_path,
        execution_job_id=result.execution_job_id,
        status=result.evidence.get("status_label", "") if isinstance(result.evidence, dict) else "",
        conclusion=result.conclusion,
        log_evidence=dict(result.evidence),
        watch_created=result.watch_created,
        body=result.body,
        meta=dict(result.meta),
    )


def compose_followup_result(result: FollowupActionResult) -> tuple[str, str, dict[str, str]]:
    intent = result.meta.get("intent") or f"actionable_{result.action_type}"
    meta = {k: str(v) for k, v in result.meta.items() if k != "intent"}
    meta.setdefault("execution_job_id", result.execution_job_id)
    meta.setdefault("action_type", result.action_type)
    if result.conclusion:
        meta.setdefault("conclusion", result.conclusion)
    return result.body, intent, meta


def compose_actionable_followup_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.conversation.provider_memory.conversational_memory_router import compose_provider_followup_reply

    return compose_provider_followup_reply(text, session_id=session_id)
