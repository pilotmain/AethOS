# SPDX-License-Identifier: Apache-2.0
"""FIX 173 — Markdown renderer for gate-routed package outcome review."""

from __future__ import annotations

from typing import Any


def render_gate_routed_package_outcome_review(gate_routed_package_outcome_review: dict[str, Any]) -> str:
    sections = gate_routed_package_outcome_review.get("sections") or {}

    lines = [
        "# Gate-Routed Package Outcome Review (FIX 173 — review before lane action)",
        "",
        f"- session_id: `{gate_routed_package_outcome_review.get('session_id', '')}`",
        f"- gate review records: **{gate_routed_package_outcome_review.get('gate_review_record_count', 0)}**",
        f"- outcomes collected: **{gate_routed_package_outcome_review.get('outcome_count', 0)}**",
        f"- incomplete packages: **{gate_routed_package_outcome_review.get('incomplete_package_count', 0)}**",
        f"- review tier: `{gate_routed_package_outcome_review.get('review_tier') or 'none'}`",
        f"- review ready: **{gate_routed_package_outcome_review.get('review_ready', False)}**",
        f"- execution performed: **{gate_routed_package_outcome_review.get('execution_performed', False)}** _(always false)_",
        f"- gate bypass: **{gate_routed_package_outcome_review.get('gate_bypass_enabled', False)}** _(always false)_",
        "",
        gate_routed_package_outcome_review.get("invariant", ""),
        "",
        "_Review classifies outcomes and maps to frozen gates — existing gates decide lane action._",
        "",
    ]

    for title, key in (
        ("Coordination context read", "coordination_context_read"),
        ("Package outcome collection", "package_outcome_collection"),
        ("Outcome quality classification", "outcome_quality_classification"),
        ("Incomplete package detection", "incomplete_package_detection"),
        ("Escalation trigger detection", "escalation_trigger_detection"),
        ("Frozen gate mapping", "frozen_gate_mapping"),
        ("Gate review packet", "gate_review_packet"),
        ("Gate handler routing", "gate_handler_routing"),
        ("Forbidden review actions", "forbidden_review_actions"),
        ("Next-step gate review sequence", "next_step_gate_review_sequence"),
        ("Gate review integrity scoring", "gate_review_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("packet_id"):
                lines.append(
                    f"- **{item.get('packet_id')}**: complete={item.get('outcomes_complete')} "
                    f"partial={item.get('outcomes_partial')} incomplete={item.get('outcomes_incomplete')}"
                )
            elif item.get("handling_gate"):
                lines.append(
                    f"- route `{item.get('route_id')}` → gate `{item.get('handling_gate')}` "
                    f"bypass={item.get('gate_bypass', False)}"
                )
            elif item.get("classification_id"):
                lines.append(
                    f"- **{item.get('classification_id')}**: quality={item.get('outcome_quality')} "
                    f"state={item.get('lifecycle_state')}"
                )
            elif item.get("mapping_id"):
                lines.append(
                    f"- mapping `{item.get('gate_id')}` frozen={item.get('frozen_software_delivery_gate')}"
                )
            elif item.get("detection_id"):
                lines.append(f"- detection `{item.get('detection_id')}`: incomplete={item.get('incomplete')}")
            elif item.get("trigger_id") or item.get("monitor_id"):
                tid = item.get("trigger_id") or item.get("monitor_id")
                lines.append(f"- trigger `{tid}`: escalation={item.get('escalation_required')}")
            elif item.get("read_id"):
                lines.append(f"- **{item.get('read_id')}**: ready={item.get('review_ready')}")
            elif item.get("outcome_id"):
                lines.append(f"- outcome `{item.get('outcome_id')}`: package={item.get('package_id')}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("step") is not None:
                lines.append(f"- step {item.get('step')}: `{item.get('command_hint')}`")
            elif item.get("score_id"):
                lines.append(
                    f"- **{item.get('score_id')}**: score={item.get('integrity_score')} label={item.get('integrity_label')}"
                )
            elif item.get("content"):
                lines.append(f"- {item.get('content')}")
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Gate review ≠ execution — hand outcomes to existing frozen gates._")
    return "\n".join(lines)
