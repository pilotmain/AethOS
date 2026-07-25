# SPDX-License-Identifier: Apache-2.0
"""Webhook security — production trust infrastructure (Phase 11.8.2)."""

from __future__ import annotations

import hashlib
import hmac
import json
from time import time
from typing import Any

from aethos_core.external_execution_truth.execution_store import get_execution_meta, upsert_execution_meta


def _secret() -> str:
    from aethos_core.config import get_settings

    return str(getattr(get_settings(), "trigger_webhook_secret", "") or "")


def sign_webhook_payload(payload: dict[str, Any]) -> str:
    secret = _secret()
    if not secret:
        return ""
    body_payload = {k: v for k, v in payload.items() if k != "signature"}
    body = json.dumps(body_payload, sort_keys=True, separators=(",", ":")).encode()
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify_webhook_signature(*, payload: dict[str, Any], signature: str | None) -> dict[str, Any]:
    secret = _secret()
    if not secret:
        return {"ok": True, "verified": False, "reason": "secret_not_configured", "dev_mode": True}
    if not signature:
        return {"ok": False, "verified": False, "reason": "missing_signature"}
    expected = sign_webhook_payload(payload)
    if not hmac.compare_digest(expected, signature):
        return {"ok": False, "verified": False, "reason": "invalid_signature"}
    return {"ok": True, "verified": True}


def validate_webhook_delivery(
    *,
    job_id: str,
    payload: dict[str, Any],
    signature: str | None = None,
    delivery_id: str | None = None,
    sequence: int | None = None,
) -> dict[str, Any]:
    auth = verify_webhook_signature(payload=payload, signature=signature)
    if not auth.get("ok") and not auth.get("dev_mode"):
        return auth

    meta = get_execution_meta(job_id) or {}
    processed = list(meta.get("processed_delivery_ids") or [])
    if delivery_id and delivery_id in processed:
        return {"ok": True, "duplicate": True, "reason": "idempotent_replay"}

    last_seq = int(meta.get("last_callback_sequence") or 0)
    if sequence is not None and sequence <= last_seq:
        return {"ok": False, "reason": "stale_callback_sequence", "last_sequence": last_seq}

    upsert_execution_meta(
        job_id,
        last_callback_sequence=sequence if sequence is not None else last_seq + 1,
        processed_delivery_ids=([delivery_id] + processed)[:50] if delivery_id else processed,
        last_webhook_at=time(),
    )
    return {"ok": True, "duplicate": False, "auth": auth}
