# SPDX-License-Identifier: Apache-2.0
"""Long-term memory — vector + keyword hybrid recall (§B5)."""

from __future__ import annotations

from typing import Any

from aethos_core.memory.vector_store import memory_snapshot, recall, remember


def remember_fact(text: str, *, tags: list[str] | None = None) -> dict[str, Any]:
    return remember(text=text, tags=tags or ["long_term"])


def recall_facts(query: str, *, limit: int = 8) -> dict[str, Any]:
    out = recall(query=query, limit=limit)
    matches = out.get("matches") if isinstance(out, dict) else []
    return {"ok": bool(out.get("ok")), "query": query, "memories": matches or [], "count": len(matches or [])}


def list_all_memories(*, limit: int = 100) -> dict[str, Any]:
    snap = memory_snapshot(limit=limit)
    rows = snap.get("entries") or snap.get("matches") or []
    return {"ok": True, "memories": rows, "count": len(rows)}


def export_memory_bundle() -> dict[str, Any]:
    snap = memory_snapshot(limit=500)
    return {"ok": True, "bundle": snap}
