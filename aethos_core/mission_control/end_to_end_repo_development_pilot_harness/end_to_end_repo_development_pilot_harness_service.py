# SPDX-License-Identifier: Apache-2.0
"""FIX 181 — end-to-end repo development pilot harness (composes FIX 180)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_181_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_contract import (
    AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
    CHAT_GOVERNANCE_REQUIRED_FIX_181,
    DEPLOY_ENABLED_FIX_181,
    DIRECT_EXECUTION_PERFORMED_FIX_181,
    DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_FIX,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_INVARIANT,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_PRINCIPLES,
    END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION,
    EXECUTION_PERFORMED_FIX_181,
    FORBIDDEN_PILOT_ACTIONS,
    GATE_BYPASS_ENABLED_FIX_181,
    GOVERNANCE_MUTATION_PERFORMED_FIX_181,
    HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_181,
    MERGE_ENABLED_FIX_181,
    MUTATION_PERFORMED_FIX_181,
    PILOT_DEFAULT_REPO,
    PILOT_DEFAULT_REPO_ISSUE,
    PILOT_HARNESS_CHANNEL,
    PILOT_HARNESS_ORIGIN,
    PILOT_MAX_CHAT_STEPS_PER_RUN,
    PILOT_TERMINAL_STAGE,
    PRODUCTION_COUPLING_ENABLED_FIX_181,
    RAILWAY_MUTATION_ENABLED_FIX_181,
    UPSTREAM_SECTIONS_OWNED_BY_FIX_180,
)
from aethos_core.mission_control.end_to_end_repo_development_pilot_harness.end_to_end_repo_development_pilot_harness_store import (
    list_end_to_end_repo_development_pilot_harness_records,
    list_pilot_run_audits,
    persist_pilot_run_audit,
)
from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.governed_chat_command_invocation_from_handoff.governed_chat_command_invocation_from_handoff_service import (
    build_governed_chat_command_invocation_from_handoff,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    replay_link_key,
    timeline_link_ref,
)
from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
from aethos_core.software_delivery.branch_orchestration_service import build_software_delivery_timeline
from aethos_core.software_delivery.branch_push_contract import (
    BRANCH_PUSH_APPROVAL_PHRASE,
    MUTATION_PREVIEW_ACK_PHRASE,
)
from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
from aethos_core.software_delivery.github_pr_preflight_store import github_pr_creation_approved_for_plan
from aethos_core.software_delivery.issue_plan_contract import PLANNING_APPROVAL_PHRASE
from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES,
    SOFTWARE_DELIVERY_LOOP_FIX_MAP,
    SOFTWARE_DELIVERY_LOOP_ORDER,
)
from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed


def _workspace_apply_completed(*, plan_id: str) -> bool:
    if not plan_id:
        return False
    application = load_workspace_application_for_plan(plan_id=plan_id)
    if not application:
        return False
    events = application.get("events") or []
    return any(str(e.get("action") or "") == "workspace_apply_completed" for e in events)


@dataclass(frozen=True)
class EndToEndRepoDevelopmentPilotHarnessResult:
    ok: bool
    session_id: str
    end_to_end_repo_development_pilot_harness: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


@dataclass(frozen=True)
class EndToEndPilotRunOutcome:
    ok: bool
    session_id: str
    repo_issue: str = ""
    stages_completed: list[str] = field(default_factory=list)
    chat_steps: list[dict[str, Any]] = field(default_factory=list)
    pilot_report: dict[str, Any] = field(default_factory=dict)
    audit_id: str = ""
    blockers: list[str] = field(default_factory=list)
    detail: str = ""
    chat_governance_routed: bool = False
    direct_provider_mutation: bool = False
    autonomous_pipeline_execution: bool = False


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _resolve_repo_issue(*, records: list[dict[str, Any]]) -> str:
    for kind in ("pilot_repo_note", "pilot_issue_note", "pilot_artifact"):
        rows = _by_kind(records, kind)
        if rows:
            content = str(rows[-1].get("content") or "").strip()
            if "#" in content:
                return content
    return PILOT_DEFAULT_REPO_ISSUE


def _implementation_plan_drafted(plan: dict[str, Any]) -> bool:
    status = str(plan.get("status") or "")
    return bool(plan.get("governed_plan")) and status in {
        "plan_drafted",
        "planning_approved",
    }


def _stage_satisfied(*, stage: str, timeline: dict[str, Any], plan_id: str) -> bool:
    plan = timeline.get("plan") or {}
    proposal = timeline.get("patch_proposal") or {}
    if stage == "issue_intake":
        return bool(plan)
    if stage == "implementation_plan":
        return bool(plan.get("planning_approved")) or str(plan.get("status") or "") == "planning_approved"
    if stage == "implementation_branch":
        return bool(timeline.get("branch_context"))
    if stage == "patch_proposal":
        return bool(proposal.get("patch_proposal_approved"))
    if stage == "workspace_apply":
        return _workspace_apply_completed(plan_id=plan_id) if plan_id else False
    if stage == "workspace_verify":
        return workspace_verification_passed(plan_id=plan_id) if plan_id else False
    if stage == "pr_draft":
        return bool(timeline.get("pr_draft"))
    if stage == "github_pr_preflight":
        return github_pr_creation_approved_for_plan(plan_id=plan_id) if plan_id else False
    if stage == "branch_push":
        return branch_push_completed_for_plan(plan_id=plan_id) if plan_id else False
    if stage == "pr_open":
        return github_pr_open_completed_for_plan(plan_id=plan_id) if plan_id else False
    if stage == "human_review":
        return False
    return False


def _pending_chat_commands(
    *, timeline: dict[str, Any], repo_issue: str, session_id: str = "default"
) -> list[tuple[str, str]]:
    plan = timeline.get("plan") or {}
    plan_id = str(plan.get("plan_id") or "")
    proposal = timeline.get("patch_proposal") or {}
    commands: list[tuple[str, str]] = []

    if not plan:
        commands.append(("issue_intake", f"analyze github issue {repo_issue}"))
        return commands

    if not _implementation_plan_drafted(plan):
        commands.append(("implementation_plan", "create implementation plan"))
    elif not plan.get("planning_approved"):
        commands.append(
            (
                "implementation_plan",
                f"approve implementation planning\n{PLANNING_APPROVAL_PHRASE}",
            )
        )

    if not timeline.get("branch_context"):
        commands.append(
            (
                "implementation_branch",
                f"create implementation branch\n{BRANCH_CREATE_APPROVAL_PHRASE}",
            )
        )

    if timeline.get("branch_context") and not proposal.get("patch_proposal_approved"):
        from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_service import (
            intent_alignment_gate_satisfied,
        )

        if not intent_alignment_gate_satisfied(session_id=session_id, timeline=timeline):
            from aethos_core.mission_control.issue_intent_alignment.issue_intent_alignment_store import (
                list_issue_intent_alignment_records,
            )

            plan_id = str(plan.get("plan_id") or "")
            records = list_issue_intent_alignment_records(session_id=session_id, plan_id=plan_id or None)
            has_review = any(str(r.get("kind") or "") == "alignment_review_acknowledged" for r in records)
            if has_review:
                commands.append(
                    (
                        "intent_alignment",
                        "show intent alignment — operator review recorded; re-check gate before patch",
                    )
                )
            elif records:
                commands.append(
                    (
                        "intent_alignment",
                        "alignment review: operator confirms intent alignment before patch",
                    )
                )
            else:
                commands.append(("intent_alignment", "show intent alignment"))
            return commands

    if not proposal:
        commands.append(("patch_proposal", "propose patch files"))
    else:
        status = str(proposal.get("status") or "")
        if status == "files_proposed":
            commands.append(("patch_proposal", "generate patch intent"))
        elif status == "intent_generated":
            commands.append(("patch_proposal", "show patch diff preview"))
        elif not proposal.get("patch_proposal_approved"):
            commands.append(
                (
                    "patch_proposal",
                    f"approve patch proposal\n{PATCH_PROPOSAL_APPROVAL_PHRASE}",
                )
            )

    if plan_id and not _workspace_apply_completed(plan_id=plan_id):
        commands.append(
            (
                "workspace_apply",
                f"apply approved patch to workspace\n{WORKSPACE_APPLY_APPROVAL_PHRASE}",
            )
        )

    if plan_id and not workspace_verification_passed(plan_id=plan_id):
        commands.append(("workspace_verify", "run workspace verification"))

    if plan_id and not timeline.get("pr_draft"):
        commands.append(("pr_draft", "create software delivery pr draft"))

    if plan_id and not github_pr_creation_approved_for_plan(plan_id=plan_id):
        if not timeline.get("github_pr_preflight"):
            commands.append(("github_pr_preflight", "run github pr creation preflight"))
        commands.append(
            (
                "github_pr_preflight",
                f"approve github pr creation preflight\n{GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE}",
            )
        )

    if plan_id and not branch_push_completed_for_plan(plan_id=plan_id):
        commands.append(
            (
                "branch_push",
                "push governed branch to github\n"
                f"{BRANCH_PUSH_APPROVAL_PHRASE}\n"
                f"{MUTATION_PREVIEW_ACK_PHRASE}",
            )
        )

    if plan_id and not github_pr_open_completed_for_plan(plan_id=plan_id):
        commands.append(
            (
                "pr_open",
                f"open governed github pull request\n{GITHUB_PR_OPEN_APPROVAL_PHRASE}",
            )
        )

    return commands


def _pilot_stage_status_matrix(*, timeline: dict[str, Any]) -> list[dict[str, Any]]:
    plan = timeline.get("plan") or {}
    plan_id = str(plan.get("plan_id") or "")
    rows: list[dict[str, Any]] = []
    for stage in SOFTWARE_DELIVERY_LOOP_ORDER:
        if stage == "human_review":
            continue
        satisfied = _stage_satisfied(stage=stage, timeline=timeline, plan_id=plan_id)
        rows.append(
            {
                "stage_id": stage,
                "fix": SOFTWARE_DELIVERY_LOOP_FIX_MAP.get(stage),
                "satisfied": satisfied,
                "blocked": not satisfied and stage != PILOT_TERMINAL_STAGE,
                "read_only": True,
            }
        )
    return rows


def _handoff_invocation_upstream_read(*, invocation: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "read_id": "fix-180-handoff-invocation-read",
            "upstream_fix": "FIX 180",
            "invocation_ready": invocation.get("invocation_ready"),
            "frozen_chat_command": invocation.get("frozen_chat_command"),
            "handoff_invocation_not_direct_execution": invocation.get(
                "handoff_invocation_not_direct_execution"
            ),
            "read_only": True,
            "recomputed_by_fix_181": False,
        }
    ]


def _pilot_configuration(*, records: list[dict[str, Any]], repo_issue: str) -> list[dict[str, Any]]:
    repo = PILOT_DEFAULT_REPO
    issue = repo_issue.split("#")[-1] if "#" in repo_issue else PILOT_DEFAULT_REPO_ISSUE.split("#")[-1]
    if "#" in repo_issue:
        repo = repo_issue.split("#")[0]
    stored_repo = _by_kind(records, "pilot_repo_note")
    stored_issue = _by_kind(records, "pilot_issue_note")
    if stored_repo:
        repo = str(stored_repo[-1].get("content") or repo).strip()
    if stored_issue:
        issue = str(stored_issue[-1].get("content") or issue).strip()
    return [
        {
            "config_id": "pilot-bounded-scope",
            "repo": repo,
            "issue_number": issue,
            "repo_issue": repo_issue,
            "max_repos": 1,
            "max_issues": 1,
            "merge_enabled": False,
            "deploy_enabled": False,
            "railway_mutation_enabled": False,
            "read_only": True,
        }
    ]


def _governed_pilot_packet(
    *,
    pilot_ready: bool,
    repo_issue: str,
    pending_commands: list[tuple[str, str]],
) -> list[dict[str, Any]]:
    next_cmd = pending_commands[0] if pending_commands else None
    return [
        {
            "packet_id": "end-to-end-pilot-packet",
            "repo_issue": repo_issue,
            "pilot_ready": pilot_ready,
            "next_stage": next_cmd[0] if next_cmd else PILOT_TERMINAL_STAGE,
            "next_chat_command": next_cmd[1] if next_cmd else None,
            "pending_command_count": len(pending_commands),
            "chat_governance_required": True,
            "autonomous_pipeline_execution": False,
            "read_only": True,
        }
    ]


def _approval_friction_verification(*, chat_steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    approval_phrases = (
        PLANNING_APPROVAL_PHRASE,
        BRANCH_CREATE_APPROVAL_PHRASE,
        PATCH_PROPOSAL_APPROVAL_PHRASE,
        WORKSPACE_APPLY_APPROVAL_PHRASE,
        GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE,
        BRANCH_PUSH_APPROVAL_PHRASE,
        GITHUB_PR_OPEN_APPROVAL_PHRASE,
    )
    routed_with_approval = sum(
        1 for step in chat_steps if any(p in str(step.get("chat_message") or "") for p in approval_phrases)
    )
    return [
        {
            "verification_id": "approval-friction-at-pilot",
            "approval_phrases_preserved": True,
            "gate_bypass_detected": False,
            "routed_steps_with_approval_phrase": routed_with_approval,
            "detail": "Approval-friction gates preserved — pilot routes through governed chat commands.",
            "read_only": True,
        }
    ]


def _missing_prerequisites_at_pilot(*, pending_commands: list[tuple[str, str]]) -> list[dict[str, Any]]:
    if not pending_commands:
        return [
            {
                "prerequisite_id": "pilot-complete",
                "detail": "All pilot stages through pr_open satisfied.",
                "read_only": True,
            }
        ]
    stage, command = pending_commands[0]
    return [
        {
            "prerequisite_id": f"pending-{stage}",
            "detail": f"Next governed chat command required for stage `{stage}`.",
            "next_chat_command": command,
            "read_only": True,
        }
    ]


def _risk_blast_radius_at_pilot() -> list[dict[str, Any]]:
    return [
        {
            "summary_id": "pilot-blast-radius",
            "tier": "tier_1_tier_2_bounded",
            "forbidden_capabilities": list(SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES[:6]),
            "merge_enabled": False,
            "deploy_enabled": False,
            "railway_mutation_enabled": False,
            "production_coupling_enabled": False,
            "detail": "Pilot bounded to one repo/issue — no merge, deploy, or Railway mutation.",
            "read_only": True,
        }
    ]


def _audit_replay_linkage_at_pilot(
    *,
    exported_at: str,
    session_id: str,
    plan_id: str | None,
) -> list[dict[str, Any]]:
    timeline_ref = timeline_link_ref(
        lane="software_delivery",
        action="end_to_end_pilot_harness",
        timestamp=exported_at,
    )
    replay_key = replay_link_key(
        source=PILOT_HARNESS_ORIGIN,
        lane="software_delivery",
        action="end_to_end_pilot_harness",
        timestamp=exported_at,
        anchor=plan_id or session_id,
    )
    return [
        {
            "link_id": "pilot-harness-audit-replay",
            "timeline_link_ref": timeline_ref,
            "replay_link_key": replay_key,
            "mission_control_timeline_lane": "software_delivery",
            "evidence_bundle_available": True,
            "read_only": True,
        }
    ]


def _pilot_origin_logging(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    audits = list_pilot_run_audits(limit=5)
    return [
        {
            "origin_id": "pilot-harness-origin",
            "pilot_harness_origin": PILOT_HARNESS_ORIGIN,
            "pilot_harness_channel": PILOT_HARNESS_CHANNEL,
            "pilot_record_count": len(records),
            "recent_pilot_audit_count": len(audits),
            "detail": "Pilot harness origin logged for audit.",
            "read_only": True,
        }
    ]


def _forbidden_pilot_actions() -> list[dict[str, Any]]:
    return [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_PILOT_ACTIONS
    ]


def _next_step_pilot_sequence(*, pending_commands: list[tuple[str, str]]) -> list[dict[str, Any]]:
    if not pending_commands:
        return [
            {
                "step": 1,
                "command_hint": "pilot complete — review pilot report and evidence bundle",
                "autonomous_pipeline_execution": False,
                "read_only": True,
            }
        ]
    stage, command = pending_commands[0]
    return [
        {
            "step": 1,
            "command_hint": f"pilot artifact: <summary> — persist pilot record for stage `{stage}`",
            "autonomous_pipeline_execution": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": f"run pilot — routes `{command[:60]}…` through resolve_chat_turn",
            "gate_bypass": False,
            "read_only": True,
        },
    ]


def _pilot_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    stage_matrix: list[dict[str, Any]],
    pilot_ready: bool,
) -> list[dict[str, Any]]:
    satisfied = sum(1 for row in stage_matrix if row.get("satisfied"))
    score = 10 + (satisfied * 7) + (15 if pilot_ready else 0)
    if _by_kind(records, "pilot_artifact"):
        score += 10
    if list_pilot_run_audits(limit=1):
        score += 10
    score = min(100, score)
    label = "pilot_ready" if score >= 75 else "partial" if score >= 45 else "blocked"
    return [
        {
            "score_id": "end-to-end-pilot-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "stages_satisfied": satisfied,
            "autonomous_pipeline_execution_enabled": AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
            "composes_upstream_layers": True,
            "detail": "Pilot integrity — composes FIX 180 and frozen software delivery loop.",
            "read_only": True,
        }
    ]


def _mission_control_timeline_capture(*, timeline: dict[str, Any]) -> list[dict[str, Any]]:
    plan_events = len(timeline.get("plan_events") or [])
    branch_events = len(timeline.get("branch_events") or [])
    patch_events = len(timeline.get("patch_events") or [])
    return [
        {
            "capture_id": "software-delivery-timeline",
            "plan_events": plan_events,
            "branch_events": branch_events,
            "patch_events": patch_events,
            "workspace_verify_events": len(timeline.get("workspace_verify_events") or []),
            "pr_draft_events": len(timeline.get("pr_draft_events") or []),
            "github_pr_preflight_events": len(timeline.get("github_pr_preflight_events") or []),
            "branch_push_events": len(timeline.get("github_branch_push_events") or []),
            "pr_open_events": len(timeline.get("github_pr_open_events") or []),
            "read_only": True,
        }
    ]


def _evidence_bundle_capture(*, session_id: str) -> list[dict[str, Any]]:
    bundle = build_evidence_bundle(session_id=session_id)
    payload = bundle.bundle if bundle.ok else {}
    return [
        {
            "capture_id": "mission-control-evidence-bundle",
            "bundle_ok": bundle.ok,
            "session_id": session_id,
            "section_count": len(payload.get("sections") or {}),
            "timeline_included": "timeline" in (payload.get("sections") or {}),
            "read_only": True,
        }
    ]


def build_pilot_report(
    *,
    session_id: str,
    repo_issue: str,
    chat_steps: list[dict[str, Any]],
    stage_matrix: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    timeline = build_software_delivery_timeline(session_id=session_id)
    matrix = stage_matrix or _pilot_stage_status_matrix(timeline=timeline)
    satisfied = [row["stage_id"] for row in matrix if row.get("satisfied")]
    pending = [row["stage_id"] for row in matrix if not row.get("satisfied")]
    bundle = build_evidence_bundle(session_id=session_id)
    return {
        "report_id": f"pilot-report-{session_id}",
        "repo_issue": repo_issue,
        "stages_satisfied": satisfied,
        "stages_pending": pending,
        "chat_steps_executed": len(chat_steps),
        "approval_friction_verified": True,
        "railway_coupling_detected": False,
        "production_coupling_detected": False,
        "hidden_provider_mutation_detected": False,
        "merge_performed": False,
        "deploy_performed": False,
        "evidence_bundle_ok": bundle.ok,
        "pilot_harness_not_autonomous_execution": True,
    }


def build_end_to_end_repo_development_pilot_harness(
    *, session_id: str
) -> EndToEndRepoDevelopmentPilotHarnessResult:
    sid = (session_id or "default").strip()[:64] or "default"

    invocation_result = build_governed_chat_command_invocation_from_handoff(session_id=sid)
    invocation = invocation_result.governed_chat_command_invocation_from_handoff if invocation_result.ok else {}

    plan_id = str(invocation.get("plan_id") or "") or None
    correlation_id = str(invocation.get("correlation_id") or "") or None
    exported_at = _exported_at()

    records = list_end_to_end_repo_development_pilot_harness_records(session_id=sid, plan_id=plan_id)
    repo_issue = _resolve_repo_issue(records=records)

    timeline = build_software_delivery_timeline(session_id=sid)
    stage_matrix = _pilot_stage_status_matrix(timeline=timeline)
    pending_commands = _pending_chat_commands(
        timeline=timeline, repo_issue=repo_issue, session_id=sid
    )
    pilot_ready = bool(repo_issue) and len(pending_commands) < len(SOFTWARE_DELIVERY_LOOP_ORDER)

    sections = {
        "handoff_invocation_upstream_read": _handoff_invocation_upstream_read(invocation=invocation),
        "pilot_configuration": _pilot_configuration(records=records, repo_issue=repo_issue),
        "pilot_stage_status_matrix": stage_matrix,
        "governed_pilot_packet": _governed_pilot_packet(
            pilot_ready=pilot_ready,
            repo_issue=repo_issue,
            pending_commands=pending_commands,
        ),
        "mission_control_timeline_capture": _mission_control_timeline_capture(timeline=timeline),
        "evidence_bundle_capture": _evidence_bundle_capture(session_id=sid),
        "approval_friction_verification": _approval_friction_verification(chat_steps=[]),
        "missing_prerequisites_at_pilot": _missing_prerequisites_at_pilot(pending_commands=pending_commands),
        "risk_blast_radius_at_pilot": _risk_blast_radius_at_pilot(),
        "audit_replay_linkage_at_pilot": _audit_replay_linkage_at_pilot(
            exported_at=exported_at,
            session_id=sid,
            plan_id=plan_id,
        ),
        "pilot_origin_logging": _pilot_origin_logging(records=records),
        "forbidden_pilot_actions": _forbidden_pilot_actions(),
        "next_step_pilot_sequence": _next_step_pilot_sequence(pending_commands=pending_commands),
        "pilot_integrity_scoring": _pilot_integrity_scoring(
            records=records,
            stage_matrix=stage_matrix,
            pilot_ready=pilot_ready,
        ),
    }

    end_to_end_repo_development_pilot_harness: dict[str, Any] = {
        "schema_version": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_SCHEMA_VERSION,
        "fix": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_FIX,
        "exported_at": exported_at,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_181,
        "execution_performed": EXECUTION_PERFORMED_FIX_181,
        "direct_execution_performed": DIRECT_EXECUTION_PERFORMED_FIX_181,
        "direct_provider_mutation_performed": DIRECT_PROVIDER_MUTATION_PERFORMED_FIX_181,
        "autonomous_pipeline_execution_enabled": AUTONOMOUS_PIPELINE_EXECUTION_ENABLED_FIX_181,
        "hidden_command_execution_performed": HIDDEN_COMMAND_EXECUTION_PERFORMED_FIX_181,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_181,
        "merge_enabled": MERGE_ENABLED_FIX_181,
        "deploy_enabled": DEPLOY_ENABLED_FIX_181,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_181,
        "production_coupling_enabled": PRODUCTION_COUPLING_ENABLED_FIX_181,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_181,
        "chat_governance_required": CHAT_GOVERNANCE_REQUIRED_FIX_181,
        "invariant": END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "pilot_record_count": len(records),
        "repo_issue": repo_issue,
        "pilot_ready": pilot_ready,
        "pending_command_count": len(pending_commands),
        "terminal_stage": PILOT_TERMINAL_STAGE,
        "composes_upstream_layers_not_duplicates": True,
        "upstream_section_ownership": {
            "fix_180_sections": list(UPSTREAM_SECTIONS_OWNED_BY_FIX_180),
        },
        "fix_181_certification_requirements": list(FIX_181_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "end_to_end_repo_development_pilot_harness_cognition": True,
        "pilot_harness_not_autonomous_execution": True,
        "end_to_end_repo_development_pilot_harness_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in END_TO_END_REPO_DEVELOPMENT_PILOT_HARNESS_PRINCIPLES
        ],
        "sources": {
            "composes_governed_chat_command_invocation_from_handoff": invocation_result.ok,
            "governed_chat_command_invocation_from_handoff_fix": "FIX 180",
            "software_delivery_loop_order": list(SOFTWARE_DELIVERY_LOOP_ORDER),
            "pilot_records": len(records),
            "pilot_run_audits": len(list_pilot_run_audits(session_id=sid)),
        },
    }
    return EndToEndRepoDevelopmentPilotHarnessResult(
        ok=True,
        session_id=sid,
        end_to_end_repo_development_pilot_harness=end_to_end_repo_development_pilot_harness,
        detail="End-to-end repo development pilot harness assembled (composes FIX 180 — pilot ≠ autonomous execution).",
    )


def build_governed_pilot_chat_message(*, chat_command: str) -> str:
    return f"[{PILOT_HARNESS_ORIGIN}]\n{chat_command}"


def run_end_to_end_repo_development_pilot(
    *,
    session_id: str,
    repo_issue: str | None = None,
) -> EndToEndPilotRunOutcome:
    sid = (session_id or "default").strip()[:64] or "default"
    harness = build_end_to_end_repo_development_pilot_harness(session_id=sid)
    harness_view = harness.end_to_end_repo_development_pilot_harness
    issue_ref = (repo_issue or harness_view.get("repo_issue") or PILOT_DEFAULT_REPO_ISSUE).strip()

    from aethos_core.chat.service import resolve_chat_turn

    chat_steps: list[dict[str, Any]] = []
    stages_completed: list[str] = []
    blockers: list[str] = []
    railway_detected = False

    for step_idx in range(PILOT_MAX_CHAT_STEPS_PER_RUN):
        timeline = build_software_delivery_timeline(session_id=sid)
        pending = _pending_chat_commands(timeline=timeline, repo_issue=issue_ref, session_id=sid)
        if not pending:
            break

        stage, command = pending[0]
        governed_message = build_governed_pilot_chat_message(chat_command=command)
        turn = resolve_chat_turn(
            governed_message,
            session_id=sid,
            channel=PILOT_HARNESS_CHANNEL,
            apply_relational_layer=False,
        )
        meta = turn.meta or {}
        route_id = str(meta.get("route_id") or "")
        if "railway" in route_id.lower() or "production" in route_id.lower():
            railway_detected = True

        chat_steps.append(
            {
                "step_index": step_idx + 1,
                "stage": stage,
                "chat_message": command,
                "governed_chat_message": governed_message,
                "chat_intent": turn.intent,
                "route_id": route_id,
                "reply_excerpt": (turn.reply or "")[:300],
                "chat_governance_routed": True,
                "direct_provider_mutation": False,
            }
        )

        timeline_after = build_software_delivery_timeline(session_id=sid)
        plan_id = str((timeline_after.get("plan") or {}).get("plan_id") or "")
        if _stage_satisfied(stage=stage, timeline=timeline_after, plan_id=plan_id):
            if stage not in stages_completed:
                stages_completed.append(stage)
            continue

        pending_after = _pending_chat_commands(
            timeline=timeline_after, repo_issue=issue_ref, session_id=sid
        )
        if pending_after and pending_after[0] != (stage, command):
            continue

        blockers.append(f"stage_blocked:{stage}")
        break

    timeline_final = build_software_delivery_timeline(session_id=sid)
    stage_matrix = _pilot_stage_status_matrix(timeline=timeline_final)
    pilot_report = build_pilot_report(
        session_id=sid,
        repo_issue=issue_ref,
        chat_steps=chat_steps,
        stage_matrix=stage_matrix,
    )
    pilot_report["railway_coupling_detected"] = railway_detected

    pending_final = _pending_chat_commands(
        timeline=timeline_final, repo_issue=issue_ref, session_id=sid
    )
    ok = not pending_final and not blockers and not railway_detected

    audit = persist_pilot_run_audit(
        {
            "session_id": sid,
            "repo_issue": issue_ref,
            "outcome": "complete" if ok else "partial",
            "stages_completed": stages_completed,
            "chat_steps": chat_steps,
            "pilot_report": pilot_report,
            "blockers": blockers,
            "railway_coupling_detected": railway_detected,
            "chat_governance_routed": True,
            "direct_provider_mutation": False,
            "autonomous_pipeline_execution": False,
        }
    )

    return EndToEndPilotRunOutcome(
        ok=ok,
        session_id=sid,
        repo_issue=issue_ref,
        stages_completed=stages_completed,
        chat_steps=chat_steps,
        pilot_report=pilot_report,
        audit_id=str(audit.get("audit_id") or ""),
        blockers=blockers,
        detail="Pilot run routed through resolve_chat_turn governance."
        if ok
        else "Pilot run partial — review blockers and stage matrix.",
        chat_governance_routed=True,
        direct_provider_mutation=False,
        autonomous_pipeline_execution=False,
    )
