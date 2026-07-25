# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any, Iterator

from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, model_validator

from aethos_core.channels.telegram.telegram_auth import TelegramAuthAdapter
from aethos_core.security.credential_vault import get_credential_vault, get_credential_vault_diagnostics
from aethos_core.security.secret_redaction import redact_text

_log = logging.getLogger(__name__)

router = APIRouter(tags=["telegram"])


class StoreTelegramCredentialIn(BaseModel):
    label: str = Field(default="Telegram bot", max_length=120)
    token: str = Field(default="", max_length=4096)
    secret: str = Field(default="", max_length=4096)

    @model_validator(mode="after")
    def _require_token(self) -> StoreTelegramCredentialIn:
        resolved = (self.token or self.secret or "").strip()
        if len(resolved) < 8:
            raise ValueError("Bot token must be at least 8 characters.")
        self.token = resolved
        return self

    def resolved_token(self) -> str:
        return (self.token or self.secret or "").strip()


class TestSendIn(BaseModel):
    chat_id: str = Field(min_length=1, max_length=32)
    message: str = Field(default="AethOS Telegram connection test.", max_length=500)


def _structured_error(*, code: str, detail: str, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"ok": False, "code": code, "detail": redact_text(detail)},
    )


@contextmanager
def _request_tenant_scope(request: Request | None) -> Iterator[str]:
    """Bind vault lookups to the authenticated tenant (same as status endpoint)."""
    from aethos_core.tenancy import DEFAULT_TENANT, tenant_scope
    from aethos_core.tenancy.middleware import tenant_for_request

    tenant = tenant_for_request(request) if request is not None else DEFAULT_TENANT
    with tenant_scope(tenant) as bound:
        yield bound


@router.post("/channels/telegram/webhook")
def post_telegram_webhook(update: dict[str, Any] | None = None) -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_router import handle_telegram_update
    from aethos_core.channels.telegram.telegram_runtime import telegram_configured
    from aethos_core.channels.webhook_tenant import channel_webhook_tenant_scope

    payload = update if isinstance(update, dict) else {}
    with channel_webhook_tenant_scope("telegram"):
        if not telegram_configured():
            raise HTTPException(status_code=503, detail="Telegram channel is not configured")
        try:
            return handle_telegram_update(payload)
        except HTTPException:
            raise
        except Exception as exc:
            _log.exception("telegram_webhook_handler_failed")
            return JSONResponse(
                status_code=200,
                content={
                    "ok": False,
                    "code": "TELEGRAM_WEBHOOK_HANDLER_FAILED",
                    "detail": redact_text(str(exc))[:240],
                },
            )


@router.get("/channels/telegram/status")
def get_telegram_status(request: Request) -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status

    return telegram_channel_status(request=request)


@router.post("/channels/telegram/webhook/register")
def register_telegram_webhook_local_api(request: Request) -> dict[str, Any]:
    """Register Telegram webhook via ngrok tunnel — local dev only."""
    from aethos_core.config import get_settings
    from aethos_core.production.deployment_mode import is_hosted_deployment
    from aethos_core.runtime.tunnel.tunnel_manager import restart_tunnel, start_tunnel, tunnel_status

    if is_hosted_deployment():
        return {
            "ok": False,
            "error": "local_webhook_on_hosted",
            "detail": "Local tunnel webhook is for dev only. Use POST /channels/telegram/webhook/register/production.",
        }

    with _request_tenant_scope(request):
        settings = get_settings()
        if settings.telegram_tunnel_enabled:
            result = start_tunnel() if settings.deployment_mode == "local" else restart_tunnel()
            if not result.get("ok"):
                return {"ok": False, "error": result.get("error") or "tunnel_start_failed", "detail": result}
            state = result.get("state") or {}
            return {
                "ok": bool(state.get("telegram_webhook_status") == "configured"),
                "webhook_url": state.get("webhook_url"),
                "telegram_webhook_status": state.get("telegram_webhook_status"),
                "tunnel_status": state.get("status"),
            }

        snapshot = tunnel_status()
        tunnel = snapshot.get("tunnel") or {}
        webhook_url = tunnel.get("webhook_url") or (snapshot.get("telegram") or {}).get("webhook", {}).get("url")
        if not webhook_url:
            return {
                "ok": False,
                "error": "webhook_url_unknown",
                "detail": "Enable TELEGRAM_TUNNEL_ENABLED and restart the API, or register the production webhook.",
            }
        from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
        from aethos_core.channels.telegram.telegram_transport import set_webhook

        token, _ = resolve_telegram_bot_token()
        if not token:
            return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram bot token missing.", status_code=503)
        wh = set_webhook(token=token, url=str(webhook_url))
        return {
            "ok": bool(wh.get("ok")),
            "webhook_url": webhook_url,
            "telegram": wh,
            "tunnel": tunnel,
        }


