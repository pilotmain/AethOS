# SPDX-License-Identifier: Apache-2.0
"""Channel pairing + allowlist store (handoff §6).

Untrusted inbound senders on external channels are not processed until the operator
pairs them. A pairing request issues a short numeric code; approving the code (via
Mission Control, API, or `aethos pairing approve <channel> <code>`) moves the sender
to a local allowlist. Local-first, gitignored JSON — mirrors the deployment-target
registry atomic-write pattern. Never auto-approves.
"""

from __future__ import annotations

import json
import random
import time
from pathlib import Path
from typing import Any


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (getattr(get_settings(), "channel_pairing_store_dir", "data/channel_pairing") or "data/channel_pairing").strip()
    return Path(raw)


def _store_path() -> Path:
    from aethos_core.tenancy.tenant_data_store import resolve_data_tenant

    tenant = resolve_data_tenant()
    return _store_root() / tenant / "pairing.json"


def _empty_index() -> dict[str, Any]:
    return {"version": 1, "allowed": [], "pending": [], "updated_at": None}


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return _empty_index()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty_index()
    if not isinstance(raw, dict):
        return _empty_index()
    raw.setdefault("allowed", [])
    raw.setdefault("pending", [])
    raw.setdefault("version", 1)
    return raw


def _atomic_write(payload: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)


def _norm(value: str) -> str:
    return (value or "").strip().lower()


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    _atomic_write(data)


def is_sender_allowed(channel: str, external_user_id: str) -> bool:
    ch, uid = _norm(channel), _norm(external_user_id)
    if not ch or not uid:
        return False
    data = _load()
    for row in data.get("allowed", []):
        if _norm(str(row.get("channel"))) == ch and _norm(str(row.get("external_user_id"))) == uid:
            return True
    # Explicit open allowlist wildcard for a channel ("*") is opt-in only.
    for row in data.get("allowed", []):
        if _norm(str(row.get("channel"))) == ch and str(row.get("external_user_id")) == "*":
            return True
    return False


def _generate_code() -> str:
    return f"{random.randint(0, 9999):04d}"


def request_pairing(channel: str, external_user_id: str, *, preview: str = "") -> dict[str, Any]:
    """Issue (or return the existing) pairing code for an unknown sender. Idempotent per sender."""
    ch, uid = _norm(channel), _norm(external_user_id)
    if not ch or not uid:
        return {"ok": False, "error": "channel_and_sender_required"}
    data = _load()
    for row in data.get("pending", []):
        if _norm(str(row.get("channel"))) == ch and _norm(str(row.get("external_user_id"))) == uid:
            return {"ok": True, "status": "pending", "code": str(row.get("code")), "channel": ch}
    code = _generate_code()
    data["pending"].append(
        {
            "channel": ch,
            "external_user_id": uid,
            "code": code,
            "preview": (preview or "")[:120],
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
    )
    _save(data)
    return {"ok": True, "status": "pending", "code": code, "channel": ch}


def approve_pairing(channel: str, code: str) -> dict[str, Any]:
    """Operator action — move a pending sender to the allowlist by pairing code."""
    ch, c = _norm(channel), (code or "").strip()
    if not ch or not c:
        return {"ok": False, "error": "channel_and_code_required"}
    data = _load()
    match = None
    for row in data.get("pending", []):
        if _norm(str(row.get("channel"))) == ch and str(row.get("code")) == c:
            match = row
            break
    if match is None:
        return {"ok": False, "error": "pairing_code_not_found", "channel": ch}
    data["pending"] = [r for r in data["pending"] if r is not match]
    uid = str(match.get("external_user_id"))
    if not is_sender_allowed(ch, uid):
        data["allowed"].append(
            {
                "channel": ch,
                "external_user_id": uid,
                "paired_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
    _save(data)
    return {"ok": True, "status": "paired", "channel": ch, "external_user_id": uid}


def revoke_sender(channel: str, external_user_id: str) -> dict[str, Any]:
    ch, uid = _norm(channel), _norm(external_user_id)
    data = _load()
    before = len(data.get("allowed", []))
    data["allowed"] = [
        r
        for r in data.get("allowed", [])
        if not (_norm(str(r.get("channel"))) == ch and _norm(str(r.get("external_user_id"))) == uid)
    ]
    _save(data)
    return {"ok": True, "revoked": before - len(data["allowed"]), "channel": ch, "external_user_id": uid}


def list_pending() -> list[dict[str, Any]]:
    return list(_load().get("pending", []))


def list_allowed() -> list[dict[str, Any]]:
    return list(_load().get("allowed", []))


def pairing_status_payload() -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    data = _load()
    return {
        "ok": True,
        "channel_gateway_enabled": bool(getattr(settings, "channel_gateway_enabled", False)),
        "channel_dm_policy": str(getattr(settings, "channel_dm_policy", "pairing")),
        "pending_count": len(data.get("pending", [])),
        "allowed_count": len(data.get("allowed", [])),
        "pending": data.get("pending", []),
        "allowed": data.get("allowed", []),
    }
