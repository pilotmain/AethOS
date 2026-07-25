# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — mission knowledge space search and semantic operational intelligence."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.knowledge_spaces.knowledge_index import build_knowledge_corpus
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
    AUTONOMOUS_ACTION_ENABLED_FIX_141,
    DEFAULT_SEARCH_LIMIT,
    KNOWLEDGE_SPACES_FIX,
    KNOWLEDGE_SPACES_INVARIANT,
    KNOWLEDGE_SPACES_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_141,
    RELATED_MISSION_SCORE_THRESHOLD,
    SEEN_BEFORE_SCORE_THRESHOLD,
)
from aethos_core.mission_control.knowledge_spaces.semantic_retrieval import rank_documents
from aethos_core.mission_control.operational_memory.cross_session.cross_session_service import (
    ingest_session_operational_memory,
)


@dataclass(frozen=True)
class KnowledgeSpacesSearchResult:
    ok: bool
    session_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _extract_query(*, query: str, text: str) -> str:
    raw = (query or text or "").strip()
    if not raw:
        return ""
    for prefix in (
        "search ",
        "find ",
        "have we seen ",
        "show ",
        "semantic search ",
        "recall ",
    ):
        if raw.lower().startswith(prefix):
            raw = raw[len(prefix) :].strip()
    return raw


def _related_missions(
    *,
    hits: list[dict[str, Any]],
    spaces: list[dict[str, Any]],
    focal_space_id: str,
) -> list[dict[str, Any]]:
    by_space: dict[str, float] = defaultdict(float)
    for hit in hits:
        sid = str(hit.get("space_id") or "")
        score = float(hit.get("relevance_score") or 0)
        if sid:
            by_space[sid] = max(by_space[sid], score)

    related: list[dict[str, Any]] = []
    for space in spaces:
        sid = str(space.get("space_id") or "")
        if not sid or sid == focal_space_id:
            continue
        score = by_space.get(sid, 0.0)
        if score >= RELATED_MISSION_SCORE_THRESHOLD:
            related.append(
                {
                    "space_id": sid,
                    "relevance_score": round(score, 4),
                    "document_count": space.get("document_count"),
                    "session_ids": space.get("session_ids"),
                    "read_only": True,
                }
            )
    related.sort(key=lambda r: -float(r.get("relevance_score") or 0))
    return related[:12]


def _seen_before(*, hits: list[dict[str, Any]], query: str) -> dict[str, Any]:
    strong = [h for h in hits if float(h.get("relevance_score") or 0) >= SEEN_BEFORE_SCORE_THRESHOLD]
    return {
        "query": query,
        "likely_seen_before": len(strong) > 0,
        "match_count": len(strong),
        "top_matches": [
            {
                "category": h.get("category"),
                "text": h.get("text"),
                "relevance_score": h.get("relevance_score"),
                "space_id": h.get("space_id"),
                "session_id": h.get("session_id"),
                "recorded_at": h.get("recorded_at"),
            }
            for h in strong[:5]
        ],
        "read_only": True,
        "note": "Similarity-based recall — not proof of identical execution",
    }


def _recommendations(
    *,
    hits: list[dict[str, Any]],
    seen: dict[str, Any],
    related: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    recs: list[dict[str, Any]] = []
    if seen.get("likely_seen_before"):
        top = (seen.get("top_matches") or [{}])[0]
        recs.append(
            {
                "kind": "historical_context",
                "recommendation": (
                    f"Review prior {top.get('category', 'operational')} context in space "
                    f"`{top.get('space_id', '')}` before taking new governed action."
                ),
                "executable": False,
                "read_only": True,
            }
        )
    categories = {str(h.get("category")) for h in hits[:8]}
    if "blocker" in categories:
        recs.append(
            {
                "kind": "blocker_awareness",
                "recommendation": "Recurring blockers appear in search results — check approval inbox and governed gates.",
                "executable": False,
                "read_only": True,
            }
        )
    if "incident" in categories:
        recs.append(
            {
                "kind": "incident_awareness",
                "recommendation": "Production incidents match this query — review incident command lane before delivery changes.",
                "executable": False,
                "read_only": True,
            }
        )
    if related:
        recs.append(
            {
                "kind": "related_mission",
                "recommendation": f"{len(related)} related mission knowledge space(s) found — compare lineage in cross-session memory.",
                "executable": False,
                "read_only": True,
            }
        )
    if not recs:
        recs.append(
            {
                "kind": "baseline",
                "recommendation": "No strong historical match — continue with governed snapshot and evidence bundle review.",
                "executable": False,
                "read_only": True,
            }
        )
    return recs


def search_mission_knowledge_spaces(
    *,
    session_id: str,
    query: str = "",
    text: str = "",
    space_id: str | None = None,
    category: str | None = None,
    ingest_current: bool = True,
    limit: int = DEFAULT_SEARCH_LIMIT,
) -> KnowledgeSpacesSearchResult:
    sid = (session_id or "default").strip()[:64] or "default"
    q = _extract_query(query=query, text=text)
    if not q and text:
        q = text.strip()
    if not q:
        return KnowledgeSpacesSearchResult(
            ok=False,
            session_id=sid,
            blockers=["missing_query"],
            detail="Provide a search query for semantic operational retrieval.",
        )

    if ingest_current:
        ingest_session_operational_memory(session_id=sid)

    docs, spaces = build_knowledge_corpus(session_id=sid, include_live=True)

    focal_space = space_id
    if not focal_space:
        for space in spaces:
            if sid in (space.get("session_ids") or []):
                focal_space = str(space.get("space_id") or "")
                break

    filtered = docs
    if focal_space:
        filtered = [d for d in filtered if str(d.get("space_id") or "") == focal_space] or docs
    if category:
        cat = category.strip().lower()
        filtered = [d for d in filtered if str(d.get("category") or "").lower() == cat] or filtered

    hits = rank_documents(query=q, documents=filtered, limit=limit)
    if not hits:
        hits = rank_documents(query=q, documents=docs, limit=limit)

    seen = _seen_before(hits=hits, query=q)
    related = _related_missions(hits=hits, spaces=spaces, focal_space_id=str(focal_space or ""))
    recommendations = _recommendations(hits=hits, seen=seen, related=related)

    by_category: dict[str, int] = defaultdict(int)
    for h in hits:
        by_category[str(h.get("category") or "unknown")] += 1

    payload: dict[str, Any] = {
        "schema_version": KNOWLEDGE_SPACES_SCHEMA_VERSION,
        "fix": KNOWLEDGE_SPACES_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_141,
        "autonomous_action_enabled": AUTONOMOUS_ACTION_ENABLED_FIX_141,
        "automatic_mutation_planning_enabled": AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_141,
        "invariant": KNOWLEDGE_SPACES_INVARIANT,
        "session_id": sid,
        "query": q,
        "focal_space_id": focal_space,
        "knowledge_spaces": spaces[:40],
        "knowledge_space_count": len(spaces),
        "document_corpus_size": len(docs),
        "search_results": hits,
        "results_by_category": dict(by_category),
        "seen_before": seen,
        "related_missions": related,
        "recommendations": recommendations,
        "operational_context_recall": {
            "query": q,
            "top_context": hits[:3],
            "recall_confidence": round(float(hits[0].get("relevance_score") or 0), 4) if hits else 0.0,
            "read_only": True,
        },
    }
    return KnowledgeSpacesSearchResult(
        ok=True,
        session_id=sid,
        payload=payload,
        detail="Mission knowledge space search complete (read-only, recommendation-only).",
    )
