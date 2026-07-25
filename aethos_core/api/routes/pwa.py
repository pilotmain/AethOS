# SPDX-License-Identifier: Apache-2.0
"""PWA + web push API."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["pwa"])


class PushSubscribeIn(BaseModel):
    endpoint: str = Field(min_length=8, max_length=2048)
    keys: dict[str, str] = Field(min_length=1)
    expiration_time: int | None = None
    user_agent: str | None = None


class PushUnsubscribeIn(BaseModel):
    endpoint: str = Field(min_length=8, max_length=2048)


class PushTestIn(BaseModel):
    title: str = Field(default="AethOS", max_length=120)
    body: str = Field(default="Test notification", max_length=500)
    url: str = Field(default="/", max_length=500)


@router.get("/pwa/status")
def pwa_status_api() -> dict[str, Any]:
    from aethos_core.pwa.push_store import list_push_subscriptions
    from aethos_core.pwa.web_push import pwa_status

    status = pwa_status()
    status["subscriptions"] = len(list_push_subscriptions())
    return status


@router.get("/pwa/vapid-public-key")
def pwa_vapid_public_key_api() -> dict[str, str]:
    from aethos_core.pwa.web_push import get_vapid_public_key, web_push_enabled

    if not web_push_enabled():
        raise HTTPException(status_code=503, detail="web_push_disabled")
    return {"ok": "true", "public_key": get_vapid_public_key()}


@router.post("/pwa/push/subscribe")
def pwa_push_subscribe_api(body: PushSubscribeIn) -> dict[str, Any]:
    from aethos_core.pwa.web_push import web_push_enabled
    from aethos_core.pwa.push_store import save_push_subscription

    if not web_push_enabled():
        raise HTTPException(status_code=503, detail="web_push_disabled")
    result = save_push_subscription(
        {
            "endpoint": body.endpoint,
            "keys": body.keys,
            "expirationTime": body.expiration_time,
            "user_agent": body.user_agent,
        }
    )
    if not result.get("ok"):
        raise HTTPException(status_code=422, detail=result.get("reason", "subscribe_failed"))
    return result


@router.post("/pwa/push/unsubscribe")
def pwa_push_unsubscribe_api(body: PushUnsubscribeIn) -> dict[str, Any]:
    from aethos_core.pwa.push_store import remove_push_subscription

    removed = remove_push_subscription(body.endpoint)
    return {"ok": True, "removed": removed}


@router.post("/pwa/push/test")
def pwa_push_test_api(body: PushTestIn) -> dict[str, Any]:
    from aethos_core.pwa.web_push import notify_tenant_web_push, web_push_enabled

    if not web_push_enabled():
        raise HTTPException(status_code=503, detail="web_push_disabled")
    return notify_tenant_web_push(title=body.title, body=body.body, url=body.url)
