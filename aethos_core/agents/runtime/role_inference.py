# SPDX-License-Identifier: Apache-2.0
"""Execution inference — detect operational entity & workspace intents."""

from __future__ import annotations

import re
from typing import Any

_CREATE_AGENTS_RX = re.compile(
    r"\b(?:create|spawn|stand\s+up|initialize)\b.*\b(?:agent|specialist)s?\b|"
    r"\b(?:agent|specialist)s?\b.*\b(?:create|spawn|initialize)\b",
    re.I,
)
_ENTITY_STATUS_RX = re.compile(
    r"\bhave you created\b|\bdid you create\b|\balready created\b|\bcreated them\b|\bcreated yet\b",
    re.I,
)
_WORKSPACE_RESULTS_RX = re.compile(
    r"\bwhere can i see\b.*\b(?:result|work|output|artifact)\b|"
    r"\b(?:show|view|open)\b.*\b(?:result|output|artifact|workspace)\b",
    re.I,
)
def infer_execution_intent(user_text: str) -> dict[str, Any]:
    raw = (user_text or "").strip()
    if not raw:
        return {"execution_prompt": False, "intent": None}

    if _CREATE_AGENTS_RX.search(raw):
        return {"execution_prompt": True, "intent": "agent_creation", "confidence": 0.88}
    if _ENTITY_STATUS_RX.search(raw):
        return {"execution_prompt": True, "intent": "entity_status", "confidence": 0.85}
    if _WORKSPACE_RESULTS_RX.search(raw):
        return {"execution_prompt": True, "intent": "workspace_results", "confidence": 0.82}

    return {"execution_prompt": False, "intent": None, "confidence": 0.0}


def extract_requested_roles(user_text: str) -> list[str]:
    from aethos_core.agents.runtime.role_planning import extract_requested_roles as _plan_roles

    return _plan_roles(user_text)
