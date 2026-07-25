# SPDX-License-Identifier: Apache-2.0
"""Self-organizing memory — auto-group stored memories by topic + compress on demand.

A read/organize layer over the existing vector store (``aethos_core.memory.vector_store``).
It does NOT change how memories are written; it derives a topic for each entry (from its
first tag, else its most salient keyword), groups entries by topic for the Memory Viewer,
and can compress a topic's entries into a short digest (deterministic by default; LLM when
a provider is configured). Tenant-scoped, since the underlying store is.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

_TOKEN_RX = re.compile(r"[a-z0-9]+")
_STOP = frozenset(
    """
    the a an and or of to for in on at is are was were be been being do does did with from by as it
    this that these those my your our their will would should could can about into over under not no
    yes we you i they he she them us me my mine ours have has had get got make made just like
    """.split()
)


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RX.findall((text or "").lower()) if len(t) >= 4 and t not in _STOP]


def topic_for(text: str, tags: list[str] | None = None) -> str:
    """Derive a stable topic label for a memory: first tag, else top keyword, else 'general'."""
    if tags:
        first = str(tags[0]).strip()
        if first:
            return first.lower()
    toks = _tokens(text)
    if not toks:
        return "general"
    # Most frequent salient token (ties → earliest), as the topic anchor.
    counts: dict[str, int] = defaultdict(int)
    order: dict[str, int] = {}
    for i, t in enumerate(toks):
        counts[t] += 1
        order.setdefault(t, i)
    best = sorted(counts.items(), key=lambda kv: (-kv[1], order[kv[0]]))[0][0]
    return best


def _rows() -> list[dict[str, Any]]:
    from aethos_core.memory.vector_store import _load_rows

    return [r for r in _load_rows() if isinstance(r, dict)]


def organize_memories(*, max_topics: int = 50, per_topic: int = 20) -> list[dict[str, Any]]:
    """Group all stored memories by derived topic. Newest entries first within a topic."""
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for idx, row in enumerate(_rows()):
        topic = topic_for(str(row.get("text") or ""), list(row.get("tags") or []))
        groups[topic].append(
            {
                "id": row.get("id"),
                "text": str(row.get("text") or "")[:500],
                "tags": list(row.get("tags") or [])[:6],
                "environment": row.get("environment"),
                "_order": idx,
            }
        )
    out: list[dict[str, Any]] = []
    for topic, entries in groups.items():
        entries.sort(key=lambda e: e["_order"], reverse=True)
        for e in entries:
            e.pop("_order", None)
        out.append({"topic": topic, "count": len(entries), "entries": entries[:per_topic]})
    out.sort(key=lambda g: g["count"], reverse=True)
    return out[:max_topics]


def memory_overview() -> dict[str, Any]:
    """Compact status for the Memory Viewer: counts + topic chips."""
    from aethos_core.config import get_settings

    topics = organize_memories()
    return {
        "ok": True,
        "enabled": bool(getattr(get_settings(), "vector_memory_enabled", False)),
        "entry_count": sum(t["count"] for t in topics),
        "topic_count": len(topics),
        "topics": [{"topic": t["topic"], "count": t["count"]} for t in topics],
    }


def compress_topic(topic: str, *, use_llm: bool | None = None) -> dict[str, Any]:
    """Summarize one topic's memories into a short digest (the 'memory digest pass')."""
    topic_key = (topic or "").strip().lower()
    match = next((t for t in organize_memories() if t["topic"] == topic_key), None)
    if not match:
        return {"ok": False, "error": "topic_not_found", "topic": topic_key}
    lines = [str(e["text"]) for e in match["entries"]]
    joined = "\n".join(f"- {ln}" for ln in lines)

    from aethos_core.config import get_settings

    want_llm = getattr(get_settings(), "memory_compression_llm", False) if use_llm is None else use_llm
    digest = joined
    if want_llm:
        try:
            from aethos_core.provider.completion import complete_chat, provider_configured

            if provider_configured():
                overlay = (
                    f"Summarize what's known about '{topic_key}' from these memory notes into 2-4 "
                    "tight bullet points. Keep only durable facts; drop noise."
                )
                res = complete_chat(joined, include_identity=False, system_overlay=overlay)
                digest = (res.text or "").strip() or joined
        except Exception:  # noqa: BLE001
            digest = joined
    return {"ok": True, "topic": topic_key, "count": match["count"], "digest": digest}
