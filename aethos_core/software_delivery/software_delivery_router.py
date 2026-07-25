# SPDX-License-Identifier: Apache-2.0
"""Unified software delivery router — FIX 125A–127."""

from __future__ import annotations

from aethos_core.software_delivery.branch_orchestration_renderer import (
    render_branch_blocked,
    render_branch_status,
    render_software_delivery_timeline,
)
from aethos_core.software_delivery.branch_orchestration_service import (
    archive_implementation_branch,
    build_software_delivery_timeline,
    create_implementation_branch,
    is_branch_orchestration_intent,
    restore_implementation_branch,
)
from aethos_core.software_delivery.branch_orchestration_store import (
    load_branch_context_for_plan,
)
from aethos_core.software_delivery.issue_plan_contract import SOFTWARE_DELIVERY_LANE_ID
from aethos_core.software_delivery.issue_plan_router import route_software_delivery_issue_plan
from aethos_core.software_delivery.issue_plan_store import load_issue_plan_for_session
from aethos_core.software_delivery.patch_proposal_renderer import (
    render_diff_preview,
    render_patch_intent,
    render_patch_proposal_blocked,
    render_patch_proposal_status,
    render_proposed_files,
)
from aethos_core.software_delivery.patch_proposal_service import (
    approve_patch_proposal,
    generate_patch_intent,
    is_patch_proposal_intent,
    propose_patch_files,
    show_patch_diff_preview,
)
from aethos_core.software_delivery.patch_proposal_store import load_patch_proposal_for_plan
from aethos_core.software_delivery.workspace_application_renderer import (
    render_governed_workspace_diff,
    render_workspace_apply_blocked,
    render_workspace_apply_status,
)
from aethos_core.software_delivery.workspace_application_service import (
    apply_approved_patch_to_workspace,
    is_workspace_application_intent,
    rollback_workspace_changes,
    show_governed_workspace_diff,
    show_workspace_apply_status,
)
from aethos_core.software_delivery.workspace_verification_renderer import (
    render_verification_blocked,
    render_verification_report,
    render_verification_status,
)
from aethos_core.software_delivery.branch_push_renderer import (
    render_branch_push_blocked,
    render_branch_push_report,
    render_branch_push_status,
)
from aethos_core.software_delivery.branch_push_service import (
    is_branch_push_intent,
    push_governed_branch_to_github,
    show_branch_push,
)
from aethos_core.software_delivery.github_pr_open_renderer import (
    render_github_pr_open_blocked,
    render_github_pr_open_report,
    render_github_pr_open_status,
)
from aethos_core.software_delivery.github_pr_open_service import (
    is_github_pr_open_intent,
    open_governed_github_pull_request,
    show_github_pr_open,
)
from aethos_core.software_delivery.multi_agent.multi_agent_renderer import (
    render_collaboration_blocked,
    render_collaboration_report,
    render_collaboration_status,
)
from aethos_core.software_delivery.multi_agent.multi_agent_service import (
    is_multi_agent_collaboration_intent,
    run_agent_collaboration,
    show_agent_collaboration,
)
from aethos_core.software_delivery.github_pr_preflight_renderer import (
    render_preflight_blocked,
    render_preflight_report,
    render_preflight_status,
)
from aethos_core.software_delivery.github_pr_preflight_service import (
    approve_github_pr_creation_preflight,
    is_github_pr_preflight_intent,
    run_github_pr_creation_preflight,
    show_github_pr_preflight,
)
from aethos_core.software_delivery.pr_draft_renderer import (
    render_pr_draft,
    render_pr_draft_blocked,
    render_pr_draft_status,
)
from aethos_core.software_delivery.pr_draft_service import (
    create_software_delivery_pr_draft,
    is_pr_draft_intent,
    show_pr_draft,
)
from aethos_core.software_delivery.workspace_verification_service import (
    is_workspace_verification_intent,
    run_workspace_verification,
    show_workspace_verification_status,
)


