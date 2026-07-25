# SPDX-License-Identifier: Apache-2.0
"""Operational memory with embedding recall — local hash vectors or OpenRouter embeddings."""

from __future__ import annotations

import json
import math
import uuid
from pathlib import Path
from typing import Any

from aethos_core.config import get_settings


def _memory_path() -> Path:
    root = Path(__file__).resolve().parents[2] / "data"
    return root / "vector_memory.json"


def _embed_text(text: str) -> list[float]:
    settings = get_settings()
    provider = str(getattr(settings, "vector_memory_embedding_provider", "local") or "local").lower()
    if provider == "openrouter" and str(getattr(settings, "openrouter_api_key", "") or "").strip():
        remote = _openrouter_embed(text, settings)
        if remote:
            return remote
    return _local_hash_embed(text)


def _local_hash_embed(text: str, dim: int = 256) -> list[float]:
    vec = [0.0] * dim
    for token in text.lower().split():
        idx = hash(token) % dim
        vec[idx] += 1.0
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def _openrouter_embed(text: str, settings: Any) -> list[float] | None:
    import httpx

    model = str(getattr(settings, "vector_memory_embedding_model", "text-embedding-3-small") or "text-embedding-3-small")
    headers = {"Authorization": f"Bearer {settings.openrouter_api_key}", "Content-Type": "application/json"}
    body = {"model": model, "input": text[:8000]}
    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.post("https://openrouter.ai/api/v1/embeddings", headers=headers, json=body)
        if response.status_code >= 400:
            return None
        data = response.json()
        rows = data.get("data") if isinstance(data, dict) else []
        if isinstance(rows, list) and rows:
            embedding = rows[0].get("embedding") if isinstance(rows[0], dict) else None
            if isinstance(embedding, list) and embedding:
                return [float(x) for x in embedding]
    except httpx.HTTPError:
        return None
    return None


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


def remember(*, text: str, tags: list[str] | None = None, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    if not getattr(get_settings(), "vector_memory_enabled", False):
        return {"ok": False, "error": "vector_memory_disabled"}
    from aethos_core.runtime.operational_environment import resolve_operational_environment
    from aethos_core.tenancy.tenant_data_store import append_vector_entry

    env = resolve_operational_environment()
    body = text.strip()
    entry = {
        "id": uuid.uuid4().hex,
        "text": body,
        "tags": list(tags or []),
        "metadata": dict(metadata or {}),
        "environment": env.canonical,
        "embedding": _embed_text(body),
    }
    append_vector_entry(entry)
    return {"ok": True, "id": entry["id"], "environment": env.canonical}


def recall(*, query: str, limit: int = 5, environment: str | None = None) -> dict[str, Any]:
    if not getattr(get_settings(), "vector_memory_enabled", False):
        return {"ok": False, "error": "vector_memory_disabled", "matches": []}
    settings = get_settings()
    backend = str(getattr(settings, "vector_memory_backend", "local") or "local").lower()
    # Shared Chroma has no per-tenant partition yet — use tenant-scoped SQLite in MT mode.
    if getattr(settings, "multi_tenant_enabled", False):
        backend = "local"
    if backend == "chroma":
        chroma_matches = _recall_chroma(query=query, limit=limit)
        if chroma_matches is not None:
            return {"ok": True, "backend": "chroma", "matches": chroma_matches}
    rows = _load_rows()
    if not rows:
        return {"ok": True, "matches": []}
    query_vec = _embed_text(query)
    env_filter = (environment or "").strip().lower()
    scored: list[tuple[float, dict[str, Any]]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        if env_filter and str(row.get("environment") or "").lower() not in {env_filter, ""}:
            continue
        embedding = row.get("embedding")
        if not isinstance(embedding, list):
            embedding = _embed_text(str(row.get("text") or ""))
        score = _cosine(query_vec, [float(x) for x in embedding])
        if score > 0.05:
            scored.append((score, {**row, "score": round(score, 4), "embedding": None}))
    scored.sort(key=lambda item: item[0], reverse=True)
    return {"ok": True, "backend": "local", "matches": [row for _, row in scored[:limit]]}


def _recall_chroma(*, query: str, limit: int) -> list[dict[str, Any]] | None:
    settings = get_settings()
    try:
        import chromadb
    except ImportError:
        return None
    try:
        host = str(getattr(settings, "chromadb_host", "localhost") or "localhost")
        port = int(getattr(settings, "chromadb_port", 8100) or 8100)
        client = chromadb.HttpClient(host=host, port=port)
        collection = client.get_or_create_collection("aethos_operational_memory")
        if collection.count() == 0:
            return []
        query_vec = _embed_text(query)
        result = collection.query(query_embeddings=[query_vec], n_results=max(1, min(limit, 20)))
        ids = list((result.get("ids") or [[]])[0])
        docs = list((result.get("documents") or [[]])[0])
        dists = list((result.get("distances") or [[]])[0])
        out: list[dict[str, Any]] = []
        for idx, doc_id in enumerate(ids):
            out.append(
                {
                    "id": doc_id,
                    "text": docs[idx] if idx < len(docs) else "",
                    "score": round(1.0 - float(dists[idx]), 4) if idx < len(dists) else 0.0,
                }
            )
        return out
    except Exception:
        return None


def _load_rows() -> list[dict[str, Any]]:
    from aethos_core.tenancy.tenant_data_store import list_vector_entries

    rows = list_vector_entries()
    if rows:
        return rows
    # Legacy global file → import into default tenant once.
    path = _memory_path()
    if not path.is_file():
        return []
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, list):
            from aethos_core.tenancy.tenant_data_store import append_vector_entry

            imported = [row for row in raw if isinstance(row, dict)]
            for row in imported[-500:]:
                append_vector_entry(row)
            return imported
    except (OSError, json.JSONDecodeError):
        return []
    return []


def memory_snapshot(*, limit: int = 5) -> dict[str, Any]:
    """Read-only status for operator UI — recent entries without a query."""
    settings = get_settings()
    enabled = bool(getattr(settings, "vector_memory_enabled", False))
    backend = str(getattr(settings, "vector_memory_backend", "local") or "local")
    rows = _load_rows()
    recent = [
        {
            "id": row.get("id"),
            "text": str(row.get("text") or "")[:240],
            "tags": list(row.get("tags") or [])[:6],
            "environment": row.get("environment"),
        }
        for row in rows[-max(1, min(limit, 20)) :]
    ]
    recent.reverse()
    return {
        "ok": True,
        "enabled": enabled,
        "backend": backend,
        "entry_count": len(rows),
        "recent": recent,
    }
