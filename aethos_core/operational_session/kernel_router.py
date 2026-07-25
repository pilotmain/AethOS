# SPDX-License-Identifier: Apache-2.0
"""Chat entry point for OPERATIONAL_CONVERSATION_KERNEL_001."""

from __future__ import annotations

from aethos_core.chat.service import ChatTurnResult
from aethos_core.config import get_settings
from aethos_core.observability.kernel_observability import KernelTurnObservation, record_kernel_turn
from aethos_core.operational_session.operational_readonly_goal import is_operational_kernel_candidate
from aethos_core.operational_session.operational_tool_loop import run_operational_tool_loop


def should_route_operational_conversation_kernel(text: str, *, session_id: str = "default") -> bool:
    settings = get_settings()
    if not settings.operational_conversation_kernel_enabled:
        return False
    return is_operational_kernel_candidate(text, session_id=session_id)


def route_operational_conversation_kernel_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> ChatTurnResult | None:
    if not should_route_operational_conversation_kernel(text, session_id=session_id):
        return None

    loop = run_operational_tool_loop(text, session_id=session_id)
    if loop is None:
        record_kernel_turn(
            KernelTurnObservation(
                ok=False,
                intent="operational_kernel_no_match",
                subject_resolved=False,
                tool_failed=True,
            )
        )
        from aethos_core.operational_session.kernel_reality_registry import capture_kernel_reality_turn

        capture_kernel_reality_turn(
            request=text,
            session_id=session_id,
            source="cli" if channel == "cli" else ("operational" if channel == "operational" else "chat"),
            ok=False,
            intent="operational_kernel_no_match",
            meta={"kernel_no_match": "true", "channel": channel},
        )
        return None

    meta = dict(loop.meta or {})
    meta["operational_kernel"] = "true"
    meta["kernel_ok"] = "true" if loop.ok else "false"
    meta["channel"] = channel
    record_kernel_turn(
        KernelTurnObservation(
            ok=loop.ok,
            intent=loop.intent,
            used_recovery=meta.get("recovery_applied") == "true",
            used_fallback=meta.get("kernel_fallback") == "true",
            subject_resolved=bool(loop.subject.provider or loop.subject.vercel_project or loop.subject.project),
            tool_failed=not loop.ok,
            plan_resume=loop.intent.endswith("continue") or meta.get("goal_kind") == "continue_plan",
            meta=meta,
        )
    )
    from aethos_core.operational_session.kernel_reality_registry import capture_kernel_reality_turn

    capture_kernel_reality_turn(
        request=text,
        session_id=session_id,
        source="cli" if channel == "cli" else ("operational" if channel == "operational" else "chat"),
        ok=loop.ok,
        intent=loop.intent,
        meta=meta,
        subject=loop.subject,
    )
    return ChatTurnResult(
        reply=loop.reply,
        intent=loop.intent,
        provider_stream=False,
        used_llm=meta.get("brain_used_llm") == "true",
        meta=meta,
    )
