# SPDX-License-Identifier: Apache-2.0
"""Chat turn resolution — deterministic lanes then provider fallback."""

from __future__ import annotations

from dataclasses import dataclass, field

from aethos_core.chat.handlers import resolve_handler
from aethos_core.chat.lanes import is_deterministic_lane
from aethos_core.provider.completion import ProviderResult, complete_chat


@dataclass
class ChatTurnResult:
    reply: str
    intent: str
    agent_key: str = "aethos"
    terminal: bool = True
    provider_stream: bool = False
    used_llm: bool = False
    provider: str | None = None
    model: str | None = None
    meta: dict[str, object] = field(default_factory=dict)


def _handled_to_result(
    handled: tuple[str, str, dict[str, str]],
    *,
    agent_key: str = "aethos",
) -> ChatTurnResult:
    body, intent, meta = handled
    return ChatTurnResult(
        reply=body,
        intent=intent,
        agent_key=agent_key,
        provider_stream=False,
        used_llm=False,
        meta=dict(meta),
    )


def resolve_deterministic_turn(
    user_text: str, *, session_id: str = "default"
) -> ChatTurnResult | None:
    from aethos_core.providers.github.workflow_discovery.workflow_discovery_runtime_context import (
        enforce_workflow_discovery_absolute_lane_turn,
    )
    from aethos_core.chat.lane_hydration import maybe_hydrate_lane_contexts

    maybe_hydrate_lane_contexts(text=user_text, session_id=session_id)
    absolute = enforce_workflow_discovery_absolute_lane_turn(user_text, session_id=session_id)
    if absolute is not None:
        return absolute

    if not is_deterministic_lane(user_text, session_id=session_id):
        return None
    handled = resolve_handler(user_text, session_id=session_id)
    if not handled:
        return None
    body, intent, meta = handled
    return ChatTurnResult(
        reply=body,
        intent=intent,
        provider_stream=False,
        used_llm=False,
        meta=meta,
    )


def resolve_chat_turn(
    user_text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
    surface: str = "webchat",
    apply_relational_layer: bool = True,
    interaction_mode: str = "agent",
    model_override: str | None = None,
    tenant_id: str | None = None,
) -> ChatTurnResult:
    """Unified chat — step 1 safety, step 2 operational fast path, step 3 agent runtime.

    ``surface`` records the inbound UI modality (webchat | voice | canvas | cli | ...)
    so every surface runs the identical Step 1/2/3 pipeline (handoff §1/§5/§11). It is
    stamped onto the turn meta and never grants a privileged/ungoverned path.
    """
    from aethos_core.canvas.session_context import canvas_client_session_scope
    from aethos_core.channels.session_alias import resolve_canonical_session_id

    surface = (surface or "webchat").strip().lower()[:24] or "webchat"
    client_session_id = (session_id or "default").strip()[:64] or "default"
    session_id = resolve_canonical_session_id(client_session_id)
    raw = (user_text or "").strip()
    from aethos_core.aethos_identity.identity_contract_loader import load_identity_contracts

    load_identity_contracts()
    from aethos_core.operational_skill_runtime import bootstrap_operational_runtime
    from aethos_core.chat.lane_hydration import maybe_hydrate_lane_contexts
    from aethos_core.chat.route_timing import begin_turn_timing, mark_router_started

    bootstrap_operational_runtime()
    begin_turn_timing()
    with canvas_client_session_scope(client_session_id):
        maybe_hydrate_lane_contexts(text=raw, session_id=session_id)
        mark_router_started()
        emotional_context = None
        if apply_relational_layer:
            from aethos_core.relational.relational_runtime import prepare_relational_turn

            emotional_context = prepare_relational_turn(user_text=raw, session_id=session_id, channel=channel)

        from aethos_core.chat.chat_turn_steps import (
            try_safety_short_circuit_turn,
            try_single_loop_turn,
        )

        final: ChatTurnResult
        step_result = try_safety_short_circuit_turn(
            raw, session_id=session_id, channel=channel, surface=surface
        )
        if step_result is not None:
            final = _finalize_result(
                step_result,
                emotional_context=emotional_context,
                surface=surface,
            )
        else:
            step_result = try_single_loop_turn(
                raw,
                session_id=session_id,
                channel=channel,
                surface=surface,
                model_override=model_override,
                tenant_id=tenant_id,
            )
            final = _finalize_result(
                step_result
                or ChatTurnResult(
                    reply="I couldn't resolve that turn.",
                    intent="unresolved_turn",
                    provider_stream=False,
                    used_llm=False,
                    meta={"lane": "none", "single_loop": "true"},
                ),
                surface=surface,
            )

        _record_conversation_turn_safe(session_id=session_id, user_text=raw, result=final)
        return final


