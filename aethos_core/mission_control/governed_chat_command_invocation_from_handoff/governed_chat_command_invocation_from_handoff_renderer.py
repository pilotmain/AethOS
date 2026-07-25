# SPDX-License-Identifier: Apache-2.0
"""FIX 180 — Markdown renderer for governed chat command invocation from handoff."""

from __future__ import annotations

from typing import Any


def render_governed_chat_command_invocation_from_handoff(
    governed_chat_command_invocation_from_handoff: dict[str, Any],
) -> str:
    sections = governed_chat_command_invocation_from_handoff.get("sections") or {}

    lines = [
        "# Governed Chat Command Invocation From Handoff (FIX 180 — invocation ≠ direct execution)",
        "",
        f"- session_id: `{governed_chat_command_invocation_from_handoff.get('session_id', '')}`",
        f"- invocation records: **{governed_chat_command_invocation_from_handoff.get('invocation_record_count', 0)}**",
        f"- target gate: `{governed_chat_command_invocation_from_handoff.get('target_gate_id') or 'none'}`",
        f"- frozen chat command: `{governed_chat_command_invocation_from_handoff.get('frozen_chat_command') or 'none'}`",
        f"- invocation tier: `{governed_chat_command_invocation_from_handoff.get('invocation_tier') or 'none'}`",
        f"- invocation ready: **{governed_chat_command_invocation_from_handoff.get('invocation_ready', False)}**",
        f"- direct execution performed: **{governed_chat_command_invocation_from_handoff.get('direct_execution_performed', False)}** _(always false)_",
        f"- direct provider mutation: **{governed_chat_command_invocation_from_handoff.get('direct_provider_mutation_performed', False)}** _(always false)_",
        f"- composes FIX 179: **{governed_chat_command_invocation_from_handoff.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        governed_chat_command_invocation_from_handoff.get("invariant", ""),
        "",
        "_Explicit `invoke handoff command` routes through resolve_chat_turn — never direct provider APIs._",
        "",
    ]

    for title, key in (
        ("Execution request upstream read (FIX 179)", "execution_request_upstream_read"),
        ("Frozen chat command build", "frozen_chat_command_build"),
        ("Governed invocation packet", "governed_invocation_packet"),
        ("Approval gate preservation", "approval_gate_preservation"),
        ("Missing prerequisites at invocation", "missing_prerequisites_at_invocation"),
        ("Risk / blast-radius at invocation", "risk_blast_radius_at_invocation"),
        ("Audit / replay linkage at invocation", "audit_replay_linkage_at_invocation"),
        ("Chat origin logging", "chat_origin_logging"),
        ("Forbidden invocation actions", "forbidden_invocation_actions"),
        ("Next-step invocation sequence", "next_step_invocation_sequence"),
        ("Invocation integrity scoring", "invocation_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: command=`{item.get('frozen_chat_command')}` "
                    f"ready={item.get('invocation_ready')}"
                )
            elif item.get("build_id"):
                lines.append(
                    f"- **{item.get('build_id')}**: `{item.get('frozen_chat_command')}` "
                    f"ready={item.get('build_ready')}"
                )
            elif item.get("origin_id"):
                lines.append(
                    f"- **{item.get('origin_id')}**: origin=`{item.get('handoff_invocation_origin')}` "
                    f"channel=`{item.get('handoff_invocation_channel')}`"
                )
            elif item.get("link_id"):
                lines.append(
                    f"- **{item.get('link_id')}**: timeline=`{item.get('timeline_link_ref')}` "
                    f"replay=`{item.get('replay_link_key')}`"
                )
            elif item.get("phrase_id"):
                lines.append(f"- phrase `{item.get('phrase_id')}`: {item.get('detail')}")
            elif item.get("prerequisite_id"):
                lines.append(f"- prerequisite `{item.get('prerequisite_id')}`: {item.get('detail')}")
            elif item.get("summary_id"):
                lines.append(f"- **{item.get('summary_id')}**: {item.get('detail')}")
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}** ({item.get('upstream_fix')})")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} "
                    f"composes_upstream={item.get('composes_upstream_layers')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Handoff invocation ≠ direct execution — frozen lane governs via chat route._")
    return "\n".join(lines)
