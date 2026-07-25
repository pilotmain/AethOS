# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — Mission Control snapshot renderer."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.cross_lane.cross_lane_contract import ARCHITECTURE_BOUNDARY


def render_snapshot(snapshot: dict[str, Any]) -> str:
    health = snapshot.get("execution_health") or {}
    lines = [
        "# AethOS Mission Control — Cross-Lane Snapshot (FIX 128)",
        "",
        f"- snapshot_id: `{snapshot.get('snapshot_id', '')}`",
        f"- correlation_id: `{snapshot.get('correlation_id', '')}`",
        f"- session_id: `{snapshot.get('session_id', '')}`",
        f"- plan_id: `{snapshot.get('plan_id', '') or 'none'}`",
        f"- overall health: **{health.get('overall', 'unknown')}**",
        "",
        "## Architecture boundary",
        f"`{ARCHITECTURE_BOUNDARY}`",
        "",
        "## Execution health",
        f"- software delivery pending gates: **{health.get('software_delivery_pending_gates', 0)}**",
        f"- open incidents: **{health.get('open_incidents', 0)}**",
        f"- railway journals (recent): **{health.get('railway_journals_seen', 0)}**",
        "",
        "## Operator attention queue",
    ]
    queue = snapshot.get("attention_queue") or []
    if not queue:
        lines.append("_No pending governance gates in attention queue._")
    else:
        for item in queue:
            lines.append(
                f"- **[{item.get('priority', '')}]** `{item.get('lane')}` — {item.get('gate')}"
                + (f" (count={item.get('count')})" if item.get("count") else "")
            )
    lines.extend(["", "## Active approvals / gates", ""])
    approvals = snapshot.get("active_approvals") or []
    if not approvals:
        lines.append("_None flagged._")
    else:
        for item in approvals:
            lines.append(f"- `{item.get('gate')}` ({item.get('lane')})")
    lines.extend(["", "## Agent collaboration summary", ""])
    ma = snapshot.get("agent_collaboration_summary") or {}
    lines.append(
        f"- status: **{ma.get('status', 'not_run')}** | agents: {', '.join(ma.get('agents_run') or []) or 'none'}"
    )
    lines.extend(["", "## Rollout / production governance", ""])
    pg = snapshot.get("rollout_visibility") or {}
    lines.append(
        f"- rollout records: **{pg.get('rollout_records', 0)}** | latest stage: `{pg.get('latest_rollout_stage', 'n/a')}`"
    )
    lines.extend(["", "## Incident linkage", ""])
    inc = snapshot.get("incident_linkage") or {}
    lines.append(
        f"- incidents tracked: **{inc.get('incident_count', 0)}** | open: **{inc.get('open_incidents', 0)}**"
    )
    lines.extend(["", "## Unified timeline (recent)", ""])
    timeline = snapshot.get("unified_timeline") or []
    if not timeline:
        lines.append("_No cross-lane timeline entries._")
    else:
        for entry in timeline[:15]:
            lines.append(
                f"- `{entry.get('timestamp', '')}` **{entry.get('lane', '')}** "
                f"{entry.get('action', '')} — {entry.get('detail', '')}"
            )
    lines.append("\n_Read-only observability — no mutations performed._")
    return "\n".join(lines)


def render_timeline(snapshot: dict[str, Any]) -> str:
    lines = ["# Mission Control — Unified Timeline", ""]
    for entry in snapshot.get("unified_timeline") or []:
        lines.append(
            f"- `{entry.get('timestamp', '')}` [{entry.get('lane', '')}] "
            f"**{entry.get('action', '')}** — {entry.get('detail', '')}"
        )
    if len(lines) == 2:
        lines.append("_Empty._")
    return "\n".join(lines)


def render_attention_queue(snapshot: dict[str, Any]) -> str:
    lines = ["# Mission Control — Attention Queue", ""]
    for item in snapshot.get("attention_queue") or []:
        lines.append(f"- **{item.get('priority')}** `{item.get('lane')}` → `{item.get('gate')}`")
    if len(lines) == 2:
        lines.append("_Queue empty._")
    return "\n".join(lines)


def render_health_summary(snapshot: dict[str, Any]) -> str:
    h = snapshot.get("execution_health") or {}
    return "\n".join(
        [
            "# Mission Control — Health Summary",
            "",
            f"- overall: **{h.get('overall', '')}**",
            f"- software_delivery_pending_gates: **{h.get('software_delivery_pending_gates', 0)}**",
            f"- open_incidents: **{h.get('open_incidents', 0)}**",
            f"- mutation in this view: **{h.get('mutation_performed_in_snapshot', False)}**",
        ]
    )


def render_audit_search(snapshot: dict[str, Any]) -> str:
    lines = [
        "# Mission Control — Audit Search",
        "",
        f"- query: `{snapshot.get('audit_query', '')}`",
        f"- matches: **{len(snapshot.get('audit_matches') or [])}**",
        "",
    ]
    for entry in snapshot.get("audit_matches") or []:
        lines.append(f"- `{entry.get('timestamp', '')}` **{entry.get('lane')}** {entry.get('action')}")
    return "\n".join(lines)
