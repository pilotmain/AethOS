# SPDX-License-Identifier: Apache-2.0
"""FIX 182 — Markdown renderer for repo pilot readiness dashboard."""

from __future__ import annotations

from typing import Any


def render_repo_pilot_readiness_dashboard(repo_pilot_readiness_dashboard: dict[str, Any]) -> str:
    sections = repo_pilot_readiness_dashboard.get("sections") or {}

    lines = [
        "# Repo Pilot Readiness Dashboard (FIX 182 — readiness ≠ execution)",
        "",
        f"- session_id: `{repo_pilot_readiness_dashboard.get('session_id', '')}`",
        f"- repo: `{repo_pilot_readiness_dashboard.get('repo') or 'none'}`",
        f"- issue: `{repo_pilot_readiness_dashboard.get('repo_issue') or 'none'}`",
        f"- pilot preflight ready: **{repo_pilot_readiness_dashboard.get('pilot_preflight_ready', False)}**",
        f"- checks ready: **{repo_pilot_readiness_dashboard.get('checks_ready', 0)}** / **{repo_pilot_readiness_dashboard.get('checks_total', 0)}**",
        f"- pilot blockers: **{repo_pilot_readiness_dashboard.get('pilot_blocker_count', 0)}**",
        f"- pilot execution performed: **{repo_pilot_readiness_dashboard.get('pilot_execution_performed', False)}** _(always false)_",
        f"- composes FIX 181: **{repo_pilot_readiness_dashboard.get('composes_upstream_layers_not_duplicates', True)}**",
        "",
        repo_pilot_readiness_dashboard.get("invariant", ""),
        "",
        "_Readiness visibility only — use FIX 181 `run pilot` for explicit execution._",
        "",
    ]

    for title, key in (
        ("Pilot harness upstream read (FIX 181)", "pilot_harness_upstream_read"),
        ("Repo selection", "repo_selection_readiness"),
        ("Issue selection", "issue_selection_readiness"),
        ("GitHub auth status", "github_auth_status_readiness"),
        ("Branch permissions", "branch_permissions_readiness"),
        ("Workspace readiness", "workspace_readiness"),
        ("Verification command readiness", "verification_command_readiness"),
        ("PR creation readiness", "pr_creation_readiness"),
        ("Mission Control evidence readiness", "mission_control_evidence_readiness"),
        ("Approval-friction summary", "approval_friction_summary"),
        ("Pilot blocker list", "pilot_blocker_list"),
        ("Audit / replay linkage at readiness", "audit_replay_linkage_at_readiness"),
        ("Forbidden readiness actions", "forbidden_readiness_actions"),
        ("Next-step readiness sequence", "next_step_readiness_sequence"),
        ("Readiness integrity scoring", "readiness_integrity_scoring"),
    ):
        items = sections.get(key) or []
        lines.extend([f"## {title}", ""])
        if not items:
            lines.append("_None recorded._")
        for item in items:
            if item.get("selection_id"):
                lines.append(
                    f"- **{item.get('selection_id')}**: ready={item.get('ready')} "
                    f"repo=`{item.get('repo') or item.get('repo_issue')}`"
                )
            elif item.get("status_id"):
                lines.append(
                    f"- **{item.get('status_id')}**: ready={item.get('ready')} "
                    f"token={item.get('api_token_state')}"
                )
            elif item.get("permission_id"):
                lines.append(
                    f"- **{item.get('permission_id')}**: ready={item.get('ready')} "
                    f"branch={item.get('branch_orchestration_enabled')}"
                )
            elif item.get("readiness_id"):
                lines.append(f"- **{item.get('readiness_id')}**: ready={item.get('ready')}")
            elif item.get("phrase_id"):
                lines.append(f"- phrase `{item.get('phrase_id')}`: required={item.get('exact_phrase_required')}")
            elif item.get("summary_id"):
                lines.append(f"- **{item.get('summary_id')}**: phrases={item.get('phrase_count')}")
            elif item.get("blocker_id"):
                lines.append(f"- **{item.get('blocker_id')}**: `{item.get('code') or item.get('detail')}`")
            elif item.get("link_id"):
                lines.append(
                    f"- **{item.get('link_id')}**: timeline=`{item.get('timeline_link_ref')}`"
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
                    f"blockers={item.get('blocker_count')}"
                )
            elif item.get("detail"):
                lines.append(f"- {item.get('detail')}")
            else:
                lines.append(f"- {item}")
        lines.append("")

    lines.append("_Readiness dashboard ≠ pilot execution — preflight before running AethOS on each repo._")
    return "\n".join(lines)