def _meta(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    return {
        "route_id": SOFTWARE_DELIVERY_LANE_ID,
        "matched_module": "software_delivery.software_delivery_router",
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
        "software_delivery_stage": stage,
        "lane_separation": "software_delivery_not_infra",
        **extra,
    }


def _meta_workspace(session_id: str, *, stage: str, workspace_write: bool = False, **extra: str) -> dict[str, str]:
    base = _meta(session_id, stage=stage, **extra)
    base["mutation_scope"] = "governed_workspace_only"
    base["workspace_write_performed"] = "true" if workspace_write else "false"
    base["repo_mutation_performed"] = "false"
    base["git_mutation_performed"] = "false"
    if workspace_write:
        base["readonly"] = "false"
    return base


def _meta_github_branch_push(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    base = _meta(session_id, stage=stage, **extra)
    base["readonly"] = "false"
    base["mutation_performed"] = "true"
    base["mutation_scope"] = "feature_branch_push_only"
    base["github_mutation_performed"] = "true"
    base["git_mutation_performed"] = "true"
    base["repo_mutation_performed"] = "true"
    base["github_pr_create_performed"] = "false"
    base["merge_performed"] = "false"
    base["deploy_performed"] = "false"
    return base


def _meta_github_pr_open(session_id: str, *, stage: str, **extra: str) -> dict[str, str]:
    base = _meta(session_id, stage=stage, **extra)
    base["readonly"] = "false"
    base["mutation_performed"] = "true"
    base["mutation_scope"] = "github_pr_open_only"
    base["github_mutation_performed"] = "true"
    base["github_pr_create_performed"] = "true"
    base["git_mutation_performed"] = "false"
    base["repo_mutation_performed"] = "true"
    base["merge_performed"] = "false"
    base["deploy_performed"] = "false"
    base["railway_mutation_performed"] = "false"
    base["human_review_required"] = "true"
    return base


def is_software_delivery_intent(text: str) -> bool:
    from aethos_core.software_delivery.issue_plan_service import (
        is_software_delivery_issue_plan_intent,
    )

    raw = (text or "").strip()
    return (
        is_software_delivery_issue_plan_intent(raw)
        or is_branch_orchestration_intent(raw)
        or is_patch_proposal_intent(raw)
        or is_workspace_application_intent(raw)
        or is_workspace_verification_intent(raw)
        or is_pr_draft_intent(raw)
        or is_github_pr_preflight_intent(raw)
        or is_branch_push_intent(raw)
        or is_github_pr_open_intent(raw)
        or is_multi_agent_collaboration_intent(raw)
    )


def route_software_delivery(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not is_software_delivery_intent(raw):
        return None

    if is_multi_agent_collaboration_intent(raw):
        return _route_multi_agent_collaboration(raw, session_id=session_id)

    if is_github_pr_open_intent(raw):
        return _route_github_pr_open(raw, session_id=session_id)

    if is_branch_push_intent(raw):
        return _route_branch_push(raw, session_id=session_id)

    if is_github_pr_preflight_intent(raw):
        return _route_github_pr_preflight(raw, session_id=session_id)

    if is_pr_draft_intent(raw):
        return _route_pr_draft(raw, session_id=session_id)

    if is_workspace_verification_intent(raw):
        return _route_workspace_verification(raw, session_id=session_id)

    if is_workspace_application_intent(raw):
        return _route_workspace_application(raw, session_id=session_id)

    if is_patch_proposal_intent(raw):
        return _route_patch_proposal(raw, session_id=session_id)

    if is_branch_orchestration_intent(raw):
        return _route_branch_orchestration(raw, session_id=session_id)

    return route_software_delivery_issue_plan(raw, session_id=session_id)


def _route_patch_proposal(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")
    proposal_id = str((load_patch_proposal_for_plan(plan_id=plan_id) or {}).get("proposal_id") or "")

    if "propose" in raw.lower() and ("patch files" in raw.lower() or "files to change" in raw.lower()):
        result = propose_patch_files(session_id=session_id)
        if result.ok:
            body = render_proposed_files(result.proposal, plan=plan)
            intent = "software_delivery_patch_files_proposed"
        else:
            body = render_patch_proposal_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_patch_proposal_blocked"
        return body, intent, _meta(
            session_id,
            stage="patch_propose_files",
            plan_id=plan_id,
            proposal_id=str((result.proposal or {}).get("proposal_id") or proposal_id),
        )

    if "generate" in raw.lower() and "patch" in raw.lower():
        result = generate_patch_intent(session_id=session_id)
        if result.ok:
            body = render_patch_intent(result.proposal)
            intent = "software_delivery_patch_intent_generated"
        else:
            body = render_patch_proposal_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_patch_proposal_blocked"
        return body, intent, _meta(
            session_id,
            stage="patch_intent",
            plan_id=plan_id,
            proposal_id=str((result.proposal or {}).get("proposal_id") or proposal_id),
        )

    if "diff" in raw.lower() and "preview" in raw.lower():
        result = show_patch_diff_preview(session_id=session_id)
        if result.ok:
            body = render_diff_preview(result.proposal)
            intent = "software_delivery_patch_diff_preview"
        else:
            body = render_patch_proposal_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_patch_proposal_blocked"
        return body, intent, _meta(
            session_id,
            stage="patch_diff_preview",
            plan_id=plan_id,
            proposal_id=str((result.proposal or {}).get("proposal_id") or proposal_id),
        )

    if "approve" in raw.lower() and "patch" in raw.lower():
        result = approve_patch_proposal(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_patch_proposal_status(result.proposal)
            intent = "software_delivery_patch_proposal_approved"
        else:
            body = render_patch_proposal_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_patch_proposal_blocked"
        return body, intent, _meta(
            session_id,
            stage="patch_approve",
            plan_id=plan_id,
            proposal_id=str((result.proposal or {}).get("proposal_id") or proposal_id),
        )

    proposal = load_patch_proposal_for_plan(plan_id=plan_id) if plan_id else None
    if proposal:
        body = render_patch_proposal_status(proposal)
        return body, "software_delivery_patch_proposal_status", _meta(
            session_id,
            stage="patch_status",
            plan_id=plan_id,
            proposal_id=str(proposal.get("proposal_id") or ""),
        )

    body = render_patch_proposal_blocked(
        blockers=["patch_proposal_missing"],
        detail="Run `propose patch files` after plan and branch are ready.",
    )
    return body, "software_delivery_patch_proposal_blocked", _meta(session_id, stage="blocked")


def _route_multi_agent_collaboration(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "run" in raw.lower() and "agent" in raw.lower():
        result = run_agent_collaboration(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_collaboration_report(result.record)
            intent = "software_delivery_agent_collaboration_completed"
        else:
            body = render_collaboration_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_agent_collaboration_blocked"
        return body, intent, _meta(
            session_id,
            stage="multi_agent_collaboration",
            plan_id=plan_id,
            collaboration_id=str((result.record or {}).get("collaboration_id") or ""),
            mutation_scope="multi_agent_advisory_only",
        )

    result = show_agent_collaboration(session_id=session_id)
    if result.ok:
        body = (
            render_collaboration_status(result.record)
            if "status" in raw.lower() and "report" not in raw.lower()
            else render_collaboration_report(result.record)
        )
        return body, "software_delivery_agent_collaboration", _meta(
            session_id,
            stage="multi_agent_collaboration_show",
            plan_id=plan_id,
            collaboration_id=str(result.record.get("collaboration_id") or ""),
        )
    body = render_collaboration_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_agent_collaboration_blocked", _meta(
        session_id, stage="multi_agent_collaboration_blocked", plan_id=plan_id
    )


def _route_github_pr_open(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "open" in raw.lower() and "pull" in raw.lower():
        result = open_governed_github_pull_request(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_github_pr_open_report(result.record)
            intent = "software_delivery_github_pr_opened"
        else:
            body = render_github_pr_open_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_github_pr_open_blocked"
        return body, intent, _meta_github_pr_open(
            session_id,
            stage="github_pr_open",
            plan_id=plan_id,
            pr_open_id=str((result.record or {}).get("pr_open_id") or ""),
        )

    result = show_github_pr_open(session_id=session_id)
    if result.ok:
        body = (
            render_github_pr_open_status(result.record)
            if "status" in raw.lower() and "report" not in raw.lower()
            else render_github_pr_open_report(result.record)
        )
        return body, "software_delivery_github_pr_open", _meta(
            session_id,
            stage="github_pr_open_show",
            plan_id=plan_id,
            pr_open_id=str(result.record.get("pr_open_id") or ""),
        )
    body = render_github_pr_open_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_github_pr_open_blocked", _meta(
        session_id, stage="github_pr_open_blocked", plan_id=plan_id
    )


def _route_branch_push(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "push" in raw.lower() and "github" in raw.lower():
        result = push_governed_branch_to_github(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_branch_push_report(result.push)
            intent = "software_delivery_github_branch_pushed"
        else:
            body = render_branch_push_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_github_branch_push_blocked"
        return body, intent, _meta_github_branch_push(
            session_id,
            stage="github_branch_push",
            plan_id=plan_id,
            push_id=str((result.push or {}).get("push_id") or ""),
        )

    result = show_branch_push(session_id=session_id)
    if result.ok:
        body = (
            render_branch_push_status(result.push)
            if "status" in raw.lower() and "report" not in raw.lower()
            else render_branch_push_report(result.push)
        )
        return body, "software_delivery_github_branch_push", _meta(
            session_id,
            stage="github_branch_push_show",
            plan_id=plan_id,
            push_id=str(result.push.get("push_id") or ""),
        )
    body = render_branch_push_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_github_branch_push_blocked", _meta(
        session_id, stage="github_branch_push_blocked", plan_id=plan_id
    )


def _route_github_pr_preflight(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "approve" in raw.lower() and "preflight" in raw.lower():
        result = approve_github_pr_creation_preflight(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_preflight_report(result.preflight)
            intent = "software_delivery_github_pr_preflight_approved"
        else:
            body = render_preflight_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_github_pr_preflight_blocked"
        return body, intent, _meta(
            session_id,
            stage="github_pr_preflight_approve",
            plan_id=plan_id,
            preflight_id=str((result.preflight or {}).get("preflight_id") or ""),
        )

    if "run" in raw.lower() and "preflight" in raw.lower():
        result = run_github_pr_creation_preflight(session_id=session_id)
        if result.preflight:
            body = render_preflight_report(result.preflight)
            intent = (
                "software_delivery_github_pr_preflight_passed"
                if result.ok
                else "software_delivery_github_pr_preflight_failed"
            )
        else:
            body = render_preflight_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_github_pr_preflight_blocked"
        return body, intent, _meta(
            session_id,
            stage="github_pr_preflight_run",
            plan_id=plan_id,
            preflight_id=str((result.preflight or {}).get("preflight_id") or ""),
        )

    result = show_github_pr_preflight(session_id=session_id)
    if result.ok:
        body = (
            render_preflight_status(result.preflight)
            if "status" in raw.lower() and "report" not in raw.lower()
            else render_preflight_report(result.preflight)
        )
        return body, "software_delivery_github_pr_preflight", _meta(
            session_id,
            stage="github_pr_preflight_show",
            plan_id=plan_id,
            preflight_id=str(result.preflight.get("preflight_id") or ""),
        )
    body = render_preflight_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_github_pr_preflight_blocked", _meta(
        session_id, stage="github_pr_preflight_blocked", plan_id=plan_id
    )


def _route_pr_draft(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "create" in raw.lower() and "pr draft" in raw.lower():
        result = create_software_delivery_pr_draft(session_id=session_id)
        if result.ok:
            body = render_pr_draft(result.draft)
            intent = "software_delivery_pr_draft_created"
        else:
            body = render_pr_draft_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_pr_draft_blocked"
        return body, intent, _meta(
            session_id,
            stage="pr_draft_create",
            plan_id=plan_id,
            draft_id=str((result.draft or {}).get("draft_id") or ""),
        )

    result = show_pr_draft(session_id=session_id)
    if result.ok:
        body = (
            render_pr_draft_status(result.draft)
            if "status" in raw.lower()
            else render_pr_draft(result.draft)
        )
        return body, "software_delivery_pr_draft", _meta(
            session_id,
            stage="pr_draft_show",
            plan_id=plan_id,
            draft_id=str(result.draft.get("draft_id") or ""),
        )
    body = render_pr_draft_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_pr_draft_blocked", _meta(session_id, stage="pr_draft_blocked", plan_id=plan_id)


def _route_workspace_verification(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "run" in raw.lower() and "verification" in raw.lower():
        result = run_workspace_verification(session_id=session_id)
        if result.verification:
            body = render_verification_report(result.verification)
            if result.ok:
                intent = "software_delivery_workspace_verification_passed"
            elif result.verification.get("status") == "failed":
                intent = "software_delivery_workspace_verification_failed"
            else:
                intent = "software_delivery_workspace_verification_blocked"
        else:
            body = render_verification_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_workspace_verification_blocked"
        return body, intent, _meta(
            session_id,
            stage="workspace_verify_run",
            plan_id=plan_id,
            verification_id=str((result.verification or {}).get("verification_id") or ""),
        )

    if "report" in raw.lower():
        result = show_workspace_verification_status(session_id=session_id)
        if result.ok:
            body = render_verification_report(result.verification)
            intent = "software_delivery_workspace_verification_report"
        else:
            body = render_verification_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_workspace_verification_blocked"
        return body, intent, _meta(session_id, stage="workspace_verify_report", plan_id=plan_id)

    result = show_workspace_verification_status(session_id=session_id)
    if result.ok:
        body = render_verification_status(result.verification)
        return body, "software_delivery_workspace_verification_status", _meta(
            session_id, stage="workspace_verify_status", plan_id=plan_id
        )
    body = render_verification_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_workspace_verification_blocked", _meta(
        session_id, stage="workspace_verify_status", plan_id=plan_id
    )


def _route_workspace_application(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "apply" in raw.lower() and "workspace" in raw.lower():
        result = apply_approved_patch_to_workspace(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_workspace_apply_status(result.application)
            intent = "software_delivery_workspace_patch_applied"
        else:
            body = render_workspace_apply_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_workspace_apply_blocked"
        return body, intent, _meta_workspace(
            session_id,
            stage="workspace_apply",
            workspace_write=result.ok,
            plan_id=plan_id,
            application_id=str((result.application or {}).get("application_id") or ""),
        )

    if "rollback" in raw.lower() and "workspace" in raw.lower():
        result = rollback_workspace_changes(session_id=session_id, user_text=raw)
        if result.ok:
            body = render_workspace_apply_status(result.application)
            intent = "software_delivery_workspace_rolled_back"
        else:
            body = render_workspace_apply_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_workspace_apply_blocked"
        return body, intent, _meta_workspace(
            session_id,
            stage="workspace_rollback",
            workspace_write=result.ok,
            plan_id=plan_id,
        )

    if "diff" in raw.lower() and "workspace" in raw.lower():
        result = show_governed_workspace_diff(session_id=session_id)
        if result.ok:
            body = render_governed_workspace_diff(result.application)
            intent = "software_delivery_workspace_diff"
        else:
            body = render_workspace_apply_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_workspace_apply_blocked"
        return body, intent, _meta_workspace(session_id, stage="workspace_diff", plan_id=plan_id)

    result = show_workspace_apply_status(session_id=session_id)
    if result.ok:
        body = render_workspace_apply_status(result.application)
        return body, "software_delivery_workspace_apply_status", _meta_workspace(
            session_id, stage="workspace_status", plan_id=plan_id
        )
    body = render_workspace_apply_blocked(blockers=result.blockers, detail=result.detail)
    return body, "software_delivery_workspace_apply_blocked", _meta_workspace(
        session_id, stage="workspace_status", plan_id=plan_id
    )


def _route_branch_orchestration(
    raw: str,
    *,
    session_id: str,
) -> tuple[str, str, dict[str, str]]:
    plan = load_issue_plan_for_session(session_id=session_id)
    plan_id = str((plan or {}).get("plan_id") or "")

    if "create" in raw.lower() and "implementation branch" in raw.lower():
        result = create_implementation_branch(session_id=session_id, user_text=raw)
        if result.ok and result.branch_context:
            body = render_branch_status(result.branch_context, plan=plan)
            intent = "software_delivery_branch_created"
        else:
            body = render_branch_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_branch_blocked"
        return body, intent, _meta(
            session_id,
            stage="branch_create",
            plan_id=plan_id,
            branch_context_id=str((result.branch_context or {}).get("branch_context_id") or ""),
        )

    if "archive" in raw.lower() and "implementation branch" in raw.lower():
        result = archive_implementation_branch(session_id=session_id, user_text=raw)
        if result.ok and result.branch_context:
            body = render_branch_status(result.branch_context, plan=plan)
            intent = "software_delivery_branch_archived"
        else:
            body = render_branch_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_branch_blocked"
        return body, intent, _meta(session_id, stage="branch_archive", plan_id=plan_id)

    if "restore" in raw.lower() and "implementation branch" in raw.lower():
        result = restore_implementation_branch(session_id=session_id, user_text=raw)
        if result.ok and result.branch_context:
            body = render_branch_status(result.branch_context, plan=plan)
            intent = "software_delivery_branch_restored"
        else:
            body = render_branch_blocked(blockers=result.blockers, detail=result.detail)
            intent = "software_delivery_branch_blocked"
        return body, intent, _meta(session_id, stage="branch_restore", plan_id=plan_id)

    if "timeline" in raw.lower():
        timeline = build_software_delivery_timeline(session_id=session_id)
        body = render_software_delivery_timeline(timeline)
        intent = "software_delivery_timeline"
        ctx = timeline.get("branch_context") or {}
        return body, intent, _meta(
            session_id,
            stage="timeline",
            plan_id=plan_id,
            branch_context_id=str(ctx.get("branch_context_id") or ""),
        )

    if not plan:
        body = (
            "No software delivery issue plan for this session. "
            "Complete FIX 125A planning before branch orchestration."
        )
        return body, "software_delivery_branch_blocked", _meta(session_id, stage="blocked")

    ctx = load_branch_context_for_plan(plan_id=plan_id)
    if not ctx:
        body = render_branch_blocked(
            blockers=["branch_context_missing"],
            detail="Run `create implementation branch` with the create approval phrase.",
        )
        return body, "software_delivery_branch_blocked", _meta(session_id, stage="branch_status")

    body = render_branch_status(ctx, plan=plan)
    return body, "software_delivery_branch_status", _meta(
        session_id,
        stage="branch_status",
        plan_id=plan_id,
        branch_context_id=str(ctx.get("branch_context_id") or ""),
    )
