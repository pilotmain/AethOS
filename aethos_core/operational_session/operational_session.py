# SPDX-License-Identifier: Apache-2.0
"""Canonical operational session — subject + context for multi-turn ops."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from aethos_core.operational_session.session_context import SessionContext, SessionTurn
from aethos_core.operational_session.session_store import (
    clear_operational_sessions_for_tests,
    load_context,
    load_session_payload,
    load_subject,
    save_session_payload,
)
from aethos_core.operational_session.session_subject import SessionSubject


@dataclass
class OperationalSession:
    session_id: str
    subject: SessionSubject
    context: SessionContext

    def has_active_subject(self) -> bool:
        return bool(self.subject.provider or self.subject.vercel_project or self.subject.project or self.subject.alias)


def load_operational_session(*, session_id: str = "default") -> OperationalSession:
    sid = (session_id or "default").strip() or "default"
    payload = load_session_payload(session_id=sid)
    return OperationalSession(
        session_id=sid,
        subject=SessionSubject.from_dict(payload.get("subject")),
        context=SessionContext.from_dict(payload.get("context")),
    )


def save_operational_session(session: OperationalSession) -> None:
    save_session_payload(
        session_id=session.session_id,
        payload={
            "subject": session.subject.to_dict(),
            "context": session.context.to_dict(),
        },
    )


def record_operational_turn(
    *,
    session_id: str,
    user_text: str,
    subject: SessionSubject,
    operation: str,
    reply_intent: str,
    result_summary: str = "",
    log_limit: int | None = None,
    tool_id: str = "",
    deployment_id: str = "",
) -> OperationalSession:
    session = load_operational_session(session_id=session_id)
    session.subject = subject
    session.context.last_operation = operation
    session.context.last_result_summary = result_summary[:400]
    session.context.last_tool_id = tool_id
    session.context.last_provider = str(subject.provider or "").strip().lower()
    session.context.last_subject_label = subject.path_label()[:240]
    if deployment_id:
        session.context.last_deployment_id = deployment_id
    if log_limit is not None:
        session.context.last_log_limit = log_limit
    session.context.turns.append(
        SessionTurn(
            user_text=(user_text or "")[:500],
            operation=operation,
            reply_intent=reply_intent,
            recorded_at=datetime.now(UTC).isoformat(),
        )
    )
    save_operational_session(session)
    try:
        from aethos_core.autonomous_execution.runtime_state import register_operator_session

        register_operator_session(
            session_id=session_id,
            last_provider=session.context.last_provider,
            last_subject_label=session.context.last_subject_label,
            last_operation=operation,
        )
    except Exception:
        pass
    return session


def operational_session_meta(*, session_id: str = "default") -> dict[str, object]:
    """Operator-facing session meta — last provider, subject, and continue hints."""
    session = load_operational_session(session_id=session_id)
    subject = session.subject
    ctx = session.context
    return {
        "session_id": session.session_id,
        "has_active_subject": session.has_active_subject(),
        "last_provider": ctx.last_provider or str(subject.provider or "").strip().lower(),
        "last_subject_label": ctx.last_subject_label or subject.path_label(),
        "last_operation": ctx.last_operation,
        "continue_hint": (
            f"Continue on {ctx.last_provider or subject.provider} — {ctx.last_subject_label or subject.path_label()}"
            if session.has_active_subject() and (ctx.last_subject_label or subject.path_label())
            else ""
        ),
    }


__all__ = [
    "OperationalSession",
    "clear_operational_sessions_for_tests",
    "load_context",
    "load_operational_session",
    "load_subject",
    "operational_session_meta",
    "record_operational_turn",
    "save_operational_session",
]
