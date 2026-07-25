# SPDX-License-Identifier: Apache-2.0
"""Delivery lane operator API — Phase 5 hook into FIX 125A–127 software delivery."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(tags=["delivery"])


class DeliveryProposeIn(BaseModel):
    message: str = Field(min_length=8, max_length=8000)
    session_id: str = Field(default="operator", max_length=64)


@router.get("/delivery/status")
def get_delivery_status() -> dict[str, Any]:
    from aethos_core.software_delivery.issue_plan_service import load_issue_plan_config

    cfg = load_issue_plan_config()
    return {
        "ok": True,
        "lane": "software_delivery",
        "planning_config": cfg,
        "hint": (
            "125A: analyze github issue … → create implementation plan → planning approval phrase. "
            "125B+: create implementation branch + branch approval phrase (session holds plan)."
        ),
    }


@router.post("/delivery/propose")
def post_delivery_propose(body: DeliveryProposeIn) -> dict[str, Any]:
    from aethos_core.software_delivery.software_delivery_router import route_software_delivery

    sid = (body.session_id or "operator").strip()[:64] or "operator"
    routed = route_software_delivery(body.message, session_id=sid)
    if routed is None:
        return {
            "ok": False,
            "error": "not_delivery_intent",
            "hint": (
                "Try: analyze github issue pilotmain/AethOS#1 — or after planning approval: "
                "create implementation branch + branch approval phrase."
            ),
        }
    reply, intent, meta = routed
    return {"ok": True, "reply": reply, "intent": intent, "meta": meta, "session_id": sid}
