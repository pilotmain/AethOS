# SPDX-License-Identifier: Apache-2.0
"""Telegram Bot API transport — send only."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)


def _bot_api(*, token: str, method: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    if not token:
        return {"ok": False, "detail": "missing token", "status_code": 0}
    url = f"https://api.telegram.org/bot{token}/{method}"
    try:
        with httpx.Client(timeout=15.0) as client:
            r = client.post(url, json=payload or {})
        data = r.json() if r.content else {}
        if r.status_code >= 400 or not data.get("ok"):
            detail = redact_text(str(data.get("description") or r.text[:200]))
            _log.warning("telegram_api_failed method=%s status=%s detail=%s", method, r.status_code, detail)
            return {"ok": False, "detail": detail or f"HTTP {r.status_code}", "status_code": r.status_code}
        return {"ok": True, "result": data.get("result"), "detail": "ok", "status_code": r.status_code}
    except httpx.HTTPError as exc:
        detail = redact_text(str(exc))
        _log.warning("telegram_api_error method=%s err=%s", method, detail)
        return {"ok": False, "detail": detail, "status_code": 0}


def test_bot_token(*, token: str) -> dict[str, Any]:
    out = _bot_api(token=token, method="getMe")
    if not out.get("ok"):
        return {"ok": False, "detail": out.get("detail") or "getMe failed"}
    result = out.get("result") if isinstance(out.get("result"), dict) else {}
    username = str(result.get("username") or "")
    return {
        "ok": True,
        "detail": f"Bot @{username} verified." if username else "Bot verified.",
        "bot_username": username or None,
    }


def get_webhook_info(*, token: str) -> dict[str, Any]:
    out = _bot_api(token=token, method="getWebhookInfo")
    if not out.get("ok"):
        return {"ok": False, "detail": out.get("detail") or "getWebhookInfo failed"}
    result = out.get("result") if isinstance(out.get("result"), dict) else {}
    return {
        "ok": True,
        "url": str(result.get("url") or ""),
        "has_custom_certificate": bool(result.get("has_custom_certificate")),
        "pending_update_count": int(result.get("pending_update_count") or 0),
        "last_error_date": result.get("last_error_date"),
        "last_error_message": redact_text(str(result.get("last_error_message") or "")) or None,
    }


def set_webhook(*, token: str, url: str) -> dict[str, Any]:
    if not url.startswith("https://"):
        return {"ok": False, "detail": "Webhook URL must be HTTPS"}
    out = _bot_api(token=token, method="setWebhook", payload={"url": url})
    if not out.get("ok"):
        return {"ok": False, "detail": out.get("detail") or "setWebhook failed"}
    return {"ok": True, "url": url, "detail": "Webhook configured"}


def delete_webhook(*, token: str) -> dict[str, Any]:
    out = _bot_api(token=token, method="deleteWebhook")
    if not out.get("ok"):
        return {"ok": False, "detail": out.get("detail") or "deleteWebhook failed"}
    return {"ok": True, "detail": "Webhook removed"}


def send_telegram_message(*, token: str, chat_id: str, text: str) -> dict[str, Any]:
    """Send a Telegram message — returns ``{ok, detail}`` with Telegram's real error text."""
    if not token or not chat_id or not text:
        return {"ok": False, "detail": "missing token, chat_id, or message text"}
    from aethos_core.channels.telegram.telegram_delivery import deliver_message

    out = deliver_message(token=token, chat_id=chat_id, text=text, bot_api_fn=_bot_api)
    if isinstance(out, dict):
        return {"ok": bool(out.get("ok")), "detail": str(out.get("detail") or ("ok" if out.get("ok") else "send_failed"))}
    return {"ok": bool(out), "detail": "ok" if out else "send_failed"}
