# SPDX-License-Identifier: Apache-2.0
"""Route Railway new-service deployment plan artifact requests."""

from __future__ import annotations

from typing import Any

_BLOCKED_HANDLERS = (
    "front_door,devops_capability,github_workflow_lane,explicit_mutation,"
    "railway_mutation_preflight,generic_help"
)


def route_railway_new_service_plan(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_plan.deployment_plan_artifact import (
        compose_target_clarification,
        classify_plan_risk,
        infer_service_name_from_repo,
        list_railway_project_environment_options,
        normalize_plan_for_artifact,
        parse_plan_fields_from_text,
        render_railway_deployment_plan_artifact,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        save_deployment_plan_context,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_lifecycle import (
        resolve_and_materialize_deployment_plan,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_intent import (
        is_railway_deployment_plan_complete_intent,
        is_railway_deployment_plan_confirm_intent,
        is_railway_deployment_plan_review_intent,
        is_railway_new_service_plan_intent,
        is_show_railway_deployment_plan_intent,
    )
    from aethos_core.providers.railway.deployment_plan.plan_review import (
        apply_plan_review_confirmation,
        compose_plan_review_confirmed,
        compose_plan_review_request,
        is_plan_review_confirmed,
        plan_ready_for_review,
    )
    from aethos_core.providers.railway.deployment_plan.plan_completion import complete_railway_deployment_plan
    from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        get_readiness_context,
    )
    raw = (text or "").strip()
    if not is_railway_new_service_plan_intent(raw):
        return None

    existing = resolve_and_materialize_deployment_plan(session_id=session_id, user_text=raw)

    if is_railway_deployment_plan_confirm_intent(raw):
        if not existing or not existing.get("repo"):
            return (
                "I don't have a saved Railway deployment plan to confirm yet.\n\n"
                "Create and complete one first:\n"
                "`create railway deployment plan for pilotmain/aethos in pilotos / production`\n"
                "`complete the railway deployment plan`\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_confirm_not_ready",
                _meta(session_id, stage="confirm_no_plan", plan={}),
            )
        if is_plan_review_confirmed(existing):
            body = compose_plan_review_confirmed(existing)
            return body, "railway_deployment_plan_confirm_already", _meta(
                session_id, stage="confirm_already", plan=existing
            )
        if not plan_ready_for_review(existing):
            gate = assess_mutation_readiness_gate(existing)
            missing = ", ".join(gate.get("missing") or []) or "plan fields"
            return (
                "The deployment plan is not ready for confirmation yet.\n\n"
                f"Still missing: {missing}\n\n"
                "Run `complete the railway deployment plan` after fixing targets or repo inspection.\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_confirm_not_ready",
                _meta(session_id, stage="confirm_not_ready", plan=existing),
            )
        updated = apply_plan_review_confirmation(existing)
        save_deployment_plan_context(session_id=session_id, plan=updated)
        body = compose_plan_review_confirmed(updated)
        return body, "railway_deployment_plan_confirm", _meta(session_id, stage="review_confirmed", plan=updated)

    if is_railway_deployment_plan_review_intent(raw):
        if not existing or not existing.get("repo"):
            return (
                "I don't have a saved Railway deployment plan to review yet.\n\n"
                "Create one first:\n"
                "`create railway deployment plan for pilotmain/aethos in pilotos / production`\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_review_not_ready",
                _meta(session_id, stage="review_no_plan", plan={}),
            )
        if not plan_ready_for_review(existing):
            return (
                "The deployment plan is not complete enough to review yet.\n\n"
                "Run `complete the railway deployment plan` after setting Railway target and repo inspection.\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_review_not_ready",
                _meta(session_id, stage="review_incomplete", plan=existing),
            )
        body = compose_plan_review_request(existing)
        return body, "railway_deployment_plan_review", _meta(session_id, stage="review", plan=existing)

    if is_railway_deployment_plan_complete_intent(raw):
        plan_base = dict(existing or {})
        fields = parse_plan_fields_from_text(raw, default_repo=str(plan_base.get("repo") or ""))
        if fields.get("repo"):
            plan_base["repo"] = fields["repo"]
        if fields.get("branch"):
            plan_base["branch"] = fields["branch"]
        if not plan_base.get("repo"):
            return (
                "I don't have a saved Railway deployment plan yet.\n\n"
                "Create one first:\n"
                "`create railway deployment plan for pilotmain/aethos in pilotos / production`\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_complete_needs_plan",
                _meta(session_id, stage="complete_needs_plan", plan={}),
            )
        if not plan_base.get("service_name"):
            plan_base["service_name"] = infer_service_name_from_repo(str(plan_base["repo"]))
        readiness_ctx = get_readiness_context(session_id=session_id)
        checks = (readiness_ctx or {}).get("checks") if readiness_ctx else None
        body, updated, _inspection = complete_railway_deployment_plan(plan_base, checks=checks)
        save_deployment_plan_context(session_id=session_id, plan=updated)
        gate = assess_mutation_readiness_gate(updated)
        intent = (
            "railway_deployment_plan_complete"
            if gate.get("mutation_ready")
            else "railway_deployment_plan_completion"
        )
        return body, intent, _meta(session_id, stage="plan_complete", plan=updated)

    if is_show_railway_deployment_plan_intent(raw):
        if not existing or not existing.get("repo"):
            return (
                "I don't have a saved Railway deployment plan yet.\n\n"
                "Create one first:\n"
                "`create railway deployment plan for pilotmain/aethos in pilotos / production`\n\n"
                "No mutation has been performed.",
                "railway_deployment_plan_show_missing",
                _meta(session_id, stage="show_missing", plan={}),
            )
        readiness_ctx = get_readiness_context(session_id=session_id)
        checks = (readiness_ctx or {}).get("checks") if readiness_ctx else None
        plan = normalize_plan_for_artifact(existing)
        body = render_railway_deployment_plan_artifact(
            plan,
            checks=checks,
            include_readiness_line=bool(checks),
            session_id=session_id,
        )
        return body, "railway_deployment_plan_show", _meta(session_id, stage="show_plan", plan=plan)

    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
        resolve_readiness_for_plan_creation,
    )

    readiness = resolve_readiness_for_plan_creation(session_id=session_id, user_text=raw)
    lifecycle = readiness.lifecycle
    checks = readiness.checks

    if not readiness.satisfied:
        body = (
            "Railway deployment readiness must pass before I can draft a governed new-service plan.\n\n"
            "Run `run railway deployment readiness for <owner/repo>` first, then ask again for the plan."
        )
        return body, "railway_deployment_plan_needs_readiness", _meta(
            session_id,
            stage="needs_readiness",
            plan={"repo": parse_plan_fields_from_text(raw).get("repo") or ""},
        )

    fields = parse_plan_fields_from_text(raw, default_repo=str((existing or {}).get("repo") or ""))
    repo = fields.get("repo")
    if not repo:
        return (
            "Include a GitHub repo in the plan request, for example:\n"
            "`create railway deployment plan for pilotmain/aethos`\n\n"
            "No mutation has been performed.",
            "railway_deployment_plan_needs_repo",
            _meta(session_id, stage="needs_repo", plan={}),
        )

    project = fields.get("project") or (existing or {}).get("project")
    environment = fields.get("environment") or (existing or {}).get("environment")
    service_name = fields.get("service_name") or (existing or {}).get("service_name")

    missing: list[str] = []
    if not project or not environment:
        missing.extend(["project", "environment"])
    if not service_name:
        missing.append("service_name")

    if missing and ("project" in missing or "environment" in missing):
        options = list_railway_project_environment_options()
        body = compose_target_clarification(repo=str(repo), options=options, missing=tuple(missing))
        draft = {
            "repo": repo,
            "branch": fields.get("branch") or "main",
            "project": project,
            "environment": environment,
            "service_name": service_name,
            "stage": "plan_needs_target",
            "mutation_ready": False,
        }
        save_deployment_plan_context(session_id=session_id, plan=draft)
        return body, "railway_deployment_plan_clarification", _meta(
            session_id,
            stage="needs_target",
            plan=draft,
        )

    if not service_name:
        service_name = infer_service_name_from_repo(str(repo))

    risk_tier = classify_plan_risk(environment=str(environment or ""))
    plan: dict[str, Any] = {
        "repo": repo,
        "branch": fields.get("branch") or "main",
        "project": project,
        "environment": environment,
        "service_name": service_name,
        "stage": "plan_draft",
        "mutation_ready": False,
        "risk_tier": risk_tier.value,
        "readiness_passed": True,
        "build_command": "unknown / inferred",
        "start_command": "unknown / inferred",
        "runtime": "unknown / inferred",
    }
    save_deployment_plan_context(session_id=session_id, plan=plan)

    body = render_railway_deployment_plan_artifact(
        plan,
        checks=checks,
        include_readiness_line=True,
        session_id=session_id,
    )
    return body, "railway_deployment_plan_draft", _meta(session_id, stage="plan_draft", plan=plan)


def _meta(session_id: str, *, stage: str, plan: dict[str, Any]) -> dict[str, str]:
    meta = {
        "route_id": "railway_deployment_plan",
        "matched_module": "providers.railway.deployment_plan.deployment_plan_router",
        "railway_deployment_plan_stage": stage,
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
        "mutation_ready": "true" if plan.get("mutation_ready") else "false",
        "review_confirmed": "true" if plan.get("review_confirmed") else "false",
        "presentation_bypass": "true",
        "presentation_mode": "engineering",
        "suppress_governance_footer": "true",
    }
    if plan.get("repo"):
        meta["repo"] = str(plan["repo"])
    if plan.get("project"):
        meta["railway_project"] = str(plan["project"])
    if plan.get("environment"):
        meta["railway_environment"] = str(plan["environment"])
    if plan.get("service_name"):
        meta["service_name"] = str(plan["service_name"])
    return meta
