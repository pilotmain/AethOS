# SPDX-License-Identifier: Apache-2.0
"""Self-organizing memory API — overview, topic groups, compression, remember."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from aethos_core.memory.self_organizing import compress_topic, memory_overview, organize_memories

router = APIRouter(tags=["memory"])


class RememberIn(BaseModel):
    text: str
    tags: list[str] | None = None


@router.get("/memory/overview")
def memory_overview_api() -> dict[str, Any]:
    return memory_overview()


@router.get("/memory/topics")
def memory_topics_api() -> dict[str, Any]:
    return {"ok": True, "topics": organize_memories()}


@router.post("/memory/compress/{topic}")
def memory_compress_api(topic: str) -> dict[str, Any]:
    return compress_topic(topic)


@router.post("/memory/remember")
def memory_remember_api(req: RememberIn) -> dict[str, Any]:
    from aethos_core.memory.vector_store import remember

    return remember(text=req.text, tags=req.tags or [])
