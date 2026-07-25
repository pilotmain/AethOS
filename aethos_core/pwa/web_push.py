# SPDX-License-Identifier: Apache-2.0
"""Web push delivery — VAPID-signed notifications for proactive events."""

from __future__ import annotations

import json
from typing import Any

from aethos_core.pwa.push_store import list_push_subscriptions, remove_push_subscription


def web_push_enabled() -> bool:
    from aethos_core.config import get_settings

    s = get_settings()
    if not getattr(s, "web_push_enabled", False):
        return False
    return bool(str(getattr(s, "vapid_public_key", "") or "").strip() and str(getattr(s, "vapid_private_key", "") or "").strip())


def get_vapid_public_key() -> str:
    from aethos_core.config import get_settings

    return str(getattr(get_settings(), "vapid_public_key", "") or "").strip()


def pwa_status() -> dict[str, Any]:
    from aethos_core.config import get_settings

    s = get_settings()
    push_on = web_push_enabled()
    return {
        "ok": True,
        "pwa_installable": True,
        "offline_shell": True,
        "web_push_enabled": push_on,
        "vapid_public_key": get_vapid_public_key() if push_on else "",
        "push_configured": push_on,
    }


def _vapid_claims() -> dict[str, str]:
    from aethos_core.config import get_settings

    subject = str(getattr(get_settings(), "vapid_subject", "") or "mailto:ops@aethos.local").strip()
    return {"sub": subject}


def send_web_push(
    subscription: dict[str, Any],
    *,
    title: str,
    body: str,
    url: str = "/",
    tag: str | None = None,
) -> dict[str, Any]:
    if not web_push_enabled():
        return {"ok": False, "reason": "web_push_disabled"}
    endpoint = str(subscription.get("endpoint") or "")
    keys = subscription.get("keys") or {}
    if not endpoint or not keys:
        return {"ok": False, "reason": "invalid_subscription"}

    payload = json.dumps({"title": title, "body": body, "url": url, "tag": tag or "aethos"})
    from aethos_core.config import get_settings

    s = get_settings()
    private_key = str(getattr(s, "vapid_private_key", "") or "").strip().replace("\\n", "\n")
    try:
        from pywebpush import WebPushException, webpush

        webpush(
            subscription_info={"endpoint": endpoint, "keys": keys},
            data=payload,
            vapid_private_key=private_key,
            vapid_claims=_vapid_claims(),
            timeout=10,
        )
        return {"ok": True, "endpoint": endpoint[:80]}
    except WebPushException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            return {"ok": False, "reason": "subscription_expired", "status": status}
        return {"ok": False, "reason": "push_failed", "detail": str(exc)[:200]}
    except Exception as exc:
        return {"ok": False, "reason": "push_unavailable", "detail": str(exc)[:200]}


def notify_tenant_web_push(
    *,
    title: str,
    body: str,
    url: str = "/",
    tenant_id: str | None = None,
) -> dict[str, Any]:
    """Send a push to all subscriptions for the tenant (best-effort)."""
    if not web_push_enabled():
        return {"ok": False, "skipped": True, "reason": "web_push_disabled"}
    subs = list_push_subscriptions(tenant_id=tenant_id, limit=50)
    if not subs:
        return {"ok": True, "sent": 0, "skipped": True, "reason": "no_subscriptions"}
    sent = 0
    removed = 0
    errors: list[str] = []
    for row in subs:
        result = send_web_push(
            {"endpoint": row.get("endpoint"), "keys": row.get("keys")},
            title=title,
            body=body,
            url=url,
        )
        if result.get("ok"):
            sent += 1
        elif result.get("reason") == "subscription_expired":
            endpoint = str(row.get("endpoint") or "")
            if endpoint and remove_push_subscription(endpoint, tenant_id=tenant_id):
                removed += 1
        else:
            errors.append(str(result.get("reason") or "error"))
    return {"ok": sent > 0, "sent": sent, "removed": removed, "errors": errors[:5]}
