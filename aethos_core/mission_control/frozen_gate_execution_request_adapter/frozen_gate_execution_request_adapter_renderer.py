# SPDX-License-Identifier: Apache-2.0
"""FIX 179 — Markdown renderer for frozen gate execution request adapter."""

from __future__ import annotations

from typing import Any


def render_frozen_gate_execution_request_adapter(
    frozen_gate_execution_request_adapter: dict[str, Any],
) -> str:
    sections = frozen_gate_execution_request_adapter.get("sections") or {}

    lines = [
        "# Frozen Gate Execution Request Adapter (FIX 179 — execution request ≠ execution)",
        "",
        f"- session_id: `{frozen_gate_execution_request_adapter.get('session_id', '')}`",
        f"- execution request records: **{frozen_gate_execution_request_adapter.get('execution_request_record_count', 0)}**",
        f"- target gate: `{frozen_gate_execution_request_adapter.get('target_gate_id') or 'none'}`",
        f"- primary frozen command: `{frozen_gate_execution_request_adapter.get('primary_frozen_command') or 'none'}`",
        f"- execution request tier: `{frozen_gate_execution_request_adapter.get('execution_request_tier') or 'none'}`",
        f"- execution request ready: **{frozen_gate_execution_request_adapter.get('execution_request_ready', False)}**",
        f"- command execution performed: **{frozen_gate_execution_request_adapter.get('command_execution_performed', False)}** _(always false)_",
        f"- gate execution performed: **{frozen_gate_execution_request_adapter.get('gate_execution_performed', False)}** _(always false)_",
        f"- composes FIX 178: **{frozen_gate_execution_request_adapter.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        frozen_gate_execution_request_adapter.get("invariant", ""),
        "",
        "_Adapter produces execution request — operator invokes frozen command via normal chat governance._",
        "",
    ]

    for title, key in (
        ("Intake preview upstream read (FIX 178)", "intake_preview_upstream_read"),
        ("Frozen gate command mapping", "frozen_gate_command_mapping"),
        ("Gate execution request artifact", "gate_execution_request_artifact"),
        ("Approval phrase preservation", "approval_phrase_preservation"),
        ("Missing prerequisites in request", "missing_prerequisites_in_request"),
        ("Risk / blast-radius summary", "risk_blast_radius_summary"),
        ("Audit / replay linkage", "audit_replay_linkage"),
        ("Forbidden request actions", "forbidden_request_actions"),
        ("Next-step request sequence", "next_step_request_sequence"),
        ("Request integrity scoring", "request_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("artifact_id"):
                lines.append(
                    f"- **{item.get('artifact_id')}**: gate=`{item.get('target_gate_id')}` "
                    f"command=`{item.get('primary_frozen_command')}` ready={item.get('execution_request_ready')}"
                )
            elif item.get("mapping_id") and item.get("primary_frozen_command"):
                lines.append(
                    f"- map `{item.get('gate_id')}` → `{item.get('primary_frozen_command')}` "
                    f"route={item.get('software_delivery_route')}"
                )
            elif item.get("phrase_id"):
                phrase = item.get("exact_approval_phrase")
                suffix = f" phrase=`{phrase}`" if phrase else ""
                lines.append(f"- phrase `{item.get('phrase_id')}` required={item.get('approval_phrase_required')}{suffix}")
            elif item.get("prerequisite_id"):
                lines.append(f"- prerequisite `{item.get('prerequisite_id')}`: {item.get('detail')}")
            elif item.get("summary_id"):
                lines.append(f"- **{item.get('summary_id')}**: {item.get('detail')}")
            elif item.get("link_id"):
                lines.append(
                    f"- **{item.get('link_id')}**: timeline=`{item.get('timeline_link_ref')}` "
                    f"replay=`{item.get('replay_link_key')}`"
                )
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

    lines.append("_Execution request ≠ command execution — frozen lane governs actual invocation._")
    return "\n".join(lines)
