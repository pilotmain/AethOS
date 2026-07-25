# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from aethos_core.channels.channel_registry import channel_registry_payload, channel_status_payload
from aethos_core.channels.registry import format_channel_summary

router = APIRouter(tags=["channels"])


@router.get("/channels")
def get_channels() -> dict:
    return channel_registry_payload()


@router.get("/channels/summary")
def get_channels_summary() -> dict[str, str]:
    return {"ok": True, "summary": format_channel_summary()}


@router.get("/channels/{name}")
def get_channel_status(name: str) -> dict:
    payload = channel_status_payload(name)
    if not payload.get("ok"):
        raise HTTPException(status_code=404, detail="Unknown channel")
    return payload


@router.post("/channels/discord/interactions")
async def post_discord_interactions(request: Request) -> dict[str, Any]:
    import json

    from aethos_core.channels.channel_registry import get_channel_adapter
    from aethos_core.channels.discord.discord_runtime import (
        discord_configured,
        discord_signature_enforced,
        verify_discord_signature,
    )
    from aethos_core.channels.inbound import handle_channel_message

    body = await request.body()
    # Discord requires Ed25519 verification of timestamp+body on every interaction
    # (incl. the PING handshake) before it will accept the endpoint.
    if discord_signature_enforced():
        signature = request.headers.get("X-Signature-Ed25519", "")
        timestamp = request.headers.get("X-Signature-Timestamp", "")
        if not verify_discord_signature(body=body, signature=signature, timestamp=timestamp):
            raise HTTPException(status_code=401, detail="Invalid Discord signature")

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    if payload.get("type") == 1:
        return {"type": 1}

    if not discord_configured():
        raise HTTPException(status_code=503, detail="Discord channel is not configured")

    adapter = get_channel_adapter("discord")
    if adapter is None:
        raise HTTPException(status_code=503, detail="Discord adapter missing")

    msg = adapter.normalize_payload(payload)
    if msg is None:
        return {"ok": True, "skipped": True}

    turn = handle_channel_message(msg)
    if turn.ok:
        adapter.send_message(chat_id=msg.external_chat_id, text=turn.reply)
    return {"ok": turn.ok, "session_id": turn.session_id, "intent": turn.intent}


def _verify_meta_webhook(request: Request, expected_token: str) -> Response:
    """Meta webhook GET verification handshake (WhatsApp Cloud / Messenger)."""
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge") or ""
    if mode == "subscribe" and expected_token and token == expected_token:
        return Response(content=challenge, media_type="text/plain")
    raise HTTPException(status_code=403, detail="Webhook verification failed")


@router.get("/channels/whatsapp/webhook")
def get_whatsapp_webhook_verify(request: Request) -> Response:
    from aethos_core.channels.channel_credentials import channel_field
    from aethos_core.config import get_settings

    verify_token = channel_field("whatsapp", "verify_token", str(get_settings().whatsapp_verify_token or ""))
    return _verify_meta_webhook(request, verify_token)


@router.post("/channels/whatsapp/webhook")
async def post_whatsapp_inbound(request: Request) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import channel_runtime_enabled
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not channel_runtime_enabled("whatsapp", get_settings().whatsapp_enabled):
        raise HTTPException(status_code=503, detail="WhatsApp channel is not enabled")
    payload = await _parse_signed_meta_body(request, "whatsapp")
    return route_channel_inbound(channel="whatsapp", payload=payload)


@router.get("/channels/messenger/webhook")
def get_messenger_webhook_verify(request: Request) -> Response:
    from aethos_core.channels.channel_credentials import channel_field
    from aethos_core.config import get_settings

    verify_token = channel_field("messenger", "verify_token", str(get_settings().messenger_verify_token or ""))
    return _verify_meta_webhook(request, verify_token)


@router.post("/channels/messenger/webhook")
async def post_messenger_inbound(request: Request) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import channel_runtime_enabled
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not channel_runtime_enabled("messenger", get_settings().messenger_enabled):
        raise HTTPException(status_code=503, detail="Messenger channel is not enabled")
    payload = await _parse_signed_meta_body(request, "messenger")
    return route_channel_inbound(channel="messenger", payload=payload)


@router.post("/channels/email/inbound")
async def post_email_inbound(request: Request) -> dict[str, Any]:
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not get_settings().email_enabled:
        raise HTTPException(status_code=503, detail="Email channel is not enabled")
    payload = await _parse_json_body(request)
    return route_channel_inbound(channel="email", payload=payload)


@router.post("/channels/teams/inbound")
async def post_teams_inbound(request: Request) -> dict[str, Any]:
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not get_settings().teams_enabled:
        raise HTTPException(status_code=503, detail="Teams channel is not enabled")
    payload = await _parse_json_body(request)
    return route_channel_inbound(channel="teams", payload=payload)


@router.post("/channels/sms/inbound")
async def post_sms_inbound(request: Request) -> dict[str, Any]:
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not get_settings().sms_enabled:
        raise HTTPException(status_code=503, detail="SMS channel is not enabled")
    payload = await _parse_twilio_or_json(request)
    return route_channel_inbound(channel="sms", payload=payload)


@router.post("/channels/voice/inbound")
async def post_voice_inbound(request: Request) -> Response:
    from aethos_core.channels.universal.universal_channel_runtime import route_channel_inbound
    from aethos_core.config import get_settings

    if not get_settings().voice_enabled:
        raise HTTPException(status_code=503, detail="Voice channel is not enabled")
    payload = await _parse_twilio_or_json(request)
    result = route_channel_inbound(channel="voice", payload=payload)
    twiml = str(result.get("twiml") or "")
    if not twiml:
        from aethos_core.channels.universal.universal_channel_runtime import build_twiml_say

        twiml = build_twiml_say(str(result.get("reply") or "Goodbye"))
    return Response(content=twiml, media_type="application/xml")


