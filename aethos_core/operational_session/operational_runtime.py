# SPDX-License-Identifier: Apache-2.0
"""Unified operational runtime — shared by chat and CLI."""

from __future__ import annotations

from dataclasses import dataclass, field

from aethos_core.config import get_settings


@dataclass
class OperationalTurnResult:
    reply: str
    intent: str
    ok: bool = True
    meta: dict[str, str] = field(default_factory=dict)
    used_llm: bool = False


def run_operational_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "operational",
) -> OperationalTurnResult:
    """Single entry for operational conversations (kernel-first)."""
    raw = (text or "").strip()
    if not raw:
        return OperationalTurnResult(reply="", intent="empty", ok=False)

    settings = get_settings()
    if not settings.operational_conversation_kernel_enabled:
        return OperationalTurnResult(
            reply="Operational conversation kernel is disabled. Set OPERATIONAL_CONVERSATION_KERNEL_ENABLED=true.",
            intent="operational_kernel_disabled",
            ok=False,
            meta={"kernel_disabled": "true"},
        )

    from aethos_core.operational_session.kernel_router import route_operational_conversation_kernel_turn

    source_channel = "cli" if channel == "cli" else "operational"
    result = route_operational_conversation_kernel_turn(raw, session_id=session_id, channel=source_channel)
    if result is None:
        from aethos_core.operational_session.kernel_reality_registry import is_continuity_prompt
        from aethos_core.operational_session.operational_session import load_operational_session

        session = load_operational_session(session_id=session_id)
        if is_continuity_prompt(raw) and not session.has_active_subject():
            from aethos_core.cli.operator_cli import OPERATOR_DEFAULT_SESSION_ID

            sid = OPERATOR_DEFAULT_SESSION_ID
            reply = (
                "This follow-up needs prior context in the **same session**.\n\n"
                f"Use one `--session-id` for every turn (default: `{sid}`), for example:\n"
                f"1. `aethos message send --session-id {sid} \"show Railway projects\"`\n"
                f"2. `aethos operational --session-id {sid} \"what about api?\"`\n\n"
                "Or start with an explicit target: `top 5 logs for aethos-api on Railway`."
            )
        else:
            reply = (
                "This operational request did not match the kernel. "
                "Try `show Railway projects`, `show logs`, `validate vercel connection`, "
                "`deployment status`, or `continue`."
            )
        return OperationalTurnResult(
            reply=reply,
            intent="operational_kernel_no_match",
            ok=False,
            meta={"route_id": "operational_conversation_kernel", "kernel_no_match": "true"},
        )

    meta = {k: str(v) for k, v in (result.meta or {}).items()}
    meta["channel"] = channel
    kernel_ok = str(meta.get("kernel_ok", "true")).lower() not in {"false", "0", "no"}
    return OperationalTurnResult(
        reply=result.reply,
        intent=result.intent,
        ok=kernel_ok,
        meta=meta,
        used_llm=bool(result.used_llm),
    )
