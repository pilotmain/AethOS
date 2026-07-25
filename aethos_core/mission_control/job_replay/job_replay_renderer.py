# SPDX-License-Identifier: Apache-2.0
"""FIX 137 — Markdown replay summary export."""

from __future__ import annotations

from typing import Any


def render_job_replay_summary(replay: dict[str, Any]) -> str:
    mission = replay.get("mission") or {}
    lines = [
        "# AethOS Mission Control — Job Replay Summary (FIX 137)",
        "",
        f"- session_id: `{replay.get('session_id', '')}`",
        f"- job_id focus: `{replay.get('job_id') or 'all session activity'}`",
        f"- correlation_id: `{mission.get('correlation_id', '')}`",
        f"- plan_id: `{mission.get('plan_id', '') or 'none'}`",
        f"- steps: **{replay.get('step_count', 0)}**",
        f"- read_only: **{replay.get('read_only', True)}**",
        "",
        "_Replay derived from evidence bundle — no mutations performed._",
        "",
        "## Final state",
        "",
    ]
    final = replay.get("final_state") or {}
    lines.append(f"- plan_status: `{final.get('plan_status', 'unknown')}`")
    lines.append(f"- gates_passed: {', '.join(final.get('gates_passed') or []) or 'none'}")
    lines.append(f"- pending_gates: {', '.join(final.get('pending_gates') or []) or 'none'}")
    lines.extend(["", "## Step playback", ""])

    for step in replay.get("steps") or []:
        idx = step.get("step_index", 0)
        lines.append(f"### Step {idx + 1}: {step.get('action', '')}")
        lines.append(f"- lane: `{step.get('lane', '')}` | source: `{step.get('source', '')}`")
        lines.append(f"- timestamp: `{step.get('timestamp', '')}`")
        lines.append(f"- detail: {step.get('detail', '')}")
        before = step.get("state_before") or {}
        after = step.get("state_after") or {}
        lines.append(f"- state_before.plan_status: `{before.get('plan_status', '')}`")
        lines.append(f"- state_after.plan_status: `{after.get('plan_status', '')}`")
        blockers = step.get("blockers") or []
        if blockers:
            lines.append(f"- blockers at transition: **{len(blockers)}**")
        approvals = step.get("approvals") or []
        if approvals:
            lines.append(f"- approvals at transition: **{len(approvals)}**")
        receipts = step.get("receipts") or []
        if receipts:
            lines.append(f"- receipts: **{len(receipts)}**")
        lines.append("")

    lines.append("_End of replay summary._")
    return "\n".join(lines)
