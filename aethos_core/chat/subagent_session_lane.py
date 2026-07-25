# SPDX-License-Identifier: Apache-2.0
"""Chat fast path for persisted agent sessions (spawn / send / list)."""

from __future__ import annotations

import re
from typing import Any

_SPAWN_RX = re.compile(r"\bagent_spawn\b|\bsave\s+session_key\b", re.I)
_SEND_RX = re.compile(r"\bagent_send\b", re.I)
_LIST_RX = re.compile(r"\bagent_sessions_list\b", re.I)


def is_subagent_spawn_request(text: str) -> bool:
    return bool(_SPAWN_RX.search((text or "").strip()))


def is_subagent_send_request(text: str) -> bool:
    return bool(_SEND_RX.search((text or "").strip()))


def is_subagent_list_request(text: str) -> bool:
    return bool(_LIST_RX.search((text or "").strip()))


def subagent_session_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    """Handle agent_spawn, agent_send, and agent_sessions_list before generic multi-agent lane."""
    raw = (text or "").strip()
    if not raw:
        return None

    if is_subagent_list_request(raw):
        return _list_reply(session_id)

    if is_subagent_send_request(raw):
        return _send_reply(raw, session_id=session_id)

    if is_subagent_spawn_request(raw):
        return _spawn_reply(raw, session_id=session_id)

    return None


def _extract_spawn_goal(text: str) -> str:
    goal = text.strip()
    goal = re.sub(r"^\s*agent_spawn\s*[:—\-]?\s*", "", goal, flags=re.I)
    goal = re.sub(r"\bsave\s+session_key\b", "", goal, flags=re.I)
    goal = re.sub(r"[—\-]\s*$", "", goal).strip()
    return goal or text.strip()


def _extract_send_message(text: str) -> str:
    match = re.search(
        r"agent_send\s+(?:to\s+(?:that\s+)?session\s*[:\-—]?\s*)?(.*)",
        text.strip(),
        flags=re.I | re.S,
    )
    if match:
        msg = match.group(1).strip()
        if msg:
            return msg
    return text.strip()


def _extract_session_key(text: str) -> str | None:
    match = re.search(r"(agent:[^\s]+:subagent:[^\s]+)", text)
    if match:
        return match.group(1)
    return None


def _spawn_reply(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.agents.runtime.subagent_ops import spawn_subagent_coordination
    from aethos_core.local_workspace.session_context import resolve_operational_hint

    goal = _extract_spawn_goal(text)
    hint = resolve_operational_hint(None, session_id=session_id)
    outcome = spawn_subagent_coordination(goal=goal, session_id=session_id, workspace_hint=hint)

    if not outcome.get("ok"):
        body = (
            f"Could not start agent session: {outcome.get('error') or 'coordination_failed'}.\n\n"
            f"{outcome.get('hint') or 'Try a clearer goal (one sentence).'}"
        )
        return body, "subagent_spawn_failed", _meta("spawn_failed", session_id, outcome)

    session_key = str(outcome.get("session_key") or "")
    excerpt = str(outcome.get("report_excerpt") or "").strip()
    body = (
        f"## Agent session started\n\n"
        f"**session_key:** `{session_key}`\n\n"
        f"Use **agent_send** with this key for follow-ups, or open **Mission Control → Orchestration**.\n\n"
    )
    if excerpt:
        body += f"{excerpt}\n"
    else:
        body += "_Coordination complete — see Mission Control for the agent pipeline._\n"

    meta = _meta("subagent_spawn", session_id, outcome)
    meta["session_key"] = session_key
    meta["spawn_id"] = str(outcome.get("spawn_id") or "")
    meta["plan_id"] = str(outcome.get("plan_id") or "")
    return body, "subagent_spawn", meta


def _send_reply(text: str, *, session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.agents.runtime.subagent_ops import send_subagent_message
    from aethos_core.agents.runtime.subagent_session_store import list_subagent_sessions

    message = _extract_send_message(text)
    session_key = _extract_session_key(text)
    spawn_id = None

    if not session_key:
        rows = list_subagent_sessions(parent_session_id=session_id, limit=1)
        if rows:
            session_key = str(rows[0].get("session_key") or "")
        else:
            body = (
                "**No agent sessions yet** for this chat.\n\n"
                "Start one with **agent_spawn** and a goal, e.g. "
                "`agent_spawn analyze Vercel deployment failures — save session_key`"
            )
            return body, "subagent_send_missing", _meta("send_missing", session_id, {})

    outcome = send_subagent_message(
        message=message,
        session_id=session_id,
        session_key=session_key,
        spawn_id=spawn_id,
    )
    if not outcome.get("ok"):
        err = outcome.get("error") or "send_failed"
        body = (
            f"Could not send follow-up ({err}).\n\n"
            f"{outcome.get('hint') or 'Spawn a session first or paste a valid session_key.'}"
        )
        return body, "subagent_send_failed", _meta("send_failed", session_id, outcome)

    key = str(outcome.get("session_key") or session_key or "")
    excerpt = str(outcome.get("report_excerpt") or "").strip()
    body = (
        f"## Follow-up sent\n\n"
        f"**session_key:** `{key}` · run **{outcome.get('run_count') or '?'}**\n\n"
    )
    body += excerpt or "_Follow-up coordination complete._\n"
    meta = _meta("subagent_send", session_id, outcome)
    meta["session_key"] = key
    return body, "subagent_send", meta


def _list_reply(session_id: str) -> tuple[str, str, dict[str, str]]:
    from aethos_core.agents.runtime.subagent_ops import agent_sessions_list_payload

    payload = agent_sessions_list_payload(parent_session_id=session_id, limit=20)
    sessions = list(payload.get("sessions") or [])
    if not sessions:
        body = "**No agent sessions** for this chat yet.\n\nUse **agent_spawn** with a goal to start one."
        return body, "subagent_sessions_empty", _meta("list_empty", session_id, payload)

    lines = ["## Agent sessions\n"]
    for row in sessions[:10]:
        key = row.get("session_key") or "—"
        goal = (row.get("goal") or "")[:100]
        runs = row.get("run_count") or 0
        lines.append(f"- `{key}` · runs {runs} · {goal}")
    body = "\n".join(lines) + "\n"
    meta = _meta("subagent_sessions_list", session_id, payload)
    meta["session_count"] = str(len(sessions))
    return body, "subagent_sessions_list", meta


def _meta(intent_type: str, session_id: str, payload: dict[str, Any]) -> dict[str, str]:
    return {
        "subagent_lane": "true",
        "agent_intent_type": intent_type,
        "fallback_used": "false",
        "read_only": "true",
        "lane": "subagent_session",
        "session_id": session_id,
        "mutation_execution_enabled": "false",
        "status": str(payload.get("status") or intent_type),
    }
