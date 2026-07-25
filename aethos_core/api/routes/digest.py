# SPDX-License-Identifier: Apache-2.0
"""Daily Digest API — preview, fetch latest, deliver now."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from aethos_core.digest import build_digest, deliver_digest, latest_digest

router = APIRouter(tags=["digest"])


@router.get("/digest/preview")
def digest_preview() -> dict[str, Any]:
    """Build the digest right now (read-only) without delivering it."""
    return {"ok": True, "digest": build_digest()}


@router.get("/digest/latest")
def digest_latest() -> dict[str, Any]:
    return {"ok": True, "digest": latest_digest()}


@router.post("/digest/deliver")
def digest_deliver() -> dict[str, Any]:
    """Generate + persist + push the digest now (manual trigger)."""
    return deliver_digest()
