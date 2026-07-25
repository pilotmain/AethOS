# SPDX-License-Identifier: Apache-2.0
"""Stripe billing (dependency-free): HMAC webhook verification, event→entitlement mapping, and
checkout gating. No network — verify_webhook/entitlement_from_event are pure; create_checkout
returns 'not_configured' without keys."""

from __future__ import annotations

import hashlib
import hmac
import json
import time

import pytest

from aethos_core.billing import stripe_client as sc
from aethos_core.config import get_settings


@pytest.fixture
def billing_env(monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "true")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def _sign(payload: bytes, secret: str, ts: int | None = None) -> str:
    ts = ts or int(time.time())
    sig = hmac.new(secret.encode(), f"{ts}.".encode() + payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def test_verify_webhook_accepts_valid_signature(billing_env):
    payload = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
    event = sc.verify_webhook(payload, _sign(payload, "whsec_test"))
    assert event is not None and event["type"] == "checkout.session.completed"


def test_verify_webhook_rejects_tampered_and_stale(billing_env):
    payload = json.dumps({"type": "x"}).encode()
    assert sc.verify_webhook(payload, _sign(payload, "wrong_secret")) is None  # bad secret
    assert sc.verify_webhook(b'{"type":"y"}', _sign(payload, "whsec_test")) is None  # tampered body
    assert sc.verify_webhook(payload, _sign(payload, "whsec_test", ts=int(time.time()) - 99999)) is None  # stale


def test_entitlement_mapping():
    checkout = {"type": "checkout.session.completed", "data": {"object": {"customer_email": "u@x.com"}}}
    out = sc.entitlement_from_event(checkout)
    assert out == {"email": "u@x.com", "status": "active", "plan": "paid", "access_expires_at": None}

    deleted = {"type": "customer.subscription.deleted",
               "data": {"object": {"status": "canceled", "metadata": {"customer_email": "u@x.com"}}}}
    assert sc.entitlement_from_event(deleted)["status"] == "expired"

    past_due = {"type": "customer.subscription.updated",
                "data": {"object": {"status": "past_due", "metadata": {"customer_email": "u@x.com"}}}}
    assert sc.entitlement_from_event(past_due)["status"] == "suspended"

    assert sc.entitlement_from_event({"type": "invoice.paid", "data": {"object": {}}}) is None  # ignored


def test_checkout_not_configured_without_keys(monkeypatch):
    monkeypatch.setenv("BILLING_ENABLED", "false")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "")
    get_settings.cache_clear()
    try:
        out = sc.create_checkout_session(customer_email="u@x.com", success_url="s", cancel_url="c")
        assert out == {"ok": False, "error": "billing_not_configured"}
    finally:
        get_settings.cache_clear()
