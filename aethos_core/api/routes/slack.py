# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from aethos_core.channels.slack.slack_runtime import slack_configured, verify_slack_signature

_log = logging.getLogger(__name__)
router = APIRouter(tags=["slack"])


@router.post("/channels/slack/events")
async def post_slack_events(request: Request) -> dict[str, Any]:
    from aethos_core.channels.slack.slack_router import handle_slack_event

    body = await request.body()
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if slack_configured() and not verify_slack_signature(body=body, timestamp=timestamp, signature=signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    import json

    try:
        payload = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from None

    if payload.get("type") != "url_verification" and not slack_configured():
        raise HTTPException(status_code=503, detail="Slack channel is not configured")

    try:
        return handle_slack_event(payload if isinstance(payload, dict) else {})
    except Exception as exc:
        _log.exception("slack_event_handler_failed")
        return {"ok": False, "detail": str(exc)[:240]}


@router.get("/channels/slack/status")
def get_slack_status() -> dict[str, Any]:
    from aethos_core.channels.slack.slack_runtime import slack_channel_status

    return slack_channel_status()
