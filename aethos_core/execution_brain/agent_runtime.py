# SPDX-License-Identifier: Apache-2.0
"""AethOS agent LLM tool loop for step-3 chat (readonly tools + governed preflight)."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from aethos_core.config import get_settings
from aethos_core.execution_brain.agent_tool_executor import (
    agent_tool_schemas,
    execute_agent_tool,
    registry_summary_for_prompt,
)
from aethos_core.provider.completion import provider_configured


@dataclass
class AgentRuntimeResult:
    reply: str
    used_llm: bool = False
    provider: str | None = None
    model: str | None = None
    tool_calls: int = 0
    iterations: int = 0
    meta: dict[str, str] = field(default_factory=dict)


MAX_TOOL_ITERATIONS = 12
MAX_TOOL_LOOP_STREAK = 24

_log = logging.getLogger("aethos.agent_runtime")


def is_provider_orchestration_request(text: str, *, session_id: str = "default") -> bool:
    """Provider cloud ops — inventory, health, logs, governed mutations."""
    from aethos_core.execution_brain.agent_provider_cloud import is_agent_provider_cloud_request

    return is_agent_provider_cloud_request(text, session_id=session_id)


def should_use_agent_runtime(text: str) -> bool:
    settings = get_settings()
    if not settings.agent_runtime_enabled:
        return False
    if not provider_configured():
        return False
    raw = (text or "").strip()
    if len(raw) < 4:
        return False
    return True


_MAX_CANVAS_PROBE = 50


def _canvas_view_ids(session_id: str) -> set[str]:
    """Exact per-session set of view ids (never the tenant-latest fallback). A render is
    verified by a NEW id appearing — robust to re-rendering the same view type, which
    replaces (delete+insert) and so leaves the COUNT unchanged but the id different."""
    try:
        from aethos_core.canvas.canvas_store import get_canvas_state

        state = get_canvas_state(session_id=session_id, limit=_MAX_CANVAS_PROBE, include_fallback=False)
        return {str(v.get("id") or "") for v in (state.get("views") or []) if v.get("id")}
    except Exception:  # pragma: no cover - defensive
        return set()


def _canvas_view_count(session_id: str) -> int:
    try:
        from aethos_core.canvas.canvas_store import get_canvas_state

        # Exact per-session count — never the tenant-latest fallback, or the before/after
        # render verification would compare a prior render against itself and falsely fail.
        return int(
            get_canvas_state(session_id=session_id, limit=1, include_fallback=False).get("view_count") or 0
        )
    except Exception:  # pragma: no cover - defensive
        return 0


def _canvas_view_type_for(text: str) -> str:
    """Pick a canvas view_type from the operator's wording (defaults to markdown)."""
    t = (text or "").lower()
    if "diff" in t:
        return "diff"
    if "timeline" in t:
        return "job_timeline"
    if "table" in t:
        return "table"
    if "research" in t or "report" in t:
        return "research_report"
    if "status" in t:
        return "status"
    return "markdown"


def _structured_canvas_payload(view_type: str, *, session_id: str) -> dict[str, Any] | None:
    """Build a minimal structured payload when the model skips canvas_render."""
    vt = (view_type or "markdown").strip().lower()
    if vt == "job_timeline":
        from aethos_core.runtime.jobs import job_store

        events: list[dict[str, str]] = []
        sid = (session_id or "default").strip() or "default"
        for job in job_store.list_all():
            if (job.session_id or "default") != sid:
                continue
            events.append(
                {
                    "label": (job.title or job.job_type or job.id)[:120],
                    "status": str(job.status.value if hasattr(job.status, "value") else job.status),
                    "timestamp": str(int(job.updated_at or job.created_at)),
                    "detail": job.job_type,
                }
            )
        if not events:
            events = [
                {
                    "label": "Session ready",
                    "status": "active",
                    "detail": "No tracked jobs yet — timeline scaffold for this chat session.",
                }
            ]
        return {"events": events[-20:]}
    if vt == "status":
        return {"items": [{"name": "Canvas", "status": "ready"}, {"name": "Session", "status": session_id[:32]}]}
    if vt == "table":
        return {"columns": ["step", "status"], "rows": [{"step": "Canvas", "status": "ready"}]}
    if vt == "markdown":
        return {"content": "Canvas view — structured render for this session."}
    return None


