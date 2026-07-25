# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — Documents tab store (handoff §8).

Draft-only local document store: markdown / text / csv / html drafts the operator
writes and the agent assists with. NEVER auto-publishes — there is no send/publish
path here; publishing would be a separate governed preflight. Gated by
WORKSPACE_SUITE_ENABLED, default off. Local-first, gitignored JSON store mirroring
the canvas/channel store atomic-write pattern.
"""

from __future__ import annotations

import secrets
import time
from pathlib import Path
from typing import Any

_NS_DOCUMENTS = "workspace_documents"

ALLOWED_FORMATS = frozenset({"markdown", "text", "csv", "html"})
_MAX_DOCS = 500
_MAX_CONTENT_CHARS = 200_000


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (
        getattr(get_settings(), "workspace_suite_store_dir", "data/workspace_suite")
        or "data/workspace_suite"
    ).strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "documents.json"


def _load() -> dict[str, Any]:
    from aethos_core.storage.hosted_json_store import load_json_blob

    data = load_json_blob(_NS_DOCUMENTS, _store_path(), lambda: {"documents": {}})
    return data if isinstance(data, dict) else {"documents": {}}


def _save(data: dict[str, Any]) -> None:
    from aethos_core.storage.hosted_json_store import save_json_blob

    save_json_blob(_NS_DOCUMENTS, _store_path(), data)


def _enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "workspace_suite_enabled", False))


def _normalize_format(fmt: str) -> str:
    f = (fmt or "markdown").strip().lower()
    return f if f in ALLOWED_FORMATS else "markdown"


def _summary(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "format": doc.get("format"),
        "char_count": len(str(doc.get("content") or "")),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
        "draft_only": True,
    }


def create_document(
    *,
    title: str,
    content: str = "",
    fmt: str = "markdown",
) -> dict[str, Any]:
    """Create a draft document. Draft-only — never published."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    clean_title = (title or "Untitled").strip()[:200] or "Untitled"
    body = str(content or "")[:_MAX_CONTENT_CHARS]
    doc_id = f"doc-{secrets.token_hex(5)}"
    now = time.time()
    doc = {
        "id": doc_id,
        "title": clean_title,
        "format": _normalize_format(fmt),
        "content": body,
        "draft_only": True,
        "created_at": now,
        "updated_at": now,
    }
    store = _load()
    docs = dict(store.get("documents") or {})
    if len(docs) >= _MAX_DOCS:
        return {"ok": False, "error": "document_limit_reached", "limit": _MAX_DOCS}
    docs[doc_id] = doc
    store["documents"] = docs
    _save(store)
    return {"ok": True, "document": _summary(doc)}


def update_document(
    *,
    doc_id: str,
    title: str | None = None,
    content: str | None = None,
    fmt: str | None = None,
) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    docs = dict(store.get("documents") or {})
    doc = docs.get((doc_id or "").strip())
    if not isinstance(doc, dict):
        return {"ok": False, "error": "document_not_found", "id": doc_id}
    if title is not None:
        doc["title"] = (title or "Untitled").strip()[:200] or "Untitled"
    if content is not None:
        doc["content"] = str(content)[:_MAX_CONTENT_CHARS]
    if fmt is not None:
        doc["format"] = _normalize_format(fmt)
    doc["updated_at"] = time.time()
    doc["draft_only"] = True
    docs[doc["id"]] = doc
    store["documents"] = docs
    _save(store)
    return {"ok": True, "document": _summary(doc)}


def get_document(*, doc_id: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    doc = (store.get("documents") or {}).get((doc_id or "").strip())
    if not isinstance(doc, dict):
        return {"ok": False, "error": "document_not_found", "id": doc_id}
    return {"ok": True, "document": doc}


def list_documents(*, limit: int = 100) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled", "documents": []}
    store = _load()
    docs = [d for d in (store.get("documents") or {}).values() if isinstance(d, dict)]
    docs.sort(key=lambda d: float(d.get("updated_at") or 0), reverse=True)
    capped = max(1, min(int(limit or 100), _MAX_DOCS))
    return {
        "ok": True,
        "document_count": len(docs),
        "documents": [_summary(d) for d in docs[:capped]],
    }


def delete_document(*, doc_id: str) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    docs = dict(store.get("documents") or {})
    if (doc_id or "").strip() not in docs:
        return {"ok": False, "error": "document_not_found", "id": doc_id}
    docs.pop((doc_id or "").strip(), None)
    store["documents"] = docs
    _save(store)
    return {"ok": True, "deleted": doc_id}


def clear_documents_for_tests() -> None:
    from aethos_core.storage.hosted_json_store import clear_json_blob_for_tests

    clear_json_blob_for_tests(_NS_DOCUMENTS, _store_path())


def propose_ai_edit(
    *,
    doc_id: str,
    instruction: str,
    session_id: str = "default",
) -> dict[str, Any]:
    """Suggest an edit diff — operator must accept before content changes (§B3)."""
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    got = get_document(doc_id=doc_id)
    if not got.get("ok"):
        return got
    doc = got["document"]
    original = str(doc.get("content") or "")
    hint = (instruction or "").strip()
    if len(hint) < 4:
        return {"ok": False, "error": "instruction_required"}
  # Deterministic assist stub when LLM off; real loop uses workspace_doc tool with model.
    from aethos_core.config import get_settings

    proposed = original
    if getattr(get_settings(), "use_real_llm", False):
        from aethos_core.provider.completion import complete_chat

        prov = complete_chat(
            f"Improve this document per instruction: {hint}\n\nDocument:\n{original[:8000]}",
            session_id=session_id,
            system_overlay="Return only the revised document body. No preamble.",
        )
        proposed = (prov.text or "").strip() or original
    else:
        proposed = original + ("\n\n<!-- AI suggestion: " + hint[:120] + " -->" if original else hint)

    suggestion_id = f"sug-{secrets.token_hex(4)}"
    store = _load()
    pending = dict(store.get("pending_edits") or {})
    pending[suggestion_id] = {
        "id": suggestion_id,
        "doc_id": doc_id,
        "original": original,
        "proposed": proposed[:_MAX_CONTENT_CHARS],
        "instruction": hint,
        "created_at": time.time(),
    }
    store["pending_edits"] = pending
    _save(store)
    return {
        "ok": True,
        "suggestion_id": suggestion_id,
        "doc_id": doc_id,
        "diff": {"before": original, "after": proposed},
        "accept_required": True,
    }


def apply_ai_edit(*, suggestion_id: str, accept: bool = True) -> dict[str, Any]:
    if not _enabled():
        return {"ok": False, "error": "workspace_suite_disabled"}
    store = _load()
    pending = dict(store.get("pending_edits") or {})
    row = pending.get((suggestion_id or "").strip())
    if not isinstance(row, dict):
        return {"ok": False, "error": "suggestion_not_found"}
    pending.pop((suggestion_id or "").strip(), None)
    store["pending_edits"] = pending
    _save(store)
    if not accept:
        return {"ok": True, "accepted": False, "doc_id": row.get("doc_id")}
    return update_document(doc_id=str(row.get("doc_id") or ""), content=str(row.get("proposed") or ""))
