# SPDX-License-Identifier: Apache-2.0
"""Multi-agent chat routing — governed coordination lane."""

from __future__ import annotations

from aethos_core.agents.runtime.coordination import run_agent_coordination
from aethos_core.agents.runtime.planner import is_multi_agent_request
from aethos_core.local_workspace.session_context import resolve_operational_hint


def multi_agent_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_multi_agent_request(raw, session_id=session_id):
        return None

    hint = resolve_operational_hint(None, session_id=session_id)
    result = run_agent_coordination(goal=raw, session_id=session_id, workspace_hint=hint)
    if not result.get("ok"):
        return (
            str(result.get("error") or "Coordination failed"),
            "agent_coordination_failed",
            _meta("coordination_failed", session_id),
        )

    plan = result.get("plan") or {}
    meta = _meta("agent_coordination", session_id)
    meta["plan_id"] = str(plan.get("plan_id") or "")
    meta["coordination_artifact_id"] = str(result.get("coordination_artifact_id") or "")
    meta["agent_count"] = str(plan.get("agent_count") or "0")
    meta["status"] = str((result.get("merged") or {}).get("status") or "unknown")
    return result.get("report") or "Multi-agent report complete.", "agent_coordination", meta


def multi_agent_job_reply(
    text: str, *, session_id: str = "default"
) -> tuple[str, str, dict[str, str]] | None:
    """Durable variant of ``multi_agent_reply``.

    Instead of running ``run_agent_coordination`` synchronously inside the chat
    request (which dies the moment the browser connection drops on navigation),
    enqueue a server-side ``agent_coordination`` job on the durable executor and
    return immediately with the ``job_id``. The run then lives on the server; the
    UI subscribes to the job lifecycle and shows progress / the consolidated plan
    as it completes, regardless of what the operator clicks.
    """
    raw = (text or "").strip()
    if not is_multi_agent_request(raw, session_id=session_id):
        return None

    from aethos_core.runtime.authority import authority

    hint = resolve_operational_hint(None, session_id=session_id)
    params: dict[str, object] = {"goal": raw, "session_id": session_id}
    if hint:
        params["workspace_hint"] = hint
    job = authority.create_job(
        title=raw[:120] or "Multi-agent coordination",
        job_type="agent_coordination",
        params=params,
        source="chat",
        session_id=session_id,
        auto_run=True,
    )
    meta = _meta("agent_coordination", session_id)
    meta["proposed_job_id"] = job.id
    meta["proposed_job_type"] = job.job_type
    body = (
        "Coordinating the agents on this in the background — it keeps running even "
        "if you switch chats, open Mission Control, or close this tab.\n\n"
        f"Tracking as job `{job.id}`. Progress and the full consolidated plan will "
        "appear here as it runs (also saved in **Mission Control → Jobs**)."
    )
    return body, "agent_coordination_job_created", meta


def _meta(intent_type: str, session_id: str) -> dict[str, str]:
    return {
        "multi_agent_route_selected": "true",
        "agent_intent_type": intent_type,
        "fallback_used": "false",
        "read_only": "true",
        "lane": "multi_agent_orchestration",
        "session_id": session_id,
        "mutation_execution_enabled": "false",
    }
