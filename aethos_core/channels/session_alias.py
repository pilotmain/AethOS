# SPDX-License-Identifier: Apache-2.0
"""Session alias registry — unify Telegram and web chat continuity keys."""

from __future__ import annotations

import re
from pathlib import Path
from time import time
from typing import Any

_ALIAS_RE = re.compile(r"[^a-zA-Z0-9._-]+")
_NS_SESSION_ALIAS = "session_alias"


def _sanitize(session_id: str) -> str:
    raw = (session_id or "default").strip()[:64]
    cleaned = _ALIAS_RE.sub("-", raw).strip("-")
    return cleaned or "default"


def _store_path() -> Path:
    root = Path("data/session_links").expanduser()
    return root / "index.json"


def _empty() -> dict[str, Any]:
    return {"groups": {}, "alias_index": {}}


def _load() -> dict[str, Any]:
    from aethos_core.storage.hosted_json_store import load_json_blob

    raw = load_json_blob(_NS_SESSION_ALIAS, _store_path(), _empty)
    raw.setdefault("groups", {})
    raw.setdefault("alias_index", {})
    return raw


def _save(data: dict[str, Any]) -> None:
    from aethos_core.storage.hosted_json_store import save_json_blob

    save_json_blob(_NS_SESSION_ALIAS, _store_path(), data)


def _pick_canonical(session_ids: list[str], preferred: str | None = None) -> str:
    if preferred:
        pref = _sanitize(preferred)
        if pref in session_ids:
            return pref
    for sid in session_ids:
        if sid.startswith("sess-") or sid.startswith("web-"):
            return sid
    return session_ids[0]


def resolve_canonical_session_id(session_id: str) -> str:
    sid = _sanitize(session_id)
    data = _load()
    alias_index = data.get("alias_index") or {}
    canonical = alias_index.get(sid)
    if isinstance(canonical, str) and canonical.strip():
        return _sanitize(canonical)
    return sid


def session_ids_for_lookup(session_id: str) -> list[str]:
    sid = _sanitize(session_id)
    canonical = resolve_canonical_session_id(sid)
    data = _load()
    groups = data.get("groups") or {}
    group = groups.get(canonical)
    if isinstance(group, dict):
        aliases = group.get("aliases") or []
        rows = [_sanitize(str(a)) for a in aliases if str(a).strip()]
        rows.append(canonical)
        return list(dict.fromkeys(rows))
    return [sid]


def get_session_group(session_id: str) -> dict[str, Any]:
    sid = _sanitize(session_id)
    canonical = resolve_canonical_session_id(sid)
    linked = session_ids_for_lookup(sid)
    return {
        "ok": True,
        "canonical_session_id": canonical,
        "session_id": sid,
        "linked_session_ids": linked,
    }


def link_session_ids(*, session_ids: list[str], canonical_session_id: str | None = None) -> dict[str, Any]:
    cleaned = list(dict.fromkeys(_sanitize(s) for s in session_ids if (s or "").strip()))
    if len(cleaned) < 1:
        return {"ok": False, "error": "session_ids_required"}
    if len(cleaned) == 1 and not canonical_session_id:
        cleaned.append(cleaned[0])

    canonical = _pick_canonical(cleaned, canonical_session_id)
    data = _load()
    groups: dict[str, Any] = dict(data.get("groups") or {})
    alias_index: dict[str, str] = dict(data.get("alias_index") or {})

    merged: set[str] = set(cleaned)
    for sid in cleaned:
        existing = resolve_canonical_session_id(sid)
        if existing in groups:
            merged.update(str(a) for a in (groups[existing].get("aliases") or []))
            merged.add(existing)

    merged_list = list(dict.fromkeys(_sanitize(s) for s in merged if s))
    canonical = _pick_canonical(merged_list, canonical_session_id)
    if canonical not in merged_list:
        merged_list.insert(0, canonical)

    groups[canonical] = {
        "canonical": canonical,
        "aliases": merged_list,
        "updated_at": time(),
    }
    for sid in merged_list:
        alias_index[sid] = canonical

    data["groups"] = groups
    data["alias_index"] = alias_index
    data["updated_at"] = time()
    _save(data)
    return get_session_group(canonical)


def clear_session_alias_for_tests() -> None:
    from aethos_core.storage.hosted_json_store import clear_json_blob_for_tests

    clear_json_blob_for_tests(_NS_SESSION_ALIAS, _store_path())
