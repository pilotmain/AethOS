# SPDX-License-Identifier: Apache-2.0
"""Skill optimization API — list skills with trace counts, record traces, propose edits."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from aethos_core.skills import (
    propose_skill_optimization,
    record_skill_trace,
    skills_with_trace_counts,
)

router = APIRouter(tags=["skill-optimization"])


class TraceIn(BaseModel):
    outcome: str
    detail: str = ""


@router.get("/skill-optimization/skills")
def list_skills_api() -> dict[str, Any]:
    return {"ok": True, "skills": skills_with_trace_counts()}


@router.post("/skill-optimization/skills/{skill_id}/trace")
def record_trace_api(skill_id: str, req: TraceIn) -> dict[str, Any]:
    return record_skill_trace(skill_id, outcome=req.outcome, detail=req.detail)


@router.post("/skill-optimization/skills/{skill_id}/optimize")
def optimize_api(skill_id: str) -> dict[str, Any]:
    return propose_skill_optimization(skill_id)
