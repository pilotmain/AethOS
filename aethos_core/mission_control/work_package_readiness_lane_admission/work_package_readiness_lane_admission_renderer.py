# SPDX-License-Identifier: Apache-2.0
"""FIX 169 — Markdown renderer for work package readiness + lane admission."""

from __future__ import annotations

from typing import Any


def render_work_package_readiness_lane_admission(work_package_readiness_lane_admission: dict[str, Any]) -> str:
    sections = work_package_readiness_lane_admission.get("sections") or {}

    lines = [
        "# Work Package Readiness + Lane Admission (FIX 169 — admission cognition)",
        "",
        f"- session_id: `{work_package_readiness_lane_admission.get('session_id', '')}`",
        f"- lane admission records: **{work_package_readiness_lane_admission.get('lane_admission_record_count', 0)}**",
        f"- agent packages: **{work_package_readiness_lane_admission.get('agent_package_count', 0)}**",
        f"- ready agents: **{work_package_readiness_lane_admission.get('ready_agent_count', 0)}**",
        f"- eligible lanes: **{work_package_readiness_lane_admission.get('eligible_lane_count', 0)}**",
        f"- autonomous lane entry: **{work_package_readiness_lane_admission.get('autonomous_lane_entry_enabled', False)}** _(always false)_",
        "",
        work_package_readiness_lane_admission.get("invariant", ""),
        "",
        "_Readiness evaluates lane eligibility — humans authorize entry, never autonomous admission._",
        "",
    ]

    for title, key in (
        ("Package readiness checks", "package_readiness_checks"),
        ("Package readiness by role", "package_readiness_by_role"),
        ("Lane admission analysis", "lane_admission_analysis"),
        ("Admission blockers", "admission_blockers"),
        ("Lane admission package", "lane_admission_package"),
        ("Admission forbidden actions", "admission_forbidden_actions"),
        ("Admission artifact registry", "admission_artifact_registry"),
        ("Next-step admission sequence", "next_step_admission_sequence"),
        ("Admission integrity scoring", "admission_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("check_id"):
                lines.append(f"- check `{item.get('check_id')}`: status={item.get('status')} — {item.get('detail')}")
            elif item.get("readiness_id"):
                lines.append(
                    f"- **{item.get('readiness_id')}**: ready={item.get('lane_admission_ready')} "
                    f"inputs={item.get('inputs_complete')} prereqs={item.get('prerequisites_met')}"
                )
            elif item.get("analysis_id"):
                lanes = ", ".join(item.get("eligible_lanes") or []) or "none"
                lines.append(
                    f"- **{item.get('analysis_id')}**: lanes=`{lanes}` eligible={item.get('admission_eligible')}"
                )
            elif item.get("blocker_id"):
                lines.append(f"- blocker `{item.get('blocker_id')}`: {item.get('detail') or item.get('blocked_by')}")
            elif item.get("package_id") and item.get("admission_ready") is not None:
                lines.append(f"- **{item.get('package_id')}**: admission_ready={item.get('admission_ready')}")
            elif item.get("action_id"):
                lines.append(f"- forbidden `{item.get('action_id')}`: {item.get('detail')}")
            elif item.get("registry_id"):
                lines.append(f"- registry `{item.get('registry_id')}` agent={item.get('agent_role_id')}")
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

    lines.append("_Readiness ≠ execution authority — eligibility only, humans authorize lane entry._")
    return "\n".join(lines)