def _try_deterministic_canvas_render(text: str, *, session_id: str) -> bool:
    """Write a structured canvas view when the model did not call canvas_render."""
    from aethos_core.canvas.canvas_store import is_structured_canvas_view_data, render_canvas_view
    from aethos_core.chat.front_door_intent import is_canvas_render_request

    if not is_canvas_render_request(text):
        return False
    if not bool(getattr(get_settings(), "canvas_surface_enabled", True)):
        return False
    view_type = _canvas_view_type_for(text)
    data = _structured_canvas_payload(view_type, session_id=session_id)
    if not data:
        return False
    valid, _ = is_structured_canvas_view_data(view_type, data)
    if not valid:
        return False
    title = view_type.replace("_", " ").title()
    out = render_canvas_view(
        session_id=session_id,
        view_type=view_type,
        title=title,
        data=data,
    )
    return bool(out.get("ok"))


_CANVAS_SUCCESS_CLAIM_RX = re.compile(
    r"\brendered\b.{0,80}\b(canvas|live canvas)\b|\bopen the canvas tab\b",
    re.I,
)

_CANVAS_REFUSAL_RX = re.compile(
    r"\b("
    r"isn'?t available"
    r"|not available in this"
    r"|can'?t render"
    r"|cannot render"
    r"|tool isn'?t"
    r"|no canvas_render"
    r"|canvas rendering tool"
    r"|canvas_render is not"
    r")\b",
    re.I,
)


def canvas_render_success_confirmation(view_type: str) -> str:
    """Single source of truth — only returned after a verified canvas write."""
    badge = (view_type or "view").replace("_", " ")
    return f"Rendered a {badge} to the Canvas — open the Canvas tab to view."


def _honest_canvas_disabled_reply() -> str:
    from aethos_core.chat.informational_help_router import compose_canvas_setup_guidance_reply

    return compose_canvas_setup_guidance_reply()


def _honest_canvas_failed_reply(error: str = "") -> str:
    if error == "canvas_surface_disabled":
        return _honest_canvas_disabled_reply()
    base = "I couldn't render to the Canvas right now."
    if error:
        return f"{base} Reason: {error.replace('_', ' ')}."
    return f"{base} Try again or check that the Canvas surface is enabled for this deployment."


def _canvas_render_verified(session_id: str, ids_before: set[str]) -> bool:
    # A render happened iff a view id exists now that wasn't there before. Robust to
    # same-type re-renders (replace gives a new id, so the count can stay the same).
    return bool(_canvas_view_ids(session_id) - ids_before)


def _latest_canvas_view_is_structured(session_id: str, view_type: str) -> bool:
    from aethos_core.canvas.canvas_store import get_canvas_state, is_structured_canvas_view_data

    state = get_canvas_state(session_id=session_id, limit=3, include_fallback=False)
    views = list(state.get("views") or [])
    if not views:
        return False
    vt = (view_type or "").strip().lower()
    for view in views:
        if str(view.get("view_type") or "").lower() == vt:
            valid, _ = is_structured_canvas_view_data(vt, view.get("data"))
            return valid
    latest = views[0]
    valid, _ = is_structured_canvas_view_data(str(latest.get("view_type") or ""), latest.get("data"))
    return valid


def _model_refused_canvas(reply: str) -> bool:
    return bool(_CANVAS_REFUSAL_RX.search(reply or ""))


def _ensure_canvas_render(text: str, *, session_id: str, reply: str, views_before: set[str]) -> str:
    """Honesty guard — success only when canvas_render wrote a real structured view.

    ``views_before`` is the set of canvas view ids that existed before the turn.
    """
    from aethos_core.chat.front_door_intent import is_canvas_render_request

    if not is_canvas_render_request(text):
        return reply

    canvas_enabled = bool(getattr(get_settings(), "canvas_surface_enabled", True))
    view_type = _canvas_view_type_for(text)
    claimed_success = bool(_CANVAS_SUCCESS_CLAIM_RX.search(reply or ""))

    if not canvas_enabled:
        if claimed_success:
            return _honest_canvas_disabled_reply()
        return reply

    if _canvas_render_verified(session_id, views_before) and _latest_canvas_view_is_structured(session_id, view_type):
        return canvas_render_success_confirmation(view_type)

    if canvas_enabled and not _canvas_render_verified(session_id, views_before):
        _try_deterministic_canvas_render(text, session_id=session_id)
        if _canvas_render_verified(session_id, views_before) and _latest_canvas_view_is_structured(session_id, view_type):
            return canvas_render_success_confirmation(view_type)

    if claimed_success or _model_refused_canvas(reply):
        return _honest_canvas_failed_reply("canvas_render_not_invoked")
    return reply


