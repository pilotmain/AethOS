# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — Markdown renderer for cross-session organizational memory."""

from __future__ import annotations

from typing import Any


def render_cross_session_operational_memory(memory: dict[str, Any]) -> str:
    org = memory.get("organizational_memory") or {}
    lines = [
        "# Cross-Session Operational Memory (FIX 140 — organizational layer)",
        "",
        f"- focal session: `{memory.get('focal_session_id', '')}`",
        f"- persisted records: **{memory.get('persisted_record_count', 0)}**",
        f"- ingested current session: **{memory.get('ingested_current_session', False)}**",
        f"- autonomous adaptation: **{memory.get('autonomous_adaptation_enabled', False)}** _(always false)_",
        "",
        memory.get("invariant", ""),
        "",
        "## Missions across sessions",
        "",
    ]
    missions = org.get("missions_across_sessions") or []
    if not missions:
        lines.append("_No cross-session mission groups yet — ingest builds history over time._")
    for row in missions[:12]:
        lines.append(
            f"- `{row.get('kind')}` **{row.get('key')}** — sessions: {', '.join(row.get('session_ids') or [])}"
        )

    lines.extend(["", "## Recurring incidents", ""])
    for row in org.get("recurring_incidents") or []:
        lines.append(f"- `{row.get('incident_id', '')}` × **{row.get('occurrences', 0)}**")

    lines.extend(["", "## PR lineage across sessions", ""])
    for row in org.get("pr_lineage_across_sessions") or []:
        lines.append(
            f"- `{row.get('pr_key', '')}` — {row.get('session_count', 0)} session(s): "
            f"{', '.join(row.get('session_ids') or [])}"
        )

    lines.extend(["", "## Historical blockers", ""])
    for row in org.get("historical_blockers") or []:
        cross = "cross-session" if row.get("cross_session") else "single-session"
        lines.append(f"- `{row.get('blocker', '')}` × **{row.get('occurrences', 0)}** ({cross})")

    lines.extend(["", "## Operator history", ""])
    for row in (org.get("operator_history") or [])[:10]:
        lines.append(
            f"- `{row.get('recorded_at', '')}` session=`{row.get('session_id', '')}` "
            f"plan=`{row.get('plan_id') or '—'}` nodes={row.get('node_count', '—')}"
        )

    lines.extend(["", "## Mission ancestry", ""])
    for chain in (org.get("mission_ancestry") or [])[:8]:
        steps = chain.get("ancestry") or []
        lines.append(f"- plan `{chain.get('plan_id', '')}` depth **{chain.get('depth', 0)}**")
        for step in steps[-3:]:
            lines.append(f"  - {step.get('recorded_at', '')} session={step.get('session_id', '')}")

    lines.extend(["", "## Approval / risk patterns", ""])
    for row in (org.get("approval_risk_patterns") or [])[:12]:
        if row.get("pattern") == "gate_frequency":
            lines.append(f"- gate `{row.get('gate_id', '')}` × **{row.get('occurrences', 0)}**")
        else:
            lines.append(f"- outcome `{row.get('outcome', '')}` × **{row.get('occurrences', 0)}**")

    lines.extend(["", "## Rollout lineage", ""])
    for row in (org.get("rollout_lineage") or [])[:8]:
        lines.append(f"- `{row.get('current_stage', '')}` @ {row.get('recorded_at', '')}")

    lines.extend(["", "## Evidence stitching", ""])
    for row in (org.get("evidence_stitching") or [])[:10]:
        lines.append(
            f"- `{row.get('stitch_kind', '')}` **{row.get('key', '')}** — {row.get('record_count', 0)} records"
        )

    lines.extend(["", "## Learning signals (observation only)", ""])
    for sig in memory.get("learning_signals") or []:
        lines.append(f"- **{sig.get('signal', '')}**: {sig.get('detail', '')}")

    lines.extend(
        [
            "",
            "_FIX 140 persists read-only organizational memory — no mutations, adaptation, or optimization._",
        ]
    )
    return "\n".join(lines)
