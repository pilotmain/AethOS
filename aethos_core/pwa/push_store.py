# SPDX-License-Identifier: Apache-2.0
"""Tenant-scoped web push subscription store."""

from __future__ import annotations

import hashlib
import json
from time import time
from typing import Any

from aethos_core.tenancy.tenant_data_store import delete_record, get_record_by_namespace_key, list_records, set_record

NS_PUSH = "web_push_subscriptions"


def _subscription_key(endpoint: str) -> str:
    digest = hashlib.sha256(endpoint.encode("utf-8")).hexdigest()[:24]
    return f"push-{digest}"


def save_push_subscription(subscription: dict[str, Any], *, tenant_id: str | None = None) -> dict[str, Any]:
    endpoint = str(subscription.get("endpoint") or "").strip()
    if not endpoint:
        return {"ok": False, "reason": "missing_endpoint"}
    key = _subscription_key(endpoint)
    row = {
        "subscription_id": key,
        "endpoint": endpoint,
        "keys": dict(subscription.get("keys") or {}),
        "expiration_time": subscription.get("expirationTime"),
        "user_agent": str(subscription.get("user_agent") or "")[:240],
        "updated_at": time(),
    }
    set_record(NS_PUSH, key, row, tenant_id=tenant_id)
    return {"ok": True, "subscription_id": key}


def remove_push_subscription(endpoint: str, *, tenant_id: str | None = None) -> bool:
    key = _subscription_key(endpoint)
    return delete_record(NS_PUSH, key, tenant_id=tenant_id)


def list_push_subscriptions(*, tenant_id: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    return list_records(NS_PUSH, tenant_id=tenant_id, limit=limit)


def get_push_subscription(subscription_id: str, *, tenant_id: str | None = None) -> dict[str, Any] | None:
    return get_record_by_namespace_key(NS_PUSH, subscription_id, tenant_id=tenant_id)


def clear_push_subscriptions_for_tests() -> None:
    from aethos_core.tenancy.tenant_data_store import reset_for_tests

    reset_for_tests()