def run_agent_runtime_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    model_override: str | None = None,
    tenant_id: str | None = None,
    surface: str = "webchat",
) -> AgentRuntimeResult | None:
    """Run governed tool loop; None when disabled or misconfigured."""
    from aethos_core.chat.chat_turn_tenant import chat_turn_scope

    with chat_turn_scope(tenant_id):
        return _run_agent_runtime_turn_impl(
            text,
            session_id=session_id,
            channel=channel,
            model_override=model_override,
            surface=surface,
        )


def _run_agent_runtime_turn_impl(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    model_override: str | None = None,
    surface: str = "webchat",
) -> AgentRuntimeResult | None:
    """Inner agent runtime body — must run inside chat_turn_scope."""
    if not should_use_agent_runtime(text):
        return None

    from aethos_core.llm.effective_model import (
        ModelSelectionUnavailable,
        effective_model_for_agent_tool_loop,
        model_unavailable_reply,
        resolve_effective_model,
        _unavailable_reason_for_entry,
    )

    try:
        effective = resolve_effective_model(session_id=session_id, turn_override=model_override)
    except ModelSelectionUnavailable as exc:
        return AgentRuntimeResult(
            reply=model_unavailable_reply(exc.catalog_id, exc.reason),
            used_llm=False,
            provider="none",
            model=exc.catalog_id,
            meta={
                "lane": "agent_runtime",
                "route_id": "agent_runtime",
                "model_selection_error": "true",
                "catalog_id": exc.catalog_id,
                "channel": channel,
                "session_id": session_id,
            },
        )
    tool_loop_model = effective_model_for_agent_tool_loop(effective)
    if tool_loop_model is None and effective.source in ("turn", "session"):
        reason = _unavailable_reason_for_entry(
            {
                "id": effective.catalog_id,
                "provider": effective.provider,
                "model": effective.model,
                "label": effective.label,
            }
        )
        return AgentRuntimeResult(
            reply=model_unavailable_reply(effective.catalog_id, reason),
            used_llm=False,
            provider=effective.provider,
            model=effective.model,
            meta={
                "lane": "agent_runtime",
                "route_id": "agent_runtime",
                "model_selection_error": "true",
                "catalog_id": effective.catalog_id,
                "channel": channel,
                "session_id": session_id,
            },
        )

    from aethos_core.execution_brain.agent_deterministic_shortcuts import run_agent_deterministic_shortcut

    shortcut = run_agent_deterministic_shortcut(text, session_id=session_id)
    if shortcut is not None:
        meta = dict(shortcut.get("meta") or {})
        meta.setdefault("lane", "agent_runtime")
        meta["channel"] = channel
        meta["session_id"] = session_id
        meta["suppress_governance_footer"] = "true"
        meta["presentation_mode"] = "direct"
        meta["effective_model"] = effective.model
        meta["effective_model_source"] = effective.source
        meta["model_catalog_id"] = effective.catalog_id
        return AgentRuntimeResult(
            reply=str(shortcut.get("reply") or ""),
            used_llm=False,
            provider=effective.provider,
            model=effective.model,
            meta=meta,
        )

    from aethos_core.provider.completion import (
        complete_chat,
        run_tool_loop_with_provider_failover,
    )

    # §5 — snapshot canvas view ids so we can tell whether the model rendered this turn
    # (a new id appearing — robust to same-type re-renders that replace in place).
    canvas_views_before = _canvas_view_ids(session_id)

    if tool_loop_model is None:
        prov = complete_chat(text, session_id=session_id, channel=channel, model_override=model_override)
        reply = _ensure_canvas_render(
            text, session_id=session_id, reply=prov.text, views_before=canvas_views_before
        )
        meta = {
            "lane": "agent_runtime",
            "route_id": "agent_runtime",
            "matched_module": "execution_brain.agent_runtime",
            "presentation_mode": "direct",
            "suppress_governance_footer": "true",
            "channel": channel,
            "session_id": session_id,
            "effective_model": effective.model,
            "effective_model_source": effective.source,
            "model_catalog_id": effective.catalog_id,
            "selected_model": effective.model,
            "selected_model_label": effective.label,
            "selected_catalog_id": effective.catalog_id,
            "tool_fallback": "false",
            "agent_tool_calls": "0",
            "agent_iterations": "1",
        }
        return AgentRuntimeResult(
            reply=reply,
            used_llm=prov.used_llm,
            provider=prov.provider,
            model=prov.model,
            meta=meta,
        )

    system = _build_system_prompt()
    user_block = _build_user_prompt(text, session_id=session_id, channel=channel)
    tool_executor = lambda name, inp: execute_agent_tool(  # noqa: E731
        name, inp, session_id=session_id, channel=channel, surface=surface
    )
    # §2 — advertise the email triage tool only on explicit email/inbox prompts so
    # an IMAP/“not configured” line can never bleed into an unrelated answer.
    turn_tools = agent_tool_schemas(
        for_prompt=text,
        channel=channel,
        session_id=session_id,
        surface=surface,
    )

    # Transparency: the picker chose `effective`; if the tool loop swapped to a
    # different model we record it as a *fallback* so the UI can show both.
    actual_model = tool_loop_model.model
    actual_provider = tool_loop_model.provider

    loop_out = run_tool_loop_with_provider_failover(
        tool_loop_model,
        system=system,
        user_message=user_block,
        tools=turn_tools,
        tool_executor=tool_executor,
        max_iterations=MAX_TOOL_ITERATIONS,
        max_tool_streak=MAX_TOOL_LOOP_STREAK,
        channel=channel,
    )
    if loop_out is None:
        return None

    actual_model = loop_out.model
    actual_provider = loop_out.provider

    selection_fallback = (
        tool_loop_model.provider != effective.provider
        or tool_loop_model.catalog_id != effective.catalog_id
    )
    provider_failover = (
        loop_out.provider != tool_loop_model.provider or loop_out.model != tool_loop_model.model
    )
    used_cloud_fallback = selection_fallback
    fallback = used_cloud_fallback or provider_failover

    from aethos_core.provider.completion import record_completion_usage

    record_completion_usage(loop_out, session_id=session_id)

    meta = {
        "lane": "agent_runtime",
        "route_id": "agent_runtime",
        "matched_module": "execution_brain.agent_runtime",
        "agent_tool_calls": str(loop_out.tool_calls),
        "agent_iterations": str(loop_out.iterations),
        "loop_outcome": str(getattr(loop_out, "loop_outcome", None) or "answered"),
        "presentation_mode": "direct",
        "suppress_governance_footer": "true",
        "channel": channel,
        "session_id": session_id,
        "effective_model": actual_model,
        "effective_model_source": effective.source,
        "model_catalog_id": effective.catalog_id,
        "selected_model": effective.model,
        "selected_model_label": effective.label,
        "selected_catalog_id": effective.catalog_id,
        "tool_fallback": "true" if fallback else "false",
    }
    reply = _ensure_canvas_render(
        text, session_id=session_id, reply=loop_out.text, views_before=canvas_views_before
    )
    if fallback and used_cloud_fallback:
        note = (
            f"_Tools needed a cloud model — this turn ran on {actual_model} "
            f"(your selection: {effective.label})._"
        )
        meta["tool_fallback_model"] = actual_model
        meta["tool_fallback_provider"] = actual_provider
        meta["escalation_note"] = note
        reply = f"{note}\n\n{reply}"
    return AgentRuntimeResult(
        reply=reply,
        used_llm=loop_out.used_llm,
        provider=loop_out.provider,
        model=loop_out.model,
        tool_calls=loop_out.tool_calls,
        iterations=loop_out.iterations,
        meta=meta,
    )


