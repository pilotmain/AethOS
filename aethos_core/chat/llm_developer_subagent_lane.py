# SPDX-License-Identifier: Apache-2.0
"""LLM tool-loop subagent spawn — on-demand dev_workspace agent with governed tools."""

from __future__ import annotations

import re
from typing import Any

_LLM_DEV_RX = re.compile(
    r"\bagent_spawn\b.*\b(llm|tool.?loop)\b.*\bdeveloper\b|\bdev_workspace\b.*\b(llm|tool.?loop)\b|\bllm\s+developer\s+spawn\b",
    re.I,
)


def is_llm_developer_spawn_request(text: str) -> bool:
    return bool(_LLM_DEV_RX.search((text or "").strip()))


def extract_llm_developer_goal(text: str) -> str:
    raw = (text or "").strip()
    for prefix in (
        r"agent_spawn\s+",
        r"llm\s+developer\s+spawn\s*[:]\s*",
        r"dev_workspace\s+llm\s*[:]\s*",
    ):
        raw = re.sub(prefix, "", raw, flags=re.I).strip()
    raw = re.sub(r"\bsave\s+session_key\b", "", raw, flags=re.I).strip()
    return raw


def llm_developer_subagent_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_llm_developer_spawn_request(text):
        return None

    goal = extract_llm_developer_goal(text)
    if len(goal) < 8:
        reply = (
            "Describe the developer task after `agent_spawn llm developer:` "
            "(e.g. scan providers, propose terminal preflight for failing tests)."
        )
        return reply, "llm_developer_spawn_help", _meta(session_id, mode="help")

    from aethos_core.agents.runtime.subagent_ops import spawn_llm_developer_subagent

    outcome = spawn_llm_developer_subagent(goal=goal, session_id=session_id)
    if not outcome.get("ok"):
        err = outcome.get("error") or "spawn_failed"
        return (
            f"LLM developer spawn failed: `{err}`. {outcome.get('hint') or ''}".strip(),
            "llm_developer_spawn_failed",
            _meta(session_id, mode="failed"),
        )

    session_key = str(outcome.get("session_key") or "")
    reply = (
        f"**LLM developer subagent** (governed tool loop)\n\n"
        f"**session_key:** `{session_key}`\n\n"
        f"{outcome.get('reply') or ''}"
    )
    meta = _meta(session_id, mode="spawn")
    meta["session_key"] = session_key
    meta["spawn_id"] = str(outcome.get("spawn_id") or "")
    meta["lane"] = "llm_developer_subagent"
    meta["agent_tool_calls"] = str(outcome.get("tool_calls") or 0)
    return reply, "llm_developer_spawn", meta


def _meta(session_id: str, *, mode: str) -> dict[str, str]:
    return {
        "route_id": "llm_developer_subagent",
        "matched_module": "chat.llm_developer_subagent_lane",
        "session_id": session_id,
        "llm_developer_mode": mode,
        "presentation_mode": "direct",
    }
