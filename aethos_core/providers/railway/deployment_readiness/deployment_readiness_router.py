# SPDX-License-Identifier: Apache-2.0
"""Railway deployment readiness router — hard ownership before generic DevOps/mutation routes."""

from __future__ import annotations

import logging
import re
from typing import Any

_log = logging.getLogger(__name__)

_BLOCKED_HANDLERS = (
    "front_door,capability_intro,devops_capability,generic_help,llm_fallback,"
    "github_workflow_lane,explicit_mutation_without_readiness"
)

_SHOW_READINESS_RX = re.compile(
    r"\bshow\s+(?:the\s+)?railway\s+deployment\s+readiness(?:\s+report)?\b",
    re.I,
)


def route_railway_deployment_readiness(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        compose_readiness_blocker,
        compose_readiness_passed_not_mutation_ready,
        readonly_checks_passed,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        get_readiness_context,
        save_readiness_context,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_intent import (
        is_railway_deployment_readiness_intent,
        is_railway_new_service_capability_question,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        compose_capability_truth_for_new_service,
        compose_readiness_report,
    )

    raw = (text or "").strip()
    if not is_railway_deployment_readiness_intent(raw):
        return None

    if _SHOW_READINESS_RX.search(raw):
        ctx = get_readiness_context(session_id=session_id)
        if ctx and ctx.get("checks"):
            body = compose_readiness_report(dict(ctx["checks"]))
            return body, "railway_deployment_readiness_plan", _meta(
                session_id,
                stage="show_plan",
                checks=ctx["checks"],
            )

    run_full_report = not is_railway_new_service_capability_question(raw) or bool(
        re.search(r"\b(readiness|check|plan|inspect|list)\b", raw, re.I)
    )

    checks: dict[str, Any] | None = None
    if run_full_report:
        checks = safe_run_deployment_readiness_checks(user_text=raw, session_id=session_id)
        save_readiness_context(session_id=session_id, checks=checks, user_text=raw)

    if is_railway_new_service_capability_question(raw) and not run_full_report:
        body = compose_capability_truth_for_new_service(checks)
        return body, "railway_new_service_capability", _meta(
            session_id,
            stage="capability_truth",
            checks=checks,
        )

    if checks is None:
        checks = safe_run_deployment_readiness_checks(user_text=raw, session_id=session_id)
        save_readiness_context(session_id=session_id, checks=checks, user_text=raw)

    if not readonly_checks_passed(checks):
        diagnostic = str(checks.get("check_error") or "")
        body = compose_readiness_blocker(checks, diagnostic=diagnostic)
        return body, "railway_deployment_readiness_blocked", _meta(
            session_id,
            stage="blocked",
            checks=checks,
            diagnostic=diagnostic,
        )

    if not checks.get("mutation_ready"):
        body = compose_readiness_passed_not_mutation_ready(checks)
        return body, "railway_deployment_readiness_passed_not_mutation_ready", _meta(
            session_id,
            stage="passed_not_mutation_ready",
            checks=checks,
        )

    body = compose_readiness_report(checks)
    if is_railway_new_service_capability_question(raw):
        prefix = compose_capability_truth_for_new_service(checks)
        body = f"{prefix}\n\n---\n\n{body}"

    return body, "railway_deployment_readiness", _meta(session_id, stage="readiness_report", checks=checks)


def _meta(
    session_id: str,
    *,
    stage: str,
    checks: dict[str, Any] | None = None,
    diagnostic: str = "",
) -> dict[str, str]:
    meta = {
        "route_id": "railway_deployment_readiness",
        "matched_module": "providers.railway.deployment_readiness.deployment_readiness_router",
        "railway_deployment_readiness_stage": stage,
        "blocked_handlers": _BLOCKED_HANDLERS,
        "session_id": session_id,
        "readonly": "true",
        "mutation_performed": "false",
    }
    if checks:
        meta["readonly_readiness_ok"] = "true" if checks.get("readonly_readiness_ok") else "false"
        meta["mutation_ready"] = "true" if checks.get("mutation_ready") else "false"
        inv = checks.get("inventory") or {}
        if inv.get("project_count") is not None:
            meta["railway_project_count"] = str(inv.get("project_count"))
        repo = str(checks.get("referenced_github_repo") or "").strip()
        if repo:
            meta["referenced_github_repo"] = repo
    if diagnostic:
        meta["diagnostic"] = diagnostic[:500]
    return meta