def _record_conversation_turn_safe(
    *, session_id: str, user_text: str, result: "ChatTurnResult"
) -> None:
    """Fold the resolved turn into the rolling conversation summary (best-effort)."""
    try:
        from aethos_core.memory.conversation_summary_memory import record_turn

        record_turn(
            session_id=session_id,
            user_text=user_text,
            reply=result.reply or "",
            intent=result.intent or "",
        )
    except Exception:
        pass


def _finalize_result(
    result: ChatTurnResult,
    *,
    emotional_context: dict[str, object] | None = None,
    surface: str = "webchat",
) -> ChatTurnResult:
    """Finalize the turn, then record per-turn latency telemetry (§C5)."""
    final = _finalize_result_inner(result, surface=surface)
    _stamp_turn_timing(final)
    return final


def _finalize_result_inner(result: ChatTurnResult, *, surface: str = "webchat") -> ChatTurnResult:
    """Deliver model output as-is; governance footer only on real mutation actions (§A1)."""
    try:
        if isinstance(result.meta, dict):
            result.meta.setdefault("surface", surface)
    except Exception:
        pass

    from aethos_core.chat.route_timing import add_finalizer_ms, mark_router_complete
    from time import perf_counter

    mark_router_complete()
    finalizer_started = perf_counter()
    try:
        reply = (result.reply or "").strip()
        if str((result.meta or {}).get("real_mutation_action") or "").lower() == "true":
            from aethos_core.identity.trust_language import LIGHT_TRUST_REMINDER

            if LIGHT_TRUST_REMINDER not in reply:
                reply = f"{reply}\n\n{LIGHT_TRUST_REMINDER}"
        return ChatTurnResult(
            reply=reply,
            intent=result.intent,
            agent_key=result.agent_key,
            terminal=result.terminal,
            provider_stream=result.provider_stream,
            used_llm=result.used_llm,
            provider=result.provider,
            model=result.model,
            meta=dict(result.meta),
        )
    finally:
        add_finalizer_ms(int((perf_counter() - finalizer_started) * 1000))


def _stamp_turn_timing(result: ChatTurnResult) -> None:
    try:
        from aethos_core.chat.route_timing import timing_for_route_trace
        from aethos_core.config import get_settings
        from aethos_core.observability.telemetry import record_turn_timing

        timing = timing_for_route_trace()
        if not timing:
            return
        record_turn_timing(timing)
        if getattr(get_settings(), "chat_verbose_timing_enabled", False) and isinstance(result.meta, dict):
            result.meta["timing_total_ms"] = timing.get("total_ms")
            result.meta["timing_router_ms"] = timing.get("router_ms")
            result.meta["timing_model_ms"] = timing.get("model_ms")
            result.meta["timing_tools_ms"] = timing.get("tools_ms")
            result.meta["timing_breakdown"] = (
                f"this turn took {timing.get('total_ms')}ms (routing {timing.get('router_ms')}ms"
                f" / model {timing.get('model_ms')}ms / tools {timing.get('tools_ms')}ms)"
            )
    except Exception:
        pass


