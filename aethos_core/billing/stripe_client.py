# SPDX-License-Identifier: Apache-2.0
"""Stripe billing — no SDK dependency.

Checkout sessions are created via Stripe's REST API (httpx); webhooks are verified with
Stripe's documented HMAC-SHA256 scheme by hand. Everything is gated on STRIPE_SECRET_KEY /
STRIPE_WEBHOOK_SECRET — absent keys mean billing is simply not configured (never a crash).
Secrets are never logged.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import time
from typing import Any
from urllib.parse import urlencode

_log = logging.getLogger("aethos.billing.stripe")

_STRIPE_API = "https://api.stripe.com/v1"
# Reject webhook timestamps older than this (replay protection), per Stripe guidance.
_WEBHOOK_TOLERANCE_SEC = 300

# Stripe subscription.status → AethOS entitlement status.
_STATUS_MAP = {
    "active": "active",
    "trialing": "trial",
    "past_due": "suspended",
    "unpaid": "suspended",
    "incomplete": "suspended",
    "incomplete_expired": "expired",
    "canceled": "expired",
}


def billing_configured() -> bool:
    from aethos_core.config import get_settings

    s = get_settings()
    return bool(s.billing_enabled and str(getattr(s, "stripe_secret_key", "") or "").strip())


def create_checkout_session(*, customer_email: str, success_url: str, cancel_url: str) -> dict[str, Any]:
    """Create a Stripe Checkout subscription session. Returns {ok, url} or {ok: False, error}."""
    import httpx

    from aethos_core.config import get_settings

    s = get_settings()
    secret = str(getattr(s, "stripe_secret_key", "") or "").strip()
    price = str(getattr(s, "stripe_price_id", "") or "").strip()
    if not (s.billing_enabled and secret):
        return {"ok": False, "error": "billing_not_configured"}
    if not price:
        return {"ok": False, "error": "stripe_price_not_set"}

    form = {
        "mode": "subscription",
        "success_url": success_url,
        "cancel_url": cancel_url,
        "line_items[0][price]": price,
        "line_items[0][quantity]": "1",
        "client_reference_id": customer_email,
    }
    if customer_email:
        form["customer_email"] = customer_email
    trial_days = int(getattr(s, "stripe_trial_days", 0) or 0)
    if trial_days > 0:
        form["subscription_data[trial_period_days]"] = str(trial_days)

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(
                f"{_STRIPE_API}/checkout/sessions",
                content=urlencode(form),
                headers={
                    "Authorization": f"Bearer {secret}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
    except httpx.HTTPError as exc:
        _log.warning("stripe checkout request failed: %s", exc.__class__.__name__)
        return {"ok": False, "error": "stripe_unreachable"}
    if resp.status_code >= 400:
        return {"ok": False, "error": "stripe_error", "status_code": resp.status_code}
    data = resp.json()
    url = str(data.get("url") or "")
    if not url:
        return {"ok": False, "error": "stripe_no_url"}
    return {"ok": True, "url": url, "session_id": data.get("id")}


def verify_webhook(payload: bytes, signature_header: str) -> dict[str, Any] | None:
    """Verify a Stripe webhook signature and return the parsed event, or None if invalid.

    Implements Stripe's scheme: signed_payload = '<t>.<raw_body>', expected = HMAC-SHA256(secret).
    """
    import json

    from aethos_core.config import get_settings

    secret = str(getattr(get_settings(), "stripe_webhook_secret", "") or "").strip()
    if not secret or not signature_header:
        return None
    parts = {}
    for item in signature_header.split(","):
        k, _, v = item.partition("=")
        parts.setdefault(k.strip(), v.strip())
    ts = parts.get("t")
    sig = parts.get("v1")
    if not ts or not sig:
        return None
    try:
        if abs(time.time() - int(ts)) > _WEBHOOK_TOLERANCE_SEC:
            return None
    except ValueError:
        return None
    signed = f"{ts}.".encode() + payload
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    try:
        return json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def entitlement_from_event(event: dict[str, Any]) -> dict[str, Any] | None:
    """Map a Stripe event to an entitlement update: {email, status, plan, access_expires_at}.

    Handles checkout.session.completed and customer.subscription.{updated,deleted}.
    Returns None for events we don't act on.
    """
    etype = str(event.get("type") or "")
    obj = (event.get("data") or {}).get("object") or {}

    if etype == "checkout.session.completed":
        email = str(obj.get("customer_email") or obj.get("client_reference_id") or "").strip().lower()
        if not email:
            return None
        return {"email": email, "status": "active", "plan": "paid", "access_expires_at": None}

    if etype in ("customer.subscription.updated", "customer.subscription.deleted"):
        status = _STATUS_MAP.get(str(obj.get("status") or "").lower(), "suspended")
        if etype == "customer.subscription.deleted":
            status = "expired"
        period_end = obj.get("current_period_end")
        # Stripe sends customer email in the event only when expanded; fall back to metadata.
        email = str(
            (obj.get("metadata") or {}).get("customer_email")
            or obj.get("customer_email")
            or ""
        ).strip().lower()
        if not email:
            return None
        return {
            "email": email,
            "status": status,
            "plan": "paid" if status in ("active", "trial") else "beta",
            "access_expires_at": float(period_end) if period_end else None,
        }

    return None