@router.post("/channels/telegram/webhook/register/production")
def register_telegram_webhook_production_api(request: Request) -> dict[str, Any]:
    """Register Telegram webhook at the deployment's canonical public API URL."""
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
    from aethos_core.channels.telegram.telegram_transport import set_webhook
    from aethos_core.production.deployment_mode import telegram_canonical_webhook_url

    webhook_url = telegram_canonical_webhook_url(request)
    if not webhook_url:
        return _structured_error(
            code="WEBHOOK_URL_UNKNOWN",
            detail="Could not resolve public API origin. Set PUBLIC_APP_BASE_URL on hosted deploys.",
            status_code=503,
        )

    # Resolve the bot token under the request's tenant first; if that yields
    # nothing (e.g. the request did not carry the owner's auth, or the token was
    # saved under a specific owner while the request resolves DEFAULT), fall back
    # to the channel's unique owner — the same resolution the inbound webhook uses.
    # Registering the webhook is a deployment-level action; it must not depend on
    # whose session happened to click the button.
    with _request_tenant_scope(request):
        token, _ = resolve_telegram_bot_token()
    if not token:
        from aethos_core.channels.webhook_tenant import channel_webhook_tenant_scope

        with channel_webhook_tenant_scope("telegram"):
            token, _ = resolve_telegram_bot_token()
    if not token:
        return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram bot token missing.", status_code=503)

    wh = set_webhook(token=token, url=webhook_url)
    if not wh.get("ok"):
        return _structured_error(
            code="TELEGRAM_SET_WEBHOOK_FAILED",
            detail=str(wh.get("detail") or "setWebhook failed"),
            status_code=502,
        )

    from aethos_core.channels.telegram.telegram_transport import get_webhook_info

    verified = get_webhook_info(token=token)
    registered_url = str(verified.get("url") or "") if verified.get("ok") else ""
    verified_ok = bool(
        verified.get("ok")
        and registered_url
        and registered_url.rstrip("/") == webhook_url.rstrip("/")
    )
    if not verified_ok:
        detail = str(verified.get("detail") or "")
        if registered_url and registered_url.rstrip("/") != webhook_url.rstrip("/"):
            detail = (
                f"Webhook registered as {registered_url} but expected {webhook_url}"
                if not detail
                else detail
            )
        return {
            "ok": False,
            "error": "webhook_verification_failed",
            "detail": detail or "getWebhookInfo did not confirm the production URL",
            "webhook_url": webhook_url,
            "registered_webhook_url": registered_url or None,
            "telegram": wh,
            "mode": "production",
        }

    return {
        "ok": True,
        "webhook_url": registered_url,
        "registered_webhook_url": registered_url,
        "verified": True,
        "telegram": wh,
        "webhook_info": verified,
        "mode": "production",
    }


@router.get("/channels/telegram/sessions")
def get_telegram_sessions() -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_sessions import list_telegram_sessions

    sessions = list_telegram_sessions(limit=50)
    return {"ok": True, "sessions": sessions, "count": len(sessions)}


@router.post("/channels/telegram/delivery/flush")
def post_telegram_delivery_flush() -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_delivery import flush_queue
    from aethos_core.channels.telegram.telegram_runtime import telegram_configured
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
    from aethos_core.channels.telegram.telegram_transport import _bot_api

    if not telegram_configured():
        return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram is not configured.", status_code=503)
    token, _ = resolve_telegram_bot_token()
    if not token:
        return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram is not configured.", status_code=503)
    return {"ok": True, "result": flush_queue(bot_api_fn=_bot_api, limit=10)}


class TelegramPreferencesIn(BaseModel):
    mode: Literal["calm", "verbose", "completion_only"] = "calm"
    session_id: str | None = Field(default=None, max_length=64)


@router.get("/channels/telegram/preferences")
def get_telegram_preferences() -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_preferences import preferences_snapshot

    return preferences_snapshot()


