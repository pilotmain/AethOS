# SPDX-License-Identifier: Apache-2.0
"""FIX 136 — Markdown renderer for operator evidence bundles."""

from __future__ import annotations

from typing import Any

from aethos_core.mission_control.cross_lane.snapshot_renderer import render_snapshot


def render_evidence_bundle_markdown(bundle: dict[str, Any]) -> str:
    mission = bundle.get("mission") or {}
    lines = [
        "# AethOS Mission Control — Operator Evidence Bundle (FIX 136)",
        "",
        f"- exported_at: `{bundle.get('exported_at', '')}`",
        f"- session_id: `{bundle.get('session_id', '')}`",
        f"- correlation_id: `{mission.get('correlation_id', '')}`",
        f"- plan_id: `{mission.get('plan_id', '') or 'none'}`",
        f"- job_id focus: `{bundle.get('job_id') or 'all session jobs'}`",
        f"- read_only: **{bundle.get('read_only', True)}**",
        "",
        "_No mutations performed by this export._",
        "",
        "## Mission summary",
        "",
        render_snapshot(dict(bundle.get("snapshot") or {})),
        "",
        "## Timeline",
        "",
    ]
    timeline = bundle.get("timeline") or []
    if not timeline:
        lines.append("_No timeline entries._")
    else:
        for entry in timeline[:80]:
            lines.append(
                f"- `{entry.get('timestamp', '')}` **{entry.get('lane', '')}** "
                f"{entry.get('action', '')} — {entry.get('detail', '')}"
            )
    lines.extend(["", "## Blockers & attention", ""])
    blockers = bundle.get("blockers") or []
    if not blockers:
        lines.append("_No blockers recorded._")
    else:
        for row in blockers[:40]:
            lines.append(f"- `{row.get('source', '')}` {row.get('lane', '')} — {row.get('detail', row.get('gate', ''))}")

    lines.extend(["", "## Approvals", ""])
    approvals = bundle.get("approvals") or {}
    inbox = approvals.get("pending_inbox") or {}
    summary = inbox.get("summary") or {}
    lines.append(f"- pending: **{summary.get('total_pending', 0)}** | ui_eligible: **{summary.get('ui_eligible_count', 0)}**")
    audits = (approvals.get("ui_audit") or {}).get("audits") or []
    lines.append(f"- ui approval audits: **{len(audits)}**")
    for row in audits[:25]:
        lines.append(
            f"  - `{row.get('recorded_at', '')}` {row.get('gate_id', '')} — "
            f"{row.get('outcome', '')} (mutation={row.get('mutation_performed', False)})"
        )

    lines.extend(["", "## Verification (software delivery)", ""])
    verification = bundle.get("verification") or {}
    sections = verification.get("sections") or []
    if not sections:
        lines.append("_No verification sections._")
    else:
        for section in sections:
            lines.append(f"### {section.get('title', section.get('section_id', ''))}")
            for row in section.get("rows") or []:
                lines.append(f"- {row.get('label', '')}: {row.get('value', '')}")

    lines.extend(["", "## Receipts", ""])
    receipts = bundle.get("receipts") or []
    if not receipts:
        lines.append("_No receipt records in bundle._")
    else:
        for receipt in receipts[:30]:
            lines.append(
                f"- `{receipt.get('recorded_at', '')}` {receipt.get('phase', '')} — {receipt.get('detail', '')}"
            )

    lines.extend(["", "## Session jobs", ""])
    jobs = bundle.get("jobs") or []
    if not jobs:
        lines.append("_No tracked jobs for this session._")
    else:
        for job in jobs[:30]:
            lines.append(
                f"- `{job.get('id', '')}` **{job.get('status', '')}** {job.get('job_type', '')} — {job.get('title', '')}"
            )

    lines.extend(["", "## Job evidence", ""])
    job_evidence = bundle.get("job_evidence") or {}
    if not job_evidence:
        lines.append("_No provider evidence bundles attached._")
    else:
        for jid, payload in list(job_evidence.items())[:20]:
            op = payload.get("operation") or payload.get("provider") or "evidence"
            lines.append(f"- `{jid}` — {op}")

    lines.extend(["", "## Operation lifecycle", ""])
    lifecycle = bundle.get("operation_lifecycle") or []
    if not lifecycle:
        lines.append("_No lifecycle index entries for session._")
    else:
        for entry in lifecycle[:20]:
            lines.append(
                f"- `{entry.get('provider', '')}` {entry.get('operation', '')} "
                f"status={entry.get('status') or entry.get('canonical_state', '')}"
            )

    lines.extend(["", "## Incident linkage", ""])
    inc = bundle.get("incident_links") or {}
    lines.append(
        f"- incidents: **{inc.get('incident_count', 0)}** | open: **{inc.get('open_incidents', 0)}**"
    )

    lines.extend(["", "## Lane drilldown index", ""])
    for lane, payload in (bundle.get("lane_drilldowns") or {}).items():
        section_count = len(payload.get("sections") or [])
        lines.append(f"- `{lane}` — {section_count} section(s)")

    lines.append("\n_Full structured data available in JSON export._")
    return "\n".join(lines)
