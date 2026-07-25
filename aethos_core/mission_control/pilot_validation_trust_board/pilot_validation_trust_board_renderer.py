# SPDX-License-Identifier: Apache-2.0
"""FIX 183 — Markdown renderer for pilot validation trust board."""

from __future__ import annotations

from typing import Any


def render_pilot_validation_trust_board(pilot_validation_trust_board: dict[str, Any]) -> str:
    sections = pilot_validation_trust_board.get("sections") or {}

    lines = [
        "# Pilot Validation & Trust Board (FIX 183 — validation ≠ re-execution)",
        "",
        f"- session_id: `{pilot_validation_trust_board.get('session_id', '')}`",
        f"- repo/issue: `{pilot_validation_trust_board.get('repo_issue') or 'none'}`",
        f"- pilot outcome: **{pilot_validation_trust_board.get('pilot_outcome', 'none')}**",
        f"- focus audit: `{pilot_validation_trust_board.get('focus_audit_id') or 'none'}`",
        f"- trust recommendation: **{pilot_validation_trust_board.get('trust_recommendation', 'none')}**",
        f"- human effort score: **{pilot_validation_trust_board.get('human_effort_score', 0)}**",
        f"- approval count: **{pilot_validation_trust_board.get('approval_count', 0)}**",
        f"- re-engagement count: **{pilot_validation_trust_board.get('re_engagement_count', 0)}**",
        f"- elapsed seconds: **{pilot_validation_trust_board.get('elapsed_seconds', 0)}**",
        f"- pilot re-execution performed: **{pilot_validation_trust_board.get('pilot_reexecution_performed', False)}** _(always false)_",
        f"- composes FIX 181 audits: **{pilot_validation_trust_board.get('validation_composes_audits_only', True)}**",
        "",
        pilot_validation_trust_board.get("invariant", ""),
        "",
        "_Validation composes pilot audits only — never re-runs FIX 181._",
        "",
    ]

    for title, key in (
        ("Pilot harness upstream read (FIX 181)", "pilot_harness_upstream_read"),
        ("Pilot audit composition", "pilot_audit_composition"),
        ("Stage completion summary", "stage_completion_summary"),
        ("Approval friction metrics", "approval_friction_metrics"),
        ("Re-engagement metrics", "re_engagement_metrics"),
        ("Manual intervention points", "manual_intervention_points"),
        ("Elapsed time", "elapsed_time_capture"),
        ("Evidence completeness", "evidence_completeness_capture"),
        ("Issue risk tier", "issue_risk_tier"),
        ("Human effort scoring", "human_effort_scoring"),
        ("Trust recommendation", "trust_recommendation"),
        ("Audit / replay linkage at validation", "audit_replay_linkage_at_validation"),
        ("Forbidden validation actions", "forbidden_validation_actions"),
        ("Validation integrity scoring", "validation_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("summary_id"):
                lines.append(
                    f"- stages completed: {', '.join(item.get('stages_completed') or []) or 'none'}"
                )
                lines.append(
                    f"- stages pending: {', '.join(item.get('stages_pending') or []) or 'none'}"
                )
                lines.append(f"- stopped at: `{item.get('stage_stopped_at')}`")
            elif item.get("metric_id"):
                lines.append(f"- **{item.get('metric_id')}**: {item}")
            elif item.get("recommendation_id"):
                lines.append(
                    f"- **trust**: `{item.get('trust_recommendation')}` — {item.get('trust_rationale')}"
                )
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('human_effort_score') or item.get('integrity_score')} "
                    f"label={item.get('human_effort_label')}"
                )
            elif item.get("intervention_id"):
                lines.append(f"- `{item.get('intervention_id')}`: {item.get('detail')}")
            elif item.get("capture_id") or item.get("composition_id") or item.get("read_id"):
                lines.append(f"- {item}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Validation board ≠ pilot re-execution — trust metrics from FIX 181 receipts only._")
    return "\n".join(lines)