def agent_runtime_chat_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    model_override: str | None = None,
    tenant_id: str | None = None,
    surface: str = "webchat",
):
    """Return ChatTurnResult when agent runtime handles the turn."""
    from aethos_core.chat.service import ChatTurnResult

    runtime = run_agent_runtime_turn(
        text,
        session_id=session_id,
        channel=channel,
        model_override=model_override,
        tenant_id=tenant_id,
        surface=surface,
    )
    if runtime is None:
        return None
    return ChatTurnResult(
        reply=runtime.reply,
        intent="agent_runtime",
        provider_stream=False,
        used_llm=runtime.used_llm,
        provider=runtime.provider,
        model=runtime.model,
        meta=dict(runtime.meta),
    )


def _repo_review_guidance_lines() -> list[str]:
    from aethos_core.production.deployment_mode import is_hosted_deployment

    if is_hosted_deployment():
        return [
            "Repository review (hosted — GitHub API, NOT the user's laptop):",
            "- On hosted AethOS you cannot read local laptop paths. For GitHub repos use "
            "github_read_repo (owner/repo or repo name) — reads tree + key files via API.",
            "- If GitHub is not connected, say so once: Mission Control → Advanced settings → Credentials (GitHub token).",
            "- Never tell a hosted user to register a local path or local workspace for a GitHub repo ask.",
            "- repo_overview/repo_list/repo_read/repo_grep are for registered local workspaces only.",
        ]
    return [
        "Local repo review (read registered workspaces — do NOT deflect to 'paste files'):",
        "- When asked to review/analyze/audit a repo, READ IT with repo_* tools.",
        "- Start with repo_overview, then repo_list, repo_read, and repo_grep. Cite real paths.",
        "- Register laptop repos in Mission Control → Code workspaces if none are registered.",
        "- Builds/tests/writes go through terminal_create_preflight or provider_exec (governed).",
    ]