@router.post("/channels/telegram/preferences")
def post_telegram_preferences(body: TelegramPreferencesIn) -> dict[str, Any]:
    from aethos_core.channels.telegram.telegram_preferences import (
        NotifyMode,
        preferences_snapshot,
        set_default_mode,
        set_session_mode,
    )

    mode: NotifyMode = body.mode  # type: ignore[assignment]
    if body.session_id:
        set_session_mode(body.session_id.strip(), mode)
    else:
        set_default_mode(mode)
    return {"ok": True, **preferences_snapshot()}


@router.get("/channels/telegram/connection")
def get_telegram_connection() -> dict[str, Any]:
    data = TelegramAuthAdapter().connection_status().to_dict()
    data["credential_vault"] = get_credential_vault_diagnostics()
    return data


@router.post("/channels/telegram/credentials", response_model=None)
def post_store_telegram_credential(body: StoreTelegramCredentialIn):
    vault_diag = get_credential_vault_diagnostics()
    if not vault_diag.get("available"):
        return _structured_error(
            code="CREDENTIAL_VAULT_UNAVAILABLE",
            detail="Credential vault is not available.",
            status_code=503,
        )
    try:
        record = get_credential_vault().store_api_token(
            provider="telegram",
            label=body.label or "Telegram bot",
            token=body.resolved_token(),
            scope=["send_message", "receive_updates"],
            write_allowed=False,
        )
    except ValueError as exc:
        return _structured_error(code="INVALID_CREDENTIAL_PAYLOAD", detail=str(exc), status_code=422)
    except Exception as exc:
        _log.exception("telegram_credential_save_failed")
        return _structured_error(code="CREDENTIAL_SAVE_FAILED", detail=str(exc), status_code=500)

    adapter = TelegramAuthAdapter()
    try:
        test_result = adapter.test_credential(record.credential_id)
    except Exception as exc:
        test_result = {"ok": False, "detail": redact_text(str(exc))}

    from aethos_core.channels.telegram.telegram_runtime import telegram_channel_status

    return {
        "ok": True,
        "credential": record.to_public_dict(),
        "test": test_result,
        "connection": adapter.connection_status().to_dict(),
        "status": telegram_channel_status(include_webhook=False),
        "credential_vault": vault_diag,
    }


@router.post("/channels/telegram/credentials/{credential_id}/test", response_model=None)
def post_test_telegram_credential(credential_id: str):
    adapter = TelegramAuthAdapter()
    try:
        result = adapter.test_credential(credential_id)
    except KeyError:
        return _structured_error(code="CREDENTIAL_NOT_FOUND", detail="Credential not found", status_code=404)
    except Exception as exc:
        return _structured_error(code="CREDENTIAL_TEST_FAILED", detail=str(exc), status_code=500)
    return {"ok": True, "test": result, "connection": adapter.connection_status().to_dict()}


@router.post("/channels/telegram/credentials/{credential_id}/revoke", response_model=None)
def post_revoke_telegram_credential(credential_id: str):
    adapter = TelegramAuthAdapter()
    if not adapter.revoke_credential(credential_id):
        return _structured_error(code="CREDENTIAL_NOT_FOUND", detail="Credential not found", status_code=404)
    return {
        "ok": True,
        "revoked": True,
        "credential_id": credential_id,
        "connection": adapter.connection_status().to_dict(),
    }


@router.post("/channels/telegram/test-send", response_model=None)
def post_telegram_test_send(body: TestSendIn):
    from aethos_core.channels.telegram.telegram_runtime import telegram_configured
    from aethos_core.channels.telegram.telegram_token import resolve_telegram_bot_token
    from aethos_core.channels.telegram.telegram_transport import send_telegram_message

    if not telegram_configured():
        return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram is not configured.", status_code=503)
    token, _ = resolve_telegram_bot_token()
    if not token:
        return _structured_error(code="TELEGRAM_NOT_CONFIGURED", detail="Telegram is not configured.", status_code=503)
    send_out = send_telegram_message(token=token, chat_id=body.chat_id.strip(), text=body.message.strip())
    ok = bool(send_out.get("ok"))
    detail = str(send_out.get("detail") or "")
    from aethos_core.channels.telegram.telegram_activity import record_outbound

    record_outbound(chat_id=body.chat_id.strip(), ok=ok, error="" if ok else detail)
    if not ok:
        return _structured_error(
            code="TELEGRAM_SEND_FAILED",
            detail=detail or "Test message could not be delivered.",
            status_code=502,
        )
    return {"ok": True, "sent": True, "chat_id": body.chat_id.strip(), "detail": detail or "ok"}
