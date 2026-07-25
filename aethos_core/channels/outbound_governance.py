# SPDX-License-Identifier: Apache-2.0
"""Governed outbound message sends (handoff §5/§8/§16).

Outbound `channel_send` (and email send) NEVER fire directly. They create an
outbound-send preflight that the operator must approve in Mission Control (or via
`aethos outbound approve <id>` / the execute API). The actual send is additionally
gated by OUTBOUND_SEND_EXECUTION_ENABLED and the channel allowlist — a send never
fires to a non-allowlisted peer. Mirrors the terminal-preflight governed pattern
(separate gitignored store, preflight → approve → execute).
"""

from __future__ import annotations

import json
import secrets
import time
from pathlib import Path
from typing import Any


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (getattr(get_settings(), "channel_outbound_store_dir", "data/channel_outbound") or "data/channel_outbound").strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "outbound.json"


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"preflights": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"preflights": {}}
    return data if isinstance(data, dict) else {"preflights": {}}


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def _new_id() -> str:
    return f"obs-{secrets.token_hex(5)}"


def create_outbound_send_preflight(
    *,
    channel: str,
    to: str,
    body: str,
    subject: str = "",
    session_id: str = "operator",
) -> dict[str, Any]:
    """Create an outbound-send preflight — design only, never sends."""
    from aethos_core.channels.pairing_store import is_sender_allowed
    from aethos_core.config import get_settings

    settings = get_settings()
    ch = (channel or "").strip().lower()
    recipient = (to or "").strip()
    text = (body or "").strip()
    if not ch or not recipient or not text:
        return {"ok": False, "error": "channel_to_body_required"}
    if not getattr(settings, "channel_gateway_enabled", False):
        return {"ok": False, "error": "channel_gateway_disabled"}

    allowlisted = is_sender_allowed(ch, recipient)
    preflight_id = _new_id()
    record = {
        "id": preflight_id,
        "channel": ch,
        "to": recipient,
        "subject": (subject or "")[:200],
        "body": text[:4000],
        "session_id": session_id,
        "status": "pending_approval",
        "allowlisted": allowlisted,
        "blast_radius": f"1 outbound message to {recipient} on {ch}",
        "rollback": "Message not sent; sending requires explicit operator approval.",
        "created_at": time.time(),
        "result": None,
    }
    data = _load()
    preflights = dict(data.get("preflights") or {})
    preflights[preflight_id] = record
    data["preflights"] = preflights
    _save(data)
    return {
        "ok": True,
        "preflight_id": preflight_id,
        "status": "pending_approval",
        "allowlisted": allowlisted,
        "requires_approval": True,
        "sent": False,
    }


def get_outbound_preflight(preflight_id: str) -> dict[str, Any] | None:
    return (_load().get("preflights") or {}).get(preflight_id)


def list_outbound_preflights(*, limit: int = 20) -> list[dict[str, Any]]:
    rows = list((_load().get("preflights") or {}).values())
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[:limit]


def approve_outbound_send(preflight_id: str) -> dict[str, Any]:
    """Operator approval — perform the governed send if all gates pass."""
    from aethos_core.channels.pairing_store import is_sender_allowed
    from aethos_core.config import get_settings

    settings = get_settings()
    data = _load()
    preflights = dict(data.get("preflights") or {})
    record = preflights.get(preflight_id)
    if not record:
        return {"ok": False, "error": "preflight_not_found"}
    if record.get("status") == "sent":
        return {"ok": True, "status": "sent", "preflight": record, "already_sent": True}
    if not getattr(settings, "outbound_send_execution_enabled", False):
        return {"ok": False, "error": "outbound_send_execution_disabled"}

    channel = str(record.get("channel"))
    recipient = str(record.get("to"))
    # A governed send never fires to a non-allowlisted peer (handoff §6/§8).
    if not is_sender_allowed(channel, recipient):
        record["status"] = "blocked_not_allowlisted"
        preflights[preflight_id] = record
        data["preflights"] = preflights
        _save(data)
        return {"ok": False, "error": "recipient_not_allowlisted", "channel": channel, "to": recipient}

    from aethos_core.channels.channel_registry import ensure_channels_registered, get_channel_adapter

    ensure_channels_registered()
    adapter = get_channel_adapter(channel)
    if adapter is None:
        return {"ok": False, "error": "channel_adapter_missing", "channel": channel}

    try:
        sent = bool(adapter.send_message(chat_id=recipient, text=str(record.get("body") or "")))
    except Exception as exc:  # adapter/transport failure
        record["status"] = "failed"
        record["result"] = {"ok": False, "error": str(exc)[:300]}
        preflights[preflight_id] = record
        data["preflights"] = preflights
        _save(data)
        return {"ok": False, "error": "send_failed", "detail": str(exc)[:300]}

    record["status"] = "sent" if sent else "failed"
    record["result"] = {"ok": sent}
    record["sent_at"] = time.time()
    preflights[preflight_id] = record
    data["preflights"] = preflights
    _save(data)
    return {"ok": sent, "status": record["status"], "channel": channel, "to": recipient}


def outbound_status_payload(*, limit: int = 20) -> dict[str, Any]:
    from aethos_core.config import get_settings

    settings = get_settings()
    return {
        "ok": True,
        "channel_gateway_enabled": bool(getattr(settings, "channel_gateway_enabled", False)),
        "outbound_send_execution_enabled": bool(getattr(settings, "outbound_send_execution_enabled", False)),
        "preflights": list_outbound_preflights(limit=limit),
    }