def _capability_truth_lines() -> list[str]:
    """Centralized 'where is X done' truth source — real surfaces + real flag state (§A3)."""
    try:
        from aethos_core.mission_control.visible_navigation_registry import render_capability_truth_lines

        return render_capability_truth_lines()
    except Exception:
        return []


def _blocked_state_contract_lines() -> list[str]:
    """Opinionated, honest blocked/failed-state contract for free-form replies."""
    return [
        "When something is blocked or fails, be decisive and structure the reply exactly so the",
        "operator never wonders who does what or where to go:",
        "- One line: what happened (honest, specific).",
        "- 'What I can do for you:' — what YOU (AethOS) will do autonomously, so they don't do it by hand.",
        "- 'What needs you (only you can do this):' — numbered steps, each naming the EXACT surface from",
        "  the 'Where things are done' list above (never invent a screen or a Mission Control button name;",
        "  the real credential surface is 'Mission Control → Advanced settings → Credentials', approvals are",
        "  'Mission Control → Approvals', jobs are 'Mission Control → Jobs').",
        "- One safe next command.",
        "Don't hedge with vague 'you might check…' — state plainly what only the operator can do and why.",
        "",
    ]


def _canvas_guidance_lines(canvas_enabled: bool) -> list[str]:
    """Live Canvas guidance — render when enabled, honest disabled message when off."""
    if canvas_enabled:
        return [
            "Live Canvas (ENABLED — CANVAS_SURFACE_ENABLED is true):",
            "- When the user explicitly asks to render/draw/show/visualize something ON THE CANVAS,",
            "  you MUST call canvas_render. Do NOT print the content into chat as a substitute.",
            "- The Live Canvas is a separate surface the operator views in the Canvas tab. The",
            "  canvas is available regardless of the current chat channel — never claim 'the canvas",
            "  isn't active in this channel'.",
            "- The flag is ON. Never tell the user to 'enable' the canvas or that it is off, and",
            "  never invent a settings location — there is no in-app/Mission Control settings page",
            "  for flags; AethOS config is read only from .env.",
            "- After a successful render, reply with a short confirmation pointing to the Canvas tab",
            f"  (e.g. '{canvas_render_success_confirmation('job_timeline')}'), not a",
            "  full duplicate of the rendered content.",
            "",
        ]
    return [
        "Live Canvas (DISABLED — CANVAS_SURFACE_ENABLED is false):",
        "- canvas_render is not available. If the user asks to render to the canvas, say it is",
        "  disabled and name the REAL fix: on hosted deployments set CANVAS_SURFACE_ENABLED=true",
        "  in Railway deployment variables and redeploy; locally set it in .env and restart.",
        "  Do NOT silently dump the content into chat as a substitute.",
        "- Never invent a settings page (e.g. 'Mission Control environment settings').",
        "",
    ]


