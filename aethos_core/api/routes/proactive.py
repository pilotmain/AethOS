# SPDX-License-Identifier: Apache-2.0
"""Proactive suggestions API — list, scan, dismiss. Read-only proposals; never executes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from aethos_core.proactive import dismiss_suggestion, latest_suggestions, run_proactive_scan

router = APIRouter(tags=["proactive"])


@router.get("/proactive/suggestions")
def list_suggestions_api() -> dict[str, Any]:
    return {"ok": True, "suggestions": latest_suggestions()}


@router.post("/proactive/scan")
def scan_api() -> dict[str, Any]:
    return run_proactive_scan()


@router.post("/proactive/suggestions/{suggestion_id}/dismiss")
def dismiss_api(suggestion_id: str) -> dict[str, Any]:
    return dismiss_suggestion(suggestion_id)
