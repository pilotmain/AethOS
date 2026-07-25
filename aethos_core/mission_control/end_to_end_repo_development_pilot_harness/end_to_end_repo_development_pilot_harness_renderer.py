# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — Markdown renderer for end-to-end repo development pilot harness."""

from __future__ import annotations

from typing import Any


def render_end_to_end_repo_development_pilot_harness(
    end_to_end_repo_development_pilot_harness: dict[str, Any],
) -> str:
    sections = end_to_end_repo_development_pilot_harness.get("sections") or {}

    lines = [
        "# End-to-End Repo Development Pilot Harness (FIX 181 — pilot ≠ autonomous execution)",
        "",
        f"- session_id: `{end_to_end_repo_development_pilot_harness.get('session_id', '')}`",
        f"- repo/issue: `{end_to_end_repo_development_pilot_harness.get('repo_issue') or 'none'}`",
        f"- pilot records: **{end_to_end_repo_development_pilot_harness.get('pilot_record_count', 0)}**",
        f"- pending commands: **{end_to_end_repo_development_pilot_harness.get('pending_command_count', 0)}**",
        f"- terminal stage: `{end_to_end_repo_development_pilot_harness.get('terminal_stage') or 'pr_open'}`",
        f"- pilot ready: **{end_to_end_repo_development_pilot_harness.get('pilot_ready', False)}**",
        f"- autonomous pipeline execution: **{end_to_end_repo_development_pilot_harness.get('autonomous_pipeline_execution_enabled', False)}** _(always false)_",
        f"- railway mutation: **{end_to_end_repo_development_pilot_harness.get('railway_mutation_enabled', False)}** _(always false)_",
        f"- composes FIX 180: **{end_to_end_repo_development_pilot_harness.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        end_to_end_repo_development_pilot_harness.get("invariant", ""),
        "",
        "_Explicit `run pilot` routes each stage through resolve_chat_turn — one repo, one issue, no merge/deploy._",
        "",
    ]

    for title, key in (
        ("Handoff invocation upstream read (FIX 180)", "handoff_invocation_upstream_read"),
        ("Pilot configuration", "pilot_configuration"),
        ("Pilot stage status matrix", "pilot_stage_status_matrix"),
        ("Governed pilot packet", "governed_pilot_packet"),
        ("Mission Control timeline capture", "mission_control_timeline_capture"),
        ("Evidence bundle capture", "evidence_bundle_capture"),
        ("Approval-friction verification", "approval_friction_verification"),
        ("Missing prerequisites at pilot", "missing_prerequisites_at_pilot"),
        ("Risk / blast-radius at pilot", "risk_blast_radius_at_pilot"),
        ("Audit / replay linkage at pilot", "audit_replay_linkage_at_pilot"),
        ("Pilot origin logging", "pilot_origin_logging"),
        ("Forbidden pilot actions", "forbidden_pilot_actions"),
        ("Next-step pilot sequence", "next_step_pilot_sequence"),
        ("Pilot integrity scoring", "pilot_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("stage_id"):
                lines.append(
                    f"- **{item.get('stage_id')}** ({item.get('fix')}): "
                    f"satisfied={item.get('satisfied')}"
                )
            elif item.get("config_id"):
                lines.append(
                    f"- **{item.get('config_id')}**: repo=`{item.get('repo')}` "
                    f"issue=`{item.get('issue_number')}` merge={item.get('merge_enabled')}"
                )
            elif item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: next=`{item.get('next_stage')}` "
                    f"pending={item.get('pending_command_count')}"
                )
            elif item.get("capture_id"):
                lines.append(f"- **{item.get('capture_id')}**: {item.get('detail') or item}")
            elif item.get("verification_id"):
                lines.append(f"- **{item.get('verification_id')}**: {item.get('detail')}")
            elif item.get("origin_id"):
                lines.append(
                    f"- **{item.get('origin_id')}**: origin=`{item.get('pilot_harness_origin')}` "
                    f"channel=`{item.get('pilot_harness_channel')}`"
                )
            elif item.get("link_id"):
                lines.append(
                    f"- **{item.get('link_id')}**: timeline=`{item.get('timeline_link_ref')}` "
                    f"replay=`{item.get('replay_link_key')}`"
                )
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}** ({item.get('upstream_fix')})")
            elif item.get("prerequisite_id"):
                lines.append(f"- prerequisite `{item.get('prerequisite_id')}`: {item.get('detail')}")
            elif item.get("summary_id"):
                lines.append(f"- **{item.get('summary_id')}**: {item.get('detail')}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} "
                    f"stages={item.get('stages_satisfied')}"
                )
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Pilot harness ≠ autonomous pipeline execution — bounded repo development through chat governance._")
    return "\n".join(lines)