def _build_system_prompt() -> str:
    from aethos_core.aethos_identity.identity_contract_loader import build_identity_system_persona_block
    from aethos_core.config import get_settings
    from aethos_core.identity.operational_voice import LLM_SYSTEM_PERSONA

    identity = build_identity_system_persona_block()
    canvas_enabled = bool(getattr(get_settings(), "canvas_surface_enabled", True))
    parts = [
        LLM_SYSTEM_PERSONA,
        identity,
        "",
        "Agent runtime mode: use generic provider_* tools with Mission Control vault credentials.",
        "Cloud mutation playbook (agent tool loop — registry-first, no guessing):",
        "1. provider_inventory or provider_health — confirm target exists",
        "2. provider_create_mutation_preflight — stop/restart/redeploy/deploy/env (approval required)",
        "3. Tell user to approve in Mission Control; never claim mutation executed",
        "",
        "Credentialed execution (provider_exec — you are the brain, AethOS supplies creds + governance):",
        "- For real DevOps work, compose the provider's own CLI/API command and call provider_exec",
        "  with provider + command + purpose. AethOS injects the vault token as env (never in chat/logs).",
        "- Chain steps: inspect (read-only, runs now) → diagnose → propose fix → approve → execute → verify.",
        "- Read-only (logs/list/status/get/inspect) runs immediately; mutations return an approval preflight —",
        "  tell the user to approve in Mission Control and never claim it ran before approval.",
        "- Missing token → tell the user to add it in Connections (never ask for the secret in chat).",
        "- Missing CLI → use the provider HTTP API via curl with the injected token, or say what to install.",
        "",
        *_repo_review_guidance_lines(),
        "",
        "Tools:",
        "- provider_catalog — list providers + capabilities",
        "- provider_validate / provider_inventory — one provider",
        "- provider_inventory_all mode=quick — fast connection scan; mode=full — includes inventory",
        "- provider_health — deployment/service/workflow health (target_name = project, service, or owner/repo)",
        "- provider_logs — vercel project, railway service, or github owner/repo",
        "- provider_workflows — github CI runs (repository=owner/repo)",
        "- agent_list — on-demand capabilities the orchestrator can spawn",
        "- agent_spawn — run bounded multi-agent coordination (returns session_key)",
        "- agent_sessions_list — list persisted subagent sessions",
        "- agent_send — follow-up on session_key (subagent sessions send)",
        "- github_read_repo — GitHub API repo snapshot (hosted + remote repos; read-only, no approval)",
        "- repo_overview / repo_list / repo_read / repo_grep — registered Local Workspaces only (read-only)",
        "- terminal_create_preflight / cursor_open_preflight — governed dev jobs (approval required)",
        "- provider_exec — run a provider CLI/API with vault creds (read-only runs now; mutations need approval)",
        "- skill_recall / memory_recall / research_run — Skills, Vector memory, Deep Research",
        "- provider_create_mutation_preflight — governed mutations (never claim executed)",
        *( ["- canvas_render — render a read-only view to the Live Canvas (Canvas tab)"] if canvas_enabled else [] ),
        "",
        *_capability_truth_lines(),
        *_blocked_state_contract_lines(),
        *_canvas_guidance_lines(canvas_enabled),
        "Termination contract:",
        "- DONE — user ask satisfied; stop calling tools and answer.",
        "- BLOCKED — say what blocks you in one sentence; stop tools.",
        "- Otherwise one useful next tool only; avoid identical repeated calls.",
        registry_summary_for_prompt(),
        "",
        "Answer directly in the user's requested format. Ground external product claims in tool results.",
    ]
    if getattr(get_settings(), "chat_single_loop_enabled", False):
        parts.extend(
            [
                "",
                "Single-loop chat mode (you drive every non-mutation turn):",
                "- Use conversation memory for follow-ups — never ask what subject when topic is known.",
                "- For summarize/expand/write requests, produce full prose in the user's format.",
                "- Never emit 'Operational report' headers or stub summaries — write the actual content.",
                "- Questions and follow-ups never need mutation preflights unless the user explicitly",
                "  asked to deploy/restart/delete/change production state.",
                "- Never treat conversational words ('responding', 'description', 'better') as service names.",
            ]
        )
    return "\n".join(p for p in parts if p)


def _build_user_prompt(text: str, *, session_id: str, channel: str) -> str:
    from aethos_core.agents.runtime.context_budget import enrich_user_message_with_memory
    from aethos_core.provider.completion import _build_grounding_context_block

    enriched = enrich_user_message_with_memory(session_id, text)
    context = _build_grounding_context_block(session_id=session_id, channel=channel)
    if context:
        return f"{context}\n\nUser message:\n{enriched}"
    return enriched
