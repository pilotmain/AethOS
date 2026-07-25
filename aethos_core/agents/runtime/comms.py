# SPDX-License-Identifier: Apache-2.0
"""Inter-agent communication bus — records who-talks-to-whom during a coordination run.

This powers the live multi-agent visual: as the orchestrator dispatches work, agents
report back, and completed agents hand off to the next, each message is recorded as an
event ({seq, ts, from, to, type, summary}). The UI replays/animates these to show the team
working in real time. Events persist per session so the visual survives a page reload.

Recording is strictly observational and wrapped by callers in try/except — it must never
affect the coordination itself.
"""

from __future__ import annotations

import time
from typing import Any

from aethos_core.tenancy import get_current_tenant
from aethos_core.tenancy.tenant_data_store import get_record, set_record

NAMESPACE = "agent_comms"
MAX_EVENTS = 300
ORCHESTRATOR = "orchestrator"


def _now() -> float:
    return time.time()


def _load(session_id: str, owner: str) -> dict[str, Any]:
    rec = get_record(NAMESPACE, session_id, tenant_id=owner, default=None)
    if isinstance(rec, dict):
        return rec
    return {"session_id": session_id, "agents": [], "events": []}


def start_coordination_comms(
    session_id: str, agents: list[dict[str, Any]], *, goal: str = "", tenant_id: str | None = None
) -> None:
    """Reset the comms log for a session and register the agent roster (+ orchestrator)."""
    owner = tenant_id or get_current_tenant() or "default"
    roster = [{"id": ORCHESTRATOR, "label": "Orchestrator", "role": "orchestrator"}]
    for a in agents:
        roster.append({"id": a.get("id"), "label": a.get("label"), "role": a.get("role")})
    set_record(
        NAMESPACE,
        session_id,
        {
            "session_id": session_id,
            "goal": goal[:200],
            "agents": roster,
            "events": [],
            "started_at": _now(),
            "status": "running",
        },
        tenant_id=owner,
    )


def finish_coordination_comms(session_id: str, *, tenant_id: str | None = None) -> None:
    """Mark a session's comms complete so the live UI knows to stop polling."""
    owner = tenant_id or get_current_tenant() or "default"
    rec = _load(session_id, owner)
    rec["status"] = "done"
    rec["finished_at"] = _now()
    set_record(NAMESPACE, session_id, rec, tenant_id=owner)


def record_agent_message(
    session_id: str,
    *,
    frm: str,
    to: str,
    mtype: str,
    summary: str = "",
    tenant_id: str | None = None,
) -> None:
    """Append one inter-agent message. ``mtype`` ∈ dispatch | report | handoff."""
    owner = tenant_id or get_current_tenant() or "default"
    rec = _load(session_id, owner)
    events = rec.get("events") or []
    events.append(
        {
            "seq": len(events),
            "ts": _now(),
            "from": frm,
            "to": to,
            "type": mtype,
            "summary": (summary or "")[:200],
        }
    )
    rec["events"] = events[-MAX_EVENTS:]
    set_record(NAMESPACE, session_id, rec, tenant_id=owner)


def get_agent_comms(session_id: str, *, tenant_id: str | None = None) -> dict[str, Any]:
    owner = tenant_id or get_current_tenant() or "default"
    return _load(session_id, owner)