@router.get("/channels/{channel_id}/connection")
def get_channel_connection(channel_id: str) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import channel_connection_payload

    return channel_connection_payload(channel_id)


@router.post("/channels/{channel_id}/credentials")
async def post_store_channel_credential(channel_id: str, request: Request) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import (
        ChannelCredentialError,
        channel_connection_payload,
        channel_supports_credentials,
        store_channel_credentials,
        test_channel_credential,
    )
    from aethos_core.security.secret_redaction import redact_text

    if not channel_supports_credentials(channel_id):
        raise HTTPException(status_code=404, detail="Channel does not support credential management")
    payload = await _parse_json_body(request)
    label = str(payload.get("label") or "").strip()
    fields = payload.get("fields")
    if not isinstance(fields, dict):
        # Allow flat field payloads too (everything except "label").
        fields = {k: v for k, v in payload.items() if k != "label"}
    try:
        record = store_channel_credentials(
            channel_id=channel_id,
            label=label,
            fields={str(k): str(v) for k, v in fields.items()},
        )
    except ChannelCredentialError as exc:
        raise HTTPException(status_code=422, detail=redact_text(str(exc))) from None
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=redact_text(str(exc))[:240]) from None
    try:
        test_result = test_channel_credential(channel_id, record.credential_id)
    except Exception as exc:  # noqa: BLE001
        test_result = {"ok": False, "detail": redact_text(str(exc))}
    return {
        "ok": True,
        "credential": record.to_public_dict(),
        "test": test_result,
        "connection": channel_connection_payload(channel_id),
    }


@router.post("/channels/{channel_id}/credentials/{credential_id}/test")
def post_test_channel_credential(channel_id: str, credential_id: str) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import test_channel_credential

    try:
        result = test_channel_credential(channel_id, credential_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Credential not found") from None
    return {"ok": True, "test": result}


@router.post("/channels/{channel_id}/credentials/{credential_id}/revoke")
def post_revoke_channel_credential(channel_id: str, credential_id: str) -> dict[str, Any]:
    from aethos_core.channels.channel_credentials import (
        channel_connection_payload,
        revoke_channel_credential,
    )

    if not revoke_channel_credential(channel_id, credential_id):
        raise HTTPException(status_code=404, detail="Credential not found") from None
    return {"ok": True, "revoked": True, "connection": channel_connection_payload(channel_id)}


@router.get("/channels/pairing/status")
def get_pairing_status() -> dict[str, Any]:
    from aethos_core.channels.pairing_store import pairing_status_payload

    return pairing_status_payload()


@router.post("/channels/pairing/approve")
async def post_pairing_approve(request: Request) -> dict[str, Any]:
    from aethos_core.channels.pairing_store import approve_pairing

    payload = await _parse_json_body(request)
    channel = str(payload.get("channel") or "").strip()
    code = str(payload.get("code") or "").strip()
    if not channel or not code:
        raise HTTPException(status_code=400, detail="channel and code required")
    result = approve_pairing(channel, code)
    if not result.get("ok"):
        raise HTTPException(status_code=404, detail=str(result.get("error") or "pairing_failed"))
    return result


@router.post("/channels/pairing/revoke")
async def post_pairing_revoke(request: Request) -> dict[str, Any]:
    from aethos_core.channels.pairing_store import revoke_sender

    payload = await _parse_json_body(request)
    channel = str(payload.get("channel") or "").strip()
    sender = str(payload.get("external_user_id") or payload.get("sender") or "").strip()
    if not channel or not sender:
        raise HTTPException(status_code=400, detail="channel and external_user_id required")
    return revoke_sender(channel, sender)


@router.get("/channels/outbound/status")
def get_outbound_status() -> dict[str, Any]:
    from aethos_core.channels.outbound_governance import outbound_status_payload

    return outbound_status_payload()


@router.post("/channels/outbound/approve")
async def post_outbound_approve(request: Request) -> dict[str, Any]:
    from aethos_core.channels.outbound_governance import approve_outbound_send

    payload = await _parse_json_body(request)
    preflight_id = str(payload.get("preflight_id") or "").strip()
    if not preflight_id:
        raise HTTPException(status_code=400, detail="preflight_id required")
    result = approve_outbound_send(preflight_id)
    if not result.get("ok") and result.get("error") == "preflight_not_found":
        raise HTTPException(status_code=404, detail="preflight_not_found")
    return result


async def _parse_json_body(request: Request) -> dict[str, Any]:
    import json

    body = await request.body()
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Expected JSON object")
    return payload


async def _parse_signed_meta_body(request: Request, channel: str) -> dict[str, Any]:
    """Verify the Meta X-Hub-Signature-256 over the raw body (when an app secret is
    configured), then parse JSON. Skips verification when no app secret is set yet —
    matching the Slack pattern — so initial Meta setup isn't blocked."""
    import json

    from aethos_core.channels.meta_webhook import meta_app_secret, verify_meta_signature

    body = await request.body()
    secret = meta_app_secret(channel)
    if secret:
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_meta_signature(body=body, signature=signature, app_secret=secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None
    return payload if isinstance(payload, dict) else {}


async def _parse_twilio_or_json(request: Request) -> dict[str, Any]:
    import json

    content_type = (request.headers.get("content-type") or "").lower()
    if "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        return {str(k): str(v) for k, v in form.items()}
    body = await request.body()
    if not body:
        return {}
    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    return payload if isinstance(payload, dict) else {}
