# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from aethos_core.research.provider_registry import list_registered_providers
from aethos_core.research.research_artifacts import list_research_artifacts
from aethos_core.research.research_config import build_research_status
from aethos_core.research.research_runtime import get_research_replay, run_research_query

router = APIRouter(tags=["research"])


class ResearchQueryIn(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(default="default", max_length=64)
    channel: str = Field(default="api", max_length=32)


@router.get("/research/status")
def get_research_status() -> dict[str, Any]:
    return build_research_status()


@router.get("/research/providers")
def get_research_providers() -> dict[str, Any]:
    return {"providers": list_registered_providers(), "count": len(list_registered_providers())}


@router.post("/research/query")
def post_research_query(body: ResearchQueryIn) -> dict[str, Any]:
    result = run_research_query(body.message, session_id=body.session_id, channel=body.channel)
    return result.to_dict()


@router.get("/research/replay/{replay_id}")
def get_research_replay_route(replay_id: str) -> dict[str, Any]:
    replay = get_research_replay(replay_id.strip())
    if replay is None:
        raise HTTPException(status_code=404, detail="Research replay not found")
    return {"replay": replay}


@router.get("/research/session-memory/{session_id}")
def get_research_session_memory_route(session_id: str) -> dict[str, Any]:
    from aethos_core.channels.session_alias import get_session_group
    from aethos_core.research.research_session_memory import get_last_research_run

    sid = session_id.strip()[:128] or "default"
    memory = get_last_research_run(sid)
    group = get_session_group(sid)
    return {
        "ok": True,
        "session_id": sid,
        "memory": memory,
        "canonical_session_id": group.get("canonical_session_id"),
        "linked_session_ids": group.get("linked_session_ids"),
    }


@router.get("/research/comparison-html/{replay_id}")
def get_comparison_html_route(replay_id: str) -> FileResponse:
    from aethos_core.research.comparison_html import (
        build_comparison_html,
        load_comparison_context,
        load_persisted_comparison_html_path,
        persist_comparison_html,
    )

    rid = replay_id.strip()
    path = load_persisted_comparison_html_path(rid)
    if path is None:
        ctx = load_comparison_context(rid)
        if ctx is None:
            raise HTTPException(status_code=404, detail="Comparison HTML not found")
        page = build_comparison_html(ctx)
        saved = persist_comparison_html(replay_id=rid, html=page)
        path = load_persisted_comparison_html_path(rid)
        if path is None:
            raise HTTPException(status_code=404, detail=saved.get("error") or "comparison_html_write_failed")
    return FileResponse(
        path,
        media_type="text/html",
        filename=f"comparison-{rid}.html",
    )


@router.get("/research/artifacts")
def get_research_artifacts(limit: int = 30, artifact_type: str | None = None) -> dict[str, Any]:
    items = list_research_artifacts(limit=min(max(limit, 1), 200), artifact_type=artifact_type)
    return {"artifacts": items, "count": len(items)}


class ResearchNoteIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)
    replay_id: str | None = Field(default=None, max_length=64)
    query: str | None = Field(default=None, max_length=500)


class BlindEvalIn(BaseModel):
    # model_a / model_b are operator-facing field names; opt out of pydantic's
    # "model_" protected namespace so they don't emit harmless startup warnings.
    model_config = ConfigDict(protected_namespaces=())

    prompt: str = Field(min_length=8, max_length=4000)
    model_a: str | None = Field(default=None, max_length=128)
    model_b: str | None = Field(default=None, max_length=128)


@router.get("/research/notes")
def get_research_notes(session_id: str | None = None, limit: int = 20) -> dict[str, Any]:
    from aethos_core.research.research_notes_store import list_notes

    return list_notes(session_id=session_id, limit=limit)


@router.post("/research/notes/{session_id}")
def post_research_note(session_id: str, body: ResearchNoteIn) -> dict[str, Any]:
    from aethos_core.research.research_notes_store import pin_note

    return pin_note(
        session_id=session_id.strip()[:64] or "default",
        text=body.text,
        replay_id=body.replay_id,
        query=body.query,
    )


@router.delete("/research/notes/{session_id}/{note_id}")
def delete_research_note_route(session_id: str, note_id: str) -> dict[str, Any]:
    from aethos_core.research.research_notes_store import delete_note

    result = delete_note(session_id=session_id.strip()[:64] or "default", note_id=note_id)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "not_found"))
    return result


@router.post("/research/blind-eval")
def post_blind_model_eval(body: BlindEvalIn) -> dict[str, Any]:
    from aethos_core.research.blind_model_eval import run_blind_model_eval

    return run_blind_model_eval(prompt=body.prompt, model_a=body.model_a, model_b=body.model_b)
