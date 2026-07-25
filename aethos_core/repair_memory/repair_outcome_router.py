# SPDX-License-Identifier: Apache-2.0
"""Repair outcome question routing — owns direct post-mutation outcome queries."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.chat.service import ChatTurnResult
from aethos_core.repair_memory.repair_attempt_memory import RepairAttemptOutcome, list_repair_attempts, lookup_latest_for_service, lookup_latest_for_target

_REPAIR_OUTCOME_RX = re.compile(
    r"\b("
    r"did\s+restart\s+help"
    r"|did\s+(?:the\s+)?restart\s+help"
    r"|did\s+it\s+help"
    r"|did\s+that\s+fix\s+it"
    r"|did\s+restart\s+fix\s+it"
    r"|was\s+restart\s+useful"
    r"|did\s+recovery\s+improve"
    r"|is\s+it\s+better\s+after\s+(?:the\s+)?restart"
    r")\b",
    re.I,
)

_SERVICE_RX = re.compile(
    r"\b(mongodb|mongo|postgres(?:ql)?|redis|worker|api|backend|frontend|[a-z0-9][\w-]+)\b",
    re.I,
)


def is_repair_outcome_question(text: str) -> bool:
    return bool(_REPAIR_OUTCOME_RX.search(text or ""))


def repair_outcome_preemption_blocks_route(text: str, *, session_id: str = "default") -> bool:
    """True when downstream routes must defer to repair outcome routing."""
    return is_repair_outcome_question(text)


def find_latest_repair_outcome_for_context(
    text: str,
    *,
    session_id: str = "default",
) -> RepairAttemptOutcome | None:
    service = _service_from_text(text)
    target = _target_from_active_thread(session_id=session_id)

    if service:
        outcome = lookup_latest_for_target(_target_label(service, target)) or lookup_latest_for_service(service)
        if outcome is not None:
            return outcome

    if target:
        outcome = lookup_latest_for_target(target)
        if outcome is not None:
            return outcome
        service_name = target.split("/")[-1].strip()
        if service_name:
            outcome = lookup_latest_for_service(service_name)
            if outcome is not None:
                return outcome

    for row in list_repair_attempts(limit=30):
        if row.session_id == session_id:
            return row

    rows = list_repair_attempts(limit=1)
    return rows[0] if rows else None


def compose_repair_outcome_reply(outcome: RepairAttemptOutcome | None) -> str:
    if outcome is None:
        return (
            "I do not have a recorded repair outcome for that question yet.\n\n"
            "Run post-mutation verification first (for example: **verify health** or **did it recover?**) "
            "so I can record whether the latest mutation helped."
        )

    service = outcome.service or outcome.target.split("/")[-1].strip() or "the service"
    if outcome.helped:
        return "\n".join(
            [
                f"Yes — the **{outcome.operation.replace('_', ' ')}** appears to have helped **{service}**.",
                "",
                f"Latest verification for **{service}** shows:",
                f"- operation: **{outcome.operation.replace('_', ' ')}**",
                f"- result: **{outcome.result.replace('_', ' ')}**",
                f"- health after: **{outcome.health_after}**",
                f"- lesson: {outcome.lesson}",
            ]
        )

    return "\n".join(
        [
            "No — the restart did not appear to help.",
            "",
            f"Latest verification for **{service}** shows:",
            f"- operation: **{outcome.operation.replace('_', ' ')}**",
            f"- result: **{outcome.result.replace('_', ' ')}**",
            f"- health after: **{outcome.health_after}**",
            f"- lesson: {outcome.lesson}",
            "",
            "I would avoid another restart until we identify the root cause.",
        ]
    )


def compose_repair_outcome_route_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_repair_outcome_question(text):
        return None
    outcome = find_latest_repair_outcome_for_context(text, session_id=session_id)
    reply = compose_repair_outcome_reply(outcome)
    meta = {
        "route_id": "repair_outcome",
        "matched_module": "repair_memory.repair_outcome_router",
        "repair_outcome_question": "true",
    }
    if outcome is not None:
        meta["repair_helped"] = "true" if outcome.helped else "false"
        meta["repair_result"] = outcome.result
        meta["matched_target"] = outcome.target
        if outcome.service:
            meta["service"] = outcome.service
    else:
        meta["repair_outcome_available"] = "false"
    intent = "repair_outcome_helped" if outcome and outcome.helped else "repair_outcome_not_helped"
    if outcome is None:
        intent = "repair_outcome_unavailable"
    return reply, intent, meta


def route_repair_outcome_question(
    text: str,
    *,
    session_id: str = "default",
) -> ChatTurnResult | None:
    routed = compose_repair_outcome_route_reply(text, session_id=session_id)
    if routed is None:
        return None
    reply, intent, meta = routed
    return ChatTurnResult(
        reply=reply,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )


def _service_from_text(text: str) -> str:
    from aethos_core.failed_service_investigation.global_preemption import detect_failed_service_reference

    ref = detect_failed_service_reference(text, session_id="default")
    if ref and ref.rows:
        return str(ref.rows[0].get("service") or "")

    match = _SERVICE_RX.search(text or "")
    if match:
        candidate = match.group(1)
        if candidate.lower() not in {"did", "restart", "help", "that", "fix", "it", "was", "useful", "after", "the"}:
            return candidate
    return ""


def _target_from_active_thread(*, session_id: str) -> str:
    try:
        from aethos_core.conversation.provider_memory.provider_followup_runtime import get_active_operational_thread

        thread = get_active_operational_thread(session_id)
        if thread is None:
            return ""
        return thread.service_path()
    except Exception:
        return ""


def _target_label(service: str, thread_target: str) -> str:
    if " / " in thread_target:
        return thread_target
    if thread_target and service.lower() in thread_target.lower():
        return thread_target
    return service
