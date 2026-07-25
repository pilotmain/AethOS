# SPDX-License-Identifier: Apache-2.0
"""Route Railway redeploy follow-ups without falling through to generic LLM chat."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.jobs.job_approval_guidance import mutation_approval_surface
from aethos_core.task_frame.railway_redeploy_intent import (
    RailwayRedeployIntent,
    clear_railway_redeploy_intent,
    get_railway_redeploy_intent,
    is_environment_only_reply,
    is_railway_redeploy_followup,
    mentions_railway_redeploy_context,
    parse_environment_only_reply,
    save_railway_redeploy_intent,
)
from aethos_core.task_frame.task_continuation import compose_task_continuation_reply
from aethos_core.task_frame.task_memory import get_active_task_frame

# §1 — a clearly fresh readonly request (list/show/logs/status/health of
# projects, services, deployments, …) is a *different operation* than a redeploy
# and must not be answered by a stale redeploy frame.
_FRESH_READONLY_RX = re.compile(
    r"\b(?:list|show|display|fetch|tail|read|give\s+me|get|what(?:'s| is| are)?|which)\b"
    r".*\b(projects?|services?|deployments?|logs?|status|inventory|apps?|environments?)\b",
    re.I,
)
# Bare read-only verbs/nouns — a fresh "list", "show", "logs", "health", "status"
# turn is a different operation even without an explicit object.
_FRESH_READONLY_VERB_RX = re.compile(
    r"\b(list|show|display|inspect|logs?|health|status|inventory)\b",
    re.I,
)
# Any non-Railway provider named anywhere wins — even when "railway" also appears
# (e.g. "don't talk about railway, list vercel projects").
_OTHER_PROVIDER_RX = re.compile(
    r"\b(vercel|github|render|fly(?:\.io)?|aws|gcp|google\s+cloud|cloudflare|"
    r"supabase|netlify|heroku|digitalocean|azure)\b",
    re.I,
)
# Explicit stop/redirect — the operator is steering away from the redeploy.
_STOP_REDIRECT_RX = re.compile(
    r"\b(?:don'?t|do\s+not|stop|quit|forget|ignore|no\s+more)\b[^.?!]{0,40}\brailway\b"
    r"|\bnot\s+railway\b"
    r"|\b(?:instead|actually|rather|never\s*mind|nevermind)\b",
    re.I,
)


def _redeploy_frame_should_yield(text: str) -> bool:
    """True when a pending redeploy frame must yield to a fresh, unrelated request.

    Yields when the new prompt (a) names a *different* provider anywhere, (b) is a
    fresh read-only/list query, or (c) contains an explicit stop/redirect. A
    genuine redeploy follow-up (environment reply, "redeploy…", "retrigger…")
    never yields, so the existing continuation flow is unchanged.
    """
    raw = (text or "").strip()
    if not raw:
        return False
    if is_railway_redeploy_followup(raw) or mentions_railway_redeploy_context(raw):
        return False
    if _OTHER_PROVIDER_RX.search(raw):
        return True
    if _STOP_REDIRECT_RX.search(raw):
        return True
    if _FRESH_READONLY_RX.search(raw):
        return True
    return bool(_FRESH_READONLY_VERB_RX.search(raw))


def compose_railway_redeploy_continuation_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    from aethos_core.post_mutation_verification.verification_intent_router import (
        get_pending_verification_request,
        has_pending_verification_disambiguation,
        looks_like_verification_target_selection,
    )

    if has_pending_verification_disambiguation(session_id=session_id) or looks_like_verification_target_selection(raw):
        return None

    active_frame = get_active_task_frame(session_id=session_id)
    if active_frame is not None and active_frame.status == "awaiting_target_selection":
        return compose_task_continuation_reply(text, session_id=session_id)

    pending = get_railway_redeploy_intent(session_id=session_id)
    # §3 — yield (and clear) a stale redeploy frame the moment the user issues a
    # clearly fresh, unrelated request so it can never hijack this or a later turn.
    if pending is not None and _redeploy_frame_should_yield(raw):
        clear_railway_redeploy_intent(session_id=session_id)
        return None
    if is_environment_only_reply(raw):
        if pending is None:
            return None
        env = parse_environment_only_reply(raw)
        merged = _merge_intent_request(pending, environment=env)
        return _create_preflights_from_intent(merged, session_id=session_id, trigger_text=raw)

    if not is_railway_redeploy_followup(raw) and not mentions_railway_redeploy_context(raw):
        if pending is None:
            return None

    if mentions_railway_redeploy_context(raw) or is_railway_redeploy_followup(raw):
        intent = _build_intent_from_text(raw, session_id=session_id, prior=pending)
        save_railway_redeploy_intent(intent)
        return _create_preflights_from_intent(intent, session_id=session_id, trigger_text=raw)

    if pending is not None:
        return _create_preflights_from_intent(pending, session_id=session_id, trigger_text=raw)

    return None


def _build_intent_from_text(
    text: str,
    *,
    session_id: str,
    prior: RailwayRedeployIntent | None,
) -> RailwayRedeployIntent:
    from aethos_core.providers.railway.railway_inventory_target_picker import (
        default_aethos_service_hints,
        extract_environment_hint,
        extract_project_hint,
        extract_service_hints,
        infer_redeploy_environment,
    )

    base = prior.original_request if prior and prior.original_request else text
    merged_request = text if mentions_railway_redeploy_context(text) else base
    if prior and prior.original_request and text != prior.original_request:
        merged_request = f"{prior.original_request}\n{text}"

    env = extract_environment_hint(merged_request) or (prior.environment if prior else "")
    if not env and is_environment_only_reply(text):
        env = parse_environment_only_reply(text)
    if not env:
        env = infer_redeploy_environment(merged_request)
    project = extract_project_hint(merged_request) or (prior.project_hint if prior else "pilotos")
    services = extract_service_hints(merged_request, project_hint=project)
    services = [service for service in services if _looks_like_service_name(service)]
    if prior and prior.service_hints and not services:
        services = [service for service in prior.service_hints if _looks_like_service_name(service)]
    if not services:
        services = default_aethos_service_hints(project_hint=project)

    return RailwayRedeployIntent(
        session_id=session_id,
        original_request=merged_request,
        environment=env,
        project_hint=project,
        service_hints=services,
    )


def _merge_intent_request(intent: RailwayRedeployIntent, *, environment: str) -> RailwayRedeployIntent:
    return RailwayRedeployIntent(
        session_id=intent.session_id,
        original_request=intent.original_request,
        operation=intent.operation,
        environment=environment,
        project_hint=intent.project_hint,
        service_hints=list(intent.service_hints),
    )


def _looks_like_service_name(service: str) -> bool:
    token = (service or "").strip().lower()
    if not token:
        return False
    if " " in token:
        return False
    if token in {"redeploy", "redeploying", "latest", "changes", "staging", "production"}:
        return False
    return "-" in token or token.endswith(("api", "ui"))


def _create_preflights_from_intent(
    intent: RailwayRedeployIntent,
    *,
    session_id: str,
    trigger_text: str,
) -> tuple[str, str, dict[str, str]] | None:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        safe_run_deployment_readiness_checks,
    )
    from aethos_core.providers.railway.railway_inventory_target_picker import (
        infer_redeploy_environment,
        pick_railway_targets,
    )
    from aethos_core.provider_e2e_execution.railway_e2e_execution import _route_multi_target_railway_e2e
    from aethos_core.config import get_settings

    request = intent.original_request or trigger_text
    checks = safe_run_deployment_readiness_checks(user_text=request, session_id=session_id)
    if not checks.get("railway_credential_ok") or not checks.get("railway_api_connection_ok"):
        from aethos_core.task_frame.railway_deploy_selection import (
            compose_ambiguous_railway_target_reply,
            store_railway_deploy_selection_task,
        )

        candidates = pick_railway_targets(
            checks,
            request,
            default_hint=intent.project_hint or "aethos",
        ).candidates
        if candidates:
            store_railway_deploy_selection_task(
                session_id=session_id,
                user_text=request,
                checks=checks,
                candidates=candidates,
            )
        body = compose_ambiguous_railway_target_reply(
            operation=intent.operation,
            candidates=candidates or [],
        )
        return body, "railway_redeploy_missing_connection", {"provider": "railway"}

    env = intent.environment or infer_redeploy_environment(request)
    enriched = request
    if intent.service_hints:
        enriched = f"{enriched}\n" + " and ".join(intent.service_hints)
    if env and env not in enriched.lower():
        enriched = f"{enriched}\n{env}"

    picked = pick_railway_targets(
        checks,
        enriched,
        default_hint=intent.project_hint or "aethos",
    )
    if not picked.targets:
        from aethos_core.task_frame.railway_deploy_selection import (
            compose_ambiguous_railway_target_reply,
            store_railway_deploy_selection_task,
        )

        candidates = list(picked.candidates or [])
        if candidates:
            store_railway_deploy_selection_task(
                session_id=session_id,
                user_text=request,
                checks=checks,
                candidates=candidates,
            )
        body = compose_ambiguous_railway_target_reply(operation=intent.operation, candidates=candidates)
        return body, "railway_redeploy_target_clarification", {"provider": "railway", "task_frame": "stored"}

    settings = get_settings()
    triples = [(row.project, row.environment, row.service) for row in picked.targets]
    if len(triples) == 1:
        from aethos_core.chat.mutation_preflight_prompts import create_mutation_preflight_job_reply

        project, environment, service = triples[0]
        explicit = f"redeploy railway {project} / {environment} / {service} with latest git changes"
        reply = create_mutation_preflight_job_reply(explicit, session_id=session_id)
        if reply is None:
            return None
        clear_railway_redeploy_intent(session_id=session_id)
        body, reply_intent, meta = reply
        return body, reply_intent, {**meta, "railway_redeploy_continuation": "true"}

    body, reply_intent, meta = _route_multi_target_railway_e2e(
        request,
        checks=checks,
        settings=settings,
        targets=triples,
        session_id=session_id,
    )
    clear_railway_redeploy_intent(session_id=session_id)
    return body, reply_intent, {**meta, "railway_redeploy_continuation": "true"}


def compose_railway_redeploy_status_reply(
    *,
    targets: list[str],
    job_ids: list[str],
) -> str:
    approval_path = mutation_approval_surface()
    lines = [
        f"Prepared **{len(targets)}** Railway redeploy preflight(s):",
    ]
    for job_id, path in zip(job_ids, targets):
        lines.append(f"- `{job_id}` → **{path}**")
    lines.extend(
        [
            "",
            "**No redeploy has been performed yet.**",
            "",
            f"Review and approve in **{approval_path}**.",
        ]
    )
    return "\n".join(lines)
