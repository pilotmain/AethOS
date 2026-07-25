# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
import re
from collections.abc import Iterator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field

from aethos_core.chat.cognition_exception_boundary import sanitize_chat_result_for_transport
from aethos_core.chat.service import ChatTurnResult, resolve_chat_turn, resolve_deterministic_turn

router = APIRouter(tags=["chat"])


class ChatIn(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    message: str = Field(min_length=1, max_length=12_000)
    session_id: str | None = Field(default="default", max_length=64)
    interaction_mode: str = Field(default="agent", max_length=16)
    model_override: str | None = Field(default=None, max_length=120)
    # Inbound origin metadata (handoff §1/§11). channel = messaging system,
    # surface = UI modality. Both normalized downstream; default webchat/chat.
    channel: str = Field(default="chat", max_length=24)
    surface: str = Field(default="webchat", max_length=24)


class ChatOut(BaseModel):
    reply: str
    intent: str | None = None
    agent_key: str = "aethos"
    terminal: bool = True
    provider_stream: bool = False
    used_llm: bool = False
    provider: str | None = None
    model: str | None = None
    meta: dict[str, object] | None = None
    action: dict[str, object] | None = None
    job: dict[str, object] | None = None


class ChatThreadCreateIn(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    session_id: str | None = Field(default=None, max_length=64)


class ChatThreadUpsertIn(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    messages: list[dict[str, object]] = Field(default_factory=list)


def _to_out(result: ChatTurnResult) -> ChatOut:
    meta = dict(result.meta or {})
    action = None
    job = None
    aid = meta.get("proposed_action_id")
    if isinstance(aid, str) and aid:
        action = {
            "id": aid,
            "type": meta.get("proposed_action_type", "unknown"),
            "lifecycle_tracked": True,
        }
    jid = meta.get("proposed_job_id")
    if isinstance(jid, str) and jid:
        job = {
            "id": jid,
            "type": meta.get("proposed_job_type", "unknown"),
            "lifecycle_tracked": True,
        }
    return ChatOut(
        reply=result.reply,
        intent=result.intent,
        agent_key=result.agent_key,
        terminal=result.terminal,
        provider_stream=result.provider_stream,
        used_llm=result.used_llm,
        provider=result.provider,
        model=result.model,
        meta=meta or None,
        action=action,
        job=job,
    )


def _resolve_chat_out(body: ChatIn, sid: str, *, tenant_id: str | None = None) -> ChatOut:
    """Run the full governed turn pipeline and shape the transport result.

    Shared by the standard POST and the SSE stream so both deliver the identical
    governed reply (safety/grounding/footer/polish all run here).
    """
    from aethos_core.chat.chat_turn_tenant import chat_turn_scope, resolve_chat_turn_tenant

    tid = resolve_chat_turn_tenant(tenant_id)
    try:
        with chat_turn_scope(tid):
            result = sanitize_chat_result_for_transport(
                resolve_chat_turn(
                    body.message,
                    session_id=sid,
                    channel=body.channel,
                    surface=body.surface,
                    interaction_mode=body.interaction_mode,
                    model_override=body.model_override,
                    tenant_id=tid,
                )
            )
    except Exception as exc:
        from aethos_core.chat.cognition_exception_boundary import (
            CognitionBoundaryContext,
            compose_cognition_crash_fallback,
        )
        from aethos_core.providers.railway.greenfield_deployment.greenfield_router import (
            preemption_chat_turn_result,
        )

        greenfield = preemption_chat_turn_result(
            body.message,
            session_id=sid,
            route_source="chat_transport_greenfield_preemption",
        )
        if greenfield is not None:
            result = sanitize_chat_result_for_transport(greenfield)
        else:
            result = compose_cognition_crash_fallback(
                exc,
                CognitionBoundaryContext(text=body.message, session_id=sid, channel="chat"),
            )
    return _to_out(result)


@router.post("/chat", response_model=ChatOut)
def post_chat(body: ChatIn) -> ChatOut:
    import time as _time

    from aethos_core.config import get_settings

    get_settings()
    sid = (body.session_id or "default").strip()[:64] or "default"
    started = _time.monotonic()
    try:
        return _resolve_chat_out(body, sid)
    finally:  # §8 SLO signal — chat turn latency.
        try:
            from aethos_core.observability.telemetry import record_chat_latency_ms

            record_chat_latency_ms((_time.monotonic() - started) * 1000.0)
        except Exception:  # noqa: BLE001
            pass


def _stream_text_chunks(text: str, *, group: int = 4) -> Iterator[str]:
    """Yield the reply in small token groups, preserving whitespace/newlines."""
    tokens = re.findall(r"\S+\s*|\s+", text or "")
    buf: list[str] = []
    for tok in tokens:
        buf.append(tok)
        if len(buf) >= group:
            yield "".join(buf)
            buf = []
    if buf:
        yield "".join(buf)


@router.post("/chat/stream")
def post_chat_stream(body: ChatIn) -> StreamingResponse:
    """§2 — stream the governed reply over SSE (token-by-token render + abort).

    The complete governed pipeline runs first (so footer/polish/grounding and
    tool-step meta are identical to POST /chat); the final reply is then emitted
    incrementally. Disabled => 503 so the client falls back to POST /chat.
    """
    from aethos_core.config import get_settings

    if not getattr(get_settings(), "chat_streaming_enabled", False):
        raise HTTPException(status_code=503, detail="streaming_disabled")
    sid = (body.session_id or "default").strip()[:64] or "default"

    def gen() -> Iterator[str]:
        import time as _time

        started = _time.monotonic()
        if getattr(get_settings(), "live_progress_enabled", True):
            yield from _gen_with_progress(body, sid, started)
            return
        # ── flag off: behavior is exactly today's (resolve fully, then stream) ──
        try:
            out = _resolve_chat_out(body, sid)
        except Exception:
            yield f"data: {json.dumps({'type': 'error', 'error': 'chat_failed'})}\n\n"
            yield 'data: {"type": "done"}\n\n'
            return
        for chunk in _stream_text_chunks(out.reply):
            yield f"data: {json.dumps({'type': 'delta', 'text': chunk})}\n\n"
        yield f"data: {json.dumps({'type': 'final', 'out': out.model_dump()})}\n\n"
        yield 'data: {"type": "done"}\n\n'
        # §C3 — record turn latency for the streaming path too (parity with POST /chat).
        try:
            from aethos_core.observability.telemetry import record_chat_latency_ms

            record_chat_latency_ms((_time.monotonic() - started) * 1000.0)
        except Exception:  # noqa: BLE001
            pass

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no", "Connection": "keep-alive"},
    )


def _gen_with_progress(body: "ChatIn", sid: str, started: float) -> Iterator[str]:
    """§2 — live progress: resolve in a worker thread while draining step events.

    The full governed pipeline runs in a background thread with a progress sink
    installed; the generator forwards ``step``/``thought`` events as they happen,
    then streams the final reply (delta/final/done) exactly as the non-progress
    path does. Back-compat: events ride the same ``data:`` channel with a
    ``type`` field, so a client that only handles delta/final/done is unaffected.
    """
    import queue as _queue
    import threading as _threading
    import time as _time
    from contextvars import copy_context

    from aethos_core.execution_brain.agent_tool_executor import (
        reset_progress_sink,
        set_progress_sink,
    )

    from aethos_core.chat.chat_turn_tenant import chat_turn_scope, resolve_chat_turn_tenant

    captured_tenant = resolve_chat_turn_tenant()

    events: _queue.Queue = _queue.Queue()
    holder: dict = {}

    def _worker() -> None:
        token = set_progress_sink(lambda ev: events.put(ev))
        try:
            with chat_turn_scope(captured_tenant):
                holder["out"] = _resolve_chat_out(body, sid, tenant_id=captured_tenant)
        except Exception as exc:  # noqa: BLE001 — surfaced to the client below.
            holder["error"] = exc
        finally:
            reset_progress_sink(token)
            events.put({"__end__": True})

    # ContextVars (tenant scope, canvas client session id) must propagate into the worker.
    worker_ctx = copy_context()
    worker = _threading.Thread(
        target=lambda: worker_ctx.run(_worker),
        name=f"chat-progress-{sid}",
        daemon=True,
    )
    worker.start()

    while True:
        try:
            ev = events.get(timeout=30.0)
        except _queue.Empty:
            if not worker.is_alive():
                break
            continue
        if ev.get("__end__"):
            break
        if ev.get("type") in ("step", "thought"):
            yield f"data: {json.dumps(ev)}\n\n"

    out = holder.get("out")
    if out is None:
        yield f"data: {json.dumps({'type': 'error', 'error': 'chat_failed'})}\n\n"
        yield 'data: {"type": "done"}\n\n'
        return
    for chunk in _stream_text_chunks(out.reply):
        yield f"data: {json.dumps({'type': 'delta', 'text': chunk})}\n\n"
    yield f"data: {json.dumps({'type': 'final', 'out': out.model_dump()})}\n\n"
    yield 'data: {"type": "done"}\n\n'
    try:
        from aethos_core.observability.telemetry import record_chat_latency_ms

        record_chat_latency_ms((_time.monotonic() - started) * 1000.0)
    except Exception:  # noqa: BLE001
        pass


@router.post("/chat/deterministic", response_model=ChatOut)
def post_chat_deterministic(body: ChatIn) -> ChatOut:
    from aethos_core.config import get_settings

    get_settings()
    sid = (body.session_id or "default").strip()[:64] or "default"
    result = resolve_deterministic_turn(body.message, session_id=sid)
    if result is None:
        raise HTTPException(status_code=422, detail="requires_stream")
    return _to_out(result)


@router.get("/chat/threads")
def get_chat_threads(limit: int = 40) -> dict[str, object]:
    from aethos_core.chat.chat_thread_store import list_chat_threads

    return list_chat_threads(limit=min(max(limit, 1), 40))


@router.post("/chat/threads")
def post_chat_thread(body: ChatThreadCreateIn) -> dict[str, object]:
    from aethos_core.chat.chat_thread_store import create_chat_thread

    return create_chat_thread(title=body.title, session_id=body.session_id)


@router.get("/chat/threads/{session_id}")
def get_chat_thread_route(session_id: str) -> dict[str, object]:
    from aethos_core.chat.chat_thread_store import get_chat_thread

    row = get_chat_thread(session_id.strip()[:64] or "default")
    if row is None:
        raise HTTPException(status_code=404, detail="thread_not_found")
    return row


@router.put("/chat/threads/{session_id}")
def put_chat_thread_route(session_id: str, body: ChatThreadUpsertIn) -> dict[str, object]:
    from aethos_core.chat.chat_thread_store import upsert_chat_thread

    return upsert_chat_thread(
        session_id=session_id.strip()[:64] or "default",
        title=body.title,
        messages=[dict(row) for row in body.messages if isinstance(row, dict)],
    )


@router.delete("/chat/threads/{session_id}")
def delete_chat_thread_route(session_id: str) -> dict[str, object]:
    from aethos_core.chat.chat_thread_store import delete_chat_thread

    result = delete_chat_thread(session_id.strip()[:64] or "default")
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "not_found"))
    return result
