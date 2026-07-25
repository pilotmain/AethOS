# SPDX-License-Identifier: Apache-2.0
"""FIX 132 — cross-lane pending approval inbox (read-only)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_execution_contract import ui_approval_eligible
from aethos_core.mission_control.approval_inbox.approval_phrase_templates import build_copy_phrase_text
from aethos_core.mission_control.approval_inbox.approval_inbox_contract import (
    APPROVAL_EXECUTION_ENABLED_FIX_133,
    APPROVAL_INBOX_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_132,
    SEVERITY_ORDER,
)
from aethos_core.software_delivery.issue_plan_contract import (
    BLOCKED_ACTIONS_FIX_125A,
    PLANNING_APPROVAL_PHRASE,
)
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES,
)

_SEVERITY_RANK = {s: i for i, s in enumerate(SEVERITY_ORDER)}


@dataclass(frozen=True)
class ApprovalInboxResult:
    ok: bool
    session_id: str
    items: list[dict[str, Any]] = field(default_factory=list)
    groups: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    detail: str = ""


def _item(
    *,
    inbox_id: str,
    lane: str,
    gate_id: str,
    title: str,
    severity: str,
    required_phrases: list[str],
    unlocks: list[str],
    remains_forbidden: list[str],
    risk_tier: str,
    blast_radius: dict[str, Any],
    approval_surface: str = "chat",
    context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    eligible = ui_approval_eligible(lane=lane, gate_id=gate_id)
    copy_text = build_copy_phrase_text(gate_id=gate_id, required_phrases=required_phrases) if eligible else ""
    return {
        "inbox_id": inbox_id,
        "lane": lane,
        "gate_id": gate_id,
        "title": title,
        "severity": severity,
        "required_phrases": required_phrases,
        "unlocks": unlocks,
        "remains_forbidden": remains_forbidden,
        "risk_tier": risk_tier,
        "blast_radius": blast_radius,
        "approval_surface": approval_surface,
        "ui_approval_eligible": eligible,
        "copy_phrase_text": copy_text,
        "approval_execution_enabled": eligible and APPROVAL_EXECUTION_ENABLED_FIX_133,
        "execution_mode": "chat_governance_route" if eligible else "view_only_chat_required",
        "mutation_performed": False,
        "context": context or {},
    }


def _sd_forbidden() -> list[str]:
    return list(SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES[:8]) + list(BLOCKED_ACTIONS_FIX_125A[:4])


def _collect_software_delivery_approvals(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.software_delivery.branch_orchestration_contract import BRANCH_CREATE_APPROVAL_PHRASE
    from aethos_core.software_delivery.branch_orchestration_store import load_branch_context_for_plan
    from aethos_core.software_delivery.branch_push_contract import (
        BRANCH_PUSH_APPROVAL_PHRASE,
        MUTATION_PREVIEW_ACK_PHRASE,
    )
    from aethos_core.software_delivery.branch_push_store import branch_push_completed_for_plan
    from aethos_core.software_delivery.github_pr_open_contract import GITHUB_PR_OPEN_APPROVAL_PHRASE
    from aethos_core.software_delivery.github_pr_open_store import github_pr_open_completed_for_plan
    from aethos_core.software_delivery.github_pr_preflight_contract import GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE
    from aethos_core.software_delivery.github_pr_preflight_store import (
        github_pr_creation_approved_for_plan,
        load_github_pr_preflight_for_plan,
    )
    from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
    from aethos_core.software_delivery.patch_proposal_contract import PATCH_PROPOSAL_APPROVAL_PHRASE
    from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
    from aethos_core.software_delivery.workspace_application_contract import WORKSPACE_APPLY_APPROVAL_PHRASE
    from aethos_core.software_delivery.workspace_application_store import load_workspace_application_for_plan
    from aethos_core.software_delivery.workspace_verification_store import workspace_verification_passed

    plan = load_issue_plan_for_session(session_id=session_id)
    if not plan:
        return []

    plan_id = str(plan.get("plan_id") or "")
    items: list[dict[str, Any]] = []
    forbidden = _sd_forbidden()
    repo = str(plan.get("repository") or "governed repo")

    if str(plan.get("status") or "") != "planning_approved":
        items.append(
            _item(
                inbox_id=f"sd-planning-{plan_id}",
                lane="software_delivery",
                gate_id="planning_approved",
                title="Approve implementation plan",
                severity="medium",
                required_phrases=[PLANNING_APPROVAL_PHRASE],
                unlocks=["implementation branch orchestration", "patch proposal lane"],
                remains_forbidden=forbidden,
                risk_tier="medium",
                blast_radius={
                    "scope": "planning_commitment",
                    "repository": repo,
                    "files_mutated": 0,
                    "description": "Commits operator to governed delivery plan — no code mutation yet.",
                },
                context={"plan_id": plan_id, "plan_status": plan.get("status")},
            )
        )

    branch = load_branch_context_for_plan(plan_id=plan_id) if plan_id else None
    if str(plan.get("status") or "") == "planning_approved" and not branch:
        items.append(
            _item(
                inbox_id=f"sd-branch-{plan_id}",
                lane="software_delivery",
                gate_id="branch_create",
                title="Authorize governed implementation branch",
                severity="medium",
                required_phrases=[BRANCH_CREATE_APPROVAL_PHRASE],
                unlocks=["patch proposal", "governed workspace path"],
                remains_forbidden=forbidden,
                risk_tier="medium",
                blast_radius={
                    "scope": "workspace_allocation",
                    "repository": repo,
                    "description": "Creates isolated workspace + branch context only.",
                },
                context={"plan_id": plan_id},
            )
        )

    proposal = load_patch_proposal_for_plan(plan_id=plan_id) if plan_id else None
    if branch and proposal and not proposal.get("patch_proposal_approved") and not proposal.get("unified_diffs"):
        items.append(
            _item(
                inbox_id=f"sd-patch-prep-{plan_id}",
                lane="software_delivery",
                gate_id="patch_proposal_prerequisites",
                title="Complete patch proposal before approval",
                severity="medium",
                required_phrases=[],
                unlocks=["patch proposal approval"],
                remains_forbidden=forbidden,
                risk_tier="medium",
                blast_radius={
                    "scope": "bounded_patch",
                    "repository": repo,
                    "file_count": len(proposal.get("proposed_files") or []),
                    "description": "Run propose patch files → generate patch intent → show diff preview before approval.",
                },
                approval_surface="chat",
                context={
                    "plan_id": plan_id,
                    "proposal_id": proposal.get("proposal_id"),
                    "prerequisite_steps": [
                        "propose patch files",
                        "generate patch intent",
                        "show patch diff preview",
                    ],
                },
            )
        )
        row = items[-1]
        row["ui_approval_eligible"] = False
        row["execution_mode"] = "prerequisites_required"
        row["approval_execution_enabled"] = False

    if branch and proposal and not proposal.get("patch_proposal_approved") and proposal.get("unified_diffs"):
        items.append(
            _item(
                inbox_id=f"sd-patch-{plan_id}",
                lane="software_delivery",
                gate_id="patch_proposal_approved",
                title="Approve patch proposal",
                severity="high",
                required_phrases=[PATCH_PROPOSAL_APPROVAL_PHRASE],
                unlocks=["workspace apply (governed tree only)"],
                remains_forbidden=forbidden,
                risk_tier="high",
                blast_radius={
                    "scope": "bounded_patch",
                    "repository": repo,
                    "file_count": len(proposal.get("proposed_files") or []),
                    "diff_count": len(proposal.get("unified_diffs") or []),
                    "description": "Approves diff intent — still no GitHub mutation until later gates.",
                },
                context={"plan_id": plan_id, "proposal_id": proposal.get("proposal_id")},
            )
        )

    workspace = load_workspace_application_for_plan(plan_id=plan_id) if plan_id else None
    if proposal and proposal.get("patch_proposal_approved") and str((workspace or {}).get("status") or "") != "applied":
        items.append(
            _item(
                inbox_id=f"sd-workspace-apply-{plan_id}",
                lane="software_delivery",
                gate_id="workspace_apply",
                title="Authorize workspace patch application",
                severity="high",
                required_phrases=[WORKSPACE_APPLY_APPROVAL_PHRASE],
                unlocks=["workspace verification", "PR draft lane"],
                remains_forbidden=forbidden,
                risk_tier="high",
                blast_radius={
                    "scope": "governed_workspace_write",
                    "repository": repo,
                    "description": "Writes approved patch into governed workspace only — not remote repo.",
                },
                context={"plan_id": plan_id},
            )
        )

    if plan_id and workspace_verification_passed(plan_id=plan_id):
        preflight = load_github_pr_preflight_for_plan(plan_id=plan_id)
        if preflight and not github_pr_creation_approved_for_plan(plan_id=plan_id):
            items.append(
                _item(
                    inbox_id=f"sd-preflight-{plan_id}",
                    lane="software_delivery",
                    gate_id="github_preflight_approved",
                    title="Approve GitHub PR preflight",
                    severity="high",
                    required_phrases=[GITHUB_PR_PREFLIGHT_APPROVAL_PHRASE],
                    unlocks=["governed branch push (125H)", "mutation preview ack path"],
                    remains_forbidden=forbidden + ["ungoverned_github_push"],
                    risk_tier="high",
                    blast_radius={
                        "scope": "github_mutation_preflight",
                        "repository": repo,
                        "description": "Authorizes governed GitHub path after read-only preflight checks.",
                    },
                    context={"plan_id": plan_id, "preflight_id": preflight.get("preflight_id")},
                )
            )

        if github_pr_creation_approved_for_plan(plan_id=plan_id) and not branch_push_completed_for_plan(plan_id=plan_id):
            items.append(
                _item(
                    inbox_id=f"sd-branch-push-{plan_id}",
                    lane="software_delivery",
                    gate_id="branch_push_completed",
                    title="Authorize governed GitHub branch push",
                    severity="critical",
                    required_phrases=[BRANCH_PUSH_APPROVAL_PHRASE, MUTATION_PREVIEW_ACK_PHRASE],
                    unlocks=["governed PR open (125I)", "human review PR"],
                    remains_forbidden=forbidden + ["direct_main_push", "auto_merge"],
                    risk_tier="critical",
                    blast_radius={
                        "scope": "github_feature_branch_push",
                        "repository": repo,
                        "protected_branches": ["main", "master"],
                        "description": "First GitHub mutation — feature branch only with scope recheck.",
                    },
                    context={"plan_id": plan_id},
                )
            )

        if branch_push_completed_for_plan(plan_id=plan_id) and not github_pr_open_completed_for_plan(plan_id=plan_id):
            items.append(
                _item(
                    inbox_id=f"sd-pr-open-{plan_id}",
                    lane="software_delivery",
                    gate_id="github_pr_opened",
                    title="Authorize opening governed GitHub pull request",
                    severity="critical",
                    required_phrases=[GITHUB_PR_OPEN_APPROVAL_PHRASE],
                    unlocks=["human_review on GitHub"],
                    remains_forbidden=forbidden + ["autonomous_merge", "autonomous_pr_approval"],
                    risk_tier="critical",
                    blast_radius={
                        "scope": "github_pr_create",
                        "repository": repo,
                        "description": "Opens PR for human review — merge remains forbidden.",
                    },
                    context={"plan_id": plan_id},
                )
            )

    return items


def _collect_governed_execution_approvals(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.jobs.job_approval_guidance import list_pending_mutation_approvals

    items: list[dict[str, Any]] = []
    for guidance in list_pending_mutation_approvals(session_id=None, limit=30):
        job_id = str(guidance.get("job_id") or "")
        risk = str(guidance.get("risk_tier") or "high")
        severity = "critical" if risk == "critical" else "high"
        blast = guidance.get("blast_radius") if isinstance(guidance.get("blast_radius"), dict) else {}
        items.append(
            _item(
                inbox_id=f"job-{job_id}",
                lane="governed_execution",
                gate_id=str(guidance.get("job_type") or "mutation_preflight"),
                title=f"Mutation approval: {guidance.get('provider') or 'provider'} {guidance.get('operation_type') or 'operation'}",
                severity=severity,
                required_phrases=[
                    str(guidance.get("approval_action_label") or "Approve in Mission Control or chat guidance surface")
                ],
                unlocks=[str(guidance.get("post_approval_behavior") or "execute_governed_mutation")],
                remains_forbidden=[
                    "ungoverned_provider_mutation",
                    "bypass_preflight",
                    "auto_execute_without_receipt",
                ],
                risk_tier=risk,
                blast_radius={
                    **blast,
                    "target": guidance.get("target_name"),
                    "description": guidance.get("latest_summary") or guidance.get("next_step") or "",
                },
                approval_surface=str(guidance.get("approval_surface") or "mission_control_jobs"),
                context={
                    "job_id": job_id,
                    "job_type": guidance.get("job_type"),
                    "review_items": guidance.get("review_items"),
                    "rollback_plan": guidance.get("rollback_plan"),
                },
            )
        )
        row = items[-1]
        from aethos_core.config import get_settings

        row["mutation_inbox_execution_enabled"] = get_settings().mutation_execution_enabled
        row["execution_mode"] = "mutation_governed_execute"
        row["approval_execution_enabled"] = get_settings().mutation_execution_enabled
        row["approval_surface"] = "mission_control_approval_inbox"
    return items


def _group_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_lane: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        lane = str(item.get("lane") or "unknown")
        by_lane.setdefault(lane, []).append(item)

    groups: list[dict[str, Any]] = []
    for lane in sorted(by_lane.keys()):
        lane_items = sorted(
            by_lane[lane],
            key=lambda i: _SEVERITY_RANK.get(str(i.get("severity") or "low"), 99),
        )
        top_severity = str(lane_items[0].get("severity") or "low") if lane_items else "low"
        groups.append(
            {
                "lane": lane,
                "severity": top_severity,
                "count": len(lane_items),
                "items": lane_items,
            }
        )
    groups.sort(key=lambda g: _SEVERITY_RANK.get(str(g.get("severity") or "low"), 99))
    return groups


def _collect_workspace_terminal_approvals(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.workspace_runtime.terminal.terminal_preflight_store import list_terminal_preflights

    items: list[dict[str, Any]] = []
    for row in list_terminal_preflights(limit=30):
        if str(row.get("status") or "") != "pending_approval":
            continue
        if row.get("executed_at"):
            continue
        preflight_id = str(row.get("preflight_id") or "")
        if not preflight_id:
            continue
        command = str(row.get("command") or "")[:120]
        items.append(
            _item(
                inbox_id=f"tpf-{preflight_id}",
                lane="workspace_terminal",
                gate_id="terminal_execute",
                title=f"Terminal: {command or preflight_id}",
                severity="high",
                required_phrases=[f"Approve terminal execution: {command}"],
                unlocks=["bounded terminal output", "linked subagent follow-up via agent_send"],
                remains_forbidden=[
                    "ungoverned_shell",
                    "auto_execute_without_approval",
                    "merge_to_main",
                ],
                risk_tier="high",
                blast_radius={
                    "scope": "bounded_terminal",
                    "command": command,
                    "cwd": row.get("cwd"),
                    "description": "Runs allowlisted command in workspace after explicit approval.",
                },
                approval_surface="mission_control_approval_inbox",
                context={
                    "preflight_id": preflight_id,
                    "command": row.get("command"),
                    "cwd": row.get("cwd"),
                    "parent_session_id": session_id,
                },
            )
        )
        # Mark terminal items as UI-executable via dedicated endpoint (not chat phrases).
        items[-1]["ui_approval_eligible"] = False
        items[-1]["terminal_execution_enabled"] = True
        items[-1]["execution_mode"] = "terminal_governed_execute"
        items[-1]["approval_execution_enabled"] = True
    return items


def _collect_model_serve_approvals(*, session_id: str) -> list[dict[str, Any]]:
    from aethos_core.workspace_suite import model_foundry as foundry

    autostart = foundry.autostart_enabled()
    autodownload = foundry.autodownload_enabled()

    items: list[dict[str, Any]] = []
    for row in foundry.list_pending_serve_requests():
        req_id = str(row.get("id") or "")
        if not req_id:
            continue
        model_id = str(row.get("model_id") or "")
        label = str(row.get("label") or model_id)
        bind = str(row.get("bind") or "127.0.0.1")
        port = int(row.get("port") or 11434)
        min_gb = foundry.min_gb_for(model_id) or 0.0

        # Approval is the consent gate: when a convenience flag is on, the action it
        # authorizes moves from "remains forbidden" to "approval unlocks" so the
        # operator sees exactly what approving will do. external_bind /
        # ungoverned_serve are forbidden regardless of flags.
        unlocks = ["loopback model server", "chat model picker entry"]
        forbidden: list[str] = []
        if autodownload:
            unlocks.append(f"download model weights (~{min_gb:.0f} GB)")
        else:
            forbidden.append("auto_download_weights")
        if autostart:
            unlocks.append("start loopback runtime")
        else:
            forbidden.append("runtime_autostart")
        forbidden += ["external_bind", "ungoverned_serve"]

        if autostart or autodownload:
            actions = []
            if autostart:
                actions.append("start a loopback runtime if none is running")
            if autodownload:
                actions.append(f"download ~{min_gb:.0f} GB of weights if not present")
            description = (
                "Approving authorizes AethOS to "
                + " and ".join(actions)
                + ", then serve loopback-only; no external exposure; stop = kill process."
            )
        else:
            description = (
                "Verifies a loopback-only local model server is present; no external exposure; "
                "no download or process start; stop = kill process."
            )

        items.append(
            _item(
                inbox_id=f"msf-{req_id}",
                lane="model_foundry",
                gate_id="model_serve",
                title=f"Serve local model: {label}",
                severity="medium",
                required_phrases=[f"Approve local model serve: {model_id}"],
                unlocks=unlocks,
                remains_forbidden=forbidden,
                risk_tier="medium",
                blast_radius={
                    "scope": "loopback_model_serve",
                    "model_id": model_id,
                    "bind": bind,
                    "port": port,
                    "autostart": autostart,
                    "autodownload": autodownload,
                    "download_gb": min_gb if autodownload else 0,
                    "description": description,
                },
                approval_surface="mission_control_approval_inbox",
                context={
                    "serve_request_id": req_id,
                    "model_id": model_id,
                    "bind": bind,
                    "port": port,
                },
            )
        )
        # Executable via dedicated endpoint (not chat phrases), mirroring terminal items.
        items[-1]["ui_approval_eligible"] = False
        items[-1]["serve_execution_enabled"] = True
        items[-1]["execution_mode"] = "model_serve_governed_execute"
        items[-1]["approval_execution_enabled"] = True
    return items


def _deployment_execution_state_for_job(job: Any) -> tuple[bool, str]:
    """Re-assess whether greenfield deployment can execute (not planning-only)."""
    from aethos_core.config import get_settings
    from aethos_core.provider_e2e_execution.job_taxonomy import PROVIDER_E2E_ORCHESTRATION_JOB_TYPE
    from aethos_core.providers.railway.execution_contract.execution_enablement import (
        assess_railway_execution_enablement_policy,
    )
    from aethos_core.providers.railway.greenfield_deployment.greenfield_preflight import (
        RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE,
    )
    from aethos_core.providers.vercel.greenfield_deployment.greenfield_preflight import (
        VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE,
    )

    params = dict(getattr(job, "params", None) or {})
    job_type = str(getattr(job, "job_type", "") or "")
    provider = str(params.get("provider") or "")

    if job_type == RAILWAY_GREENFIELD_PREFLIGHT_JOB_TYPE:
        plan = dict(params.get("target_plan") or {})
        enablement = assess_railway_execution_enablement_policy(
            plan=plan,
            user_text=str(params.get("user_request") or ""),
        )
        if enablement.allows_real_mutation():
            return True, ""
        return False, "Enable Railway greenfield execution to deploy."

    if job_type == VERCEL_GREENFIELD_PREFLIGHT_JOB_TYPE:
        settings = get_settings()
        if settings.vercel_greenfield_execution_enabled and settings.mutation_execution_enabled:
            return True, ""
        return False, "Enable Vercel greenfield execution to deploy."

    if job_type == PROVIDER_E2E_ORCHESTRATION_JOB_TYPE:
        settings = get_settings()
        if settings.mutation_execution_enabled:
            return True, ""
        return False, "Enable mutation execution to run provider orchestration."

    if provider == "railway":
        return False, "Enable Railway greenfield execution to deploy."
    if provider == "vercel":
        return False, "Enable Vercel greenfield execution to deploy."
    return bool(get_settings().mutation_execution_enabled), ""


def _collect_operational_deployment_approvals() -> list[dict[str, Any]]:
    """Railway/Vercel greenfield preflight jobs — tenant-wide, not panel session id."""
    from aethos_core.jobs.pending_job_approval_resolution import list_pending_operational_approvals
    from aethos_core.runtime.jobs import job_store

    items: list[dict[str, Any]] = []
    for row in list_pending_operational_approvals(session_id=None):
        risk = "high"
        blast = {}
        if row.remembered:
            blast = dict(row.remembered.get("metadata") or {})
        job = job_store.get(row.job_id)
        deployment_enabled, disabled_hint = _deployment_execution_state_for_job(job) if job else (False, "")
        chat_phrase = f"approve {row.job_id}"
        items.append(
            _item(
                inbox_id=f"job-{row.job_id}",
                lane="operational_deployment",
                gate_id=row.job_type,
                title=row.label or row.job_type.replace("_", " "),
                severity="critical" if row.job_type.endswith("preflight") else "high",
                required_phrases=[chat_phrase],
                unlocks=["governed Railway/Vercel deployment execution"],
                remains_forbidden=[
                    "ungoverned_provider_mutation",
                    "bypass_preflight",
                    "auto_execute_without_receipt",
                ],
                risk_tier=risk,
                blast_radius={
                    **blast,
                    "preflight_id": row.preflight_id,
                    "description": row.label,
                },
                approval_surface="mission_control_approvals",
                context={
                    "job_id": row.job_id,
                    "job_type": row.job_type,
                    "provider": row.provider,
                    "approval_route": row.approval_route,
                    "chat_session_id": row.remembered.get("session_id"),
                },
            )
        )
        items[-1]["ui_approval_eligible"] = False
        items[-1]["approval_execution_enabled"] = True
        items[-1]["deployment_inbox_execution_enabled"] = True
        items[-1]["deployment_execution_enabled"] = deployment_enabled
        items[-1]["deployment_execution_hint"] = disabled_hint or "Enable Railway greenfield execution to deploy."
        items[-1]["execution_mode"] = "operational_deployment_approve"
    return items


def build_approval_inbox(*, session_id: str) -> ApprovalInboxResult:
    from aethos_core.mission_control.cross_lane.snapshot_service import load_mission_control_config

    cfg = load_mission_control_config()
    if not cfg.get("enabled"):
        return ApprovalInboxResult(
            ok=False,
            session_id=session_id,
            detail="mission_control_disabled",
        )

    items = (
        _collect_software_delivery_approvals(session_id=session_id)
        + _collect_governed_execution_approvals(session_id=session_id)
        + _collect_operational_deployment_approvals()
        + _collect_workspace_terminal_approvals(session_id=session_id)
        + _collect_model_serve_approvals(session_id=session_id)
    )
    groups = _group_items(items)
    by_severity: dict[str, int] = {}
    for item in items:
        sev = str(item.get("severity") or "low")
        by_severity[sev] = by_severity.get(sev, 0) + 1

    return ApprovalInboxResult(
        ok=True,
        session_id=session_id,
        items=items,
        groups=groups,
        summary={
            "total_pending": len(items),
            "by_severity": by_severity,
            "lanes_with_pending": len(groups),
            "mutation_performed": MUTATION_PERFORMED_FIX_132,
            "approval_execution_enabled": APPROVAL_EXECUTION_ENABLED_FIX_133,
            "ui_eligible_count": sum(1 for i in items if i.get("ui_approval_eligible")),
        },
        detail="Pending approvals aggregated across lanes. UI may execute eligible gates via governed chat only.",
    )


def approval_inbox_payload(*, session_id: str) -> dict[str, Any]:
    result = build_approval_inbox(session_id=session_id)
    if not result.ok:
        return {"ok": False, "session_id": session_id, "blockers": [result.detail]}
    return {
        "ok": True,
        "read_only": True,
        "schema_version": APPROVAL_INBOX_SCHEMA_VERSION,
        "session_id": result.session_id,
        "detail": result.detail,
        "summary": result.summary,
        "items": result.items,
        "groups": result.groups,
    }
