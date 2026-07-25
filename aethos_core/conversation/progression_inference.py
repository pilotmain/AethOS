# SPDX-License-Identifier: Apache-2.0
"""Progression inference — detect agent conclusion and progress intents."""

from __future__ import annotations

import re
from typing import Any

_AGENT_CONCLUSION_RX = re.compile(
    r"\bwhat did the\b.*\b(?:conclude|find|determine|recommend|say)\b|"
    r"\bwhat has the\b.*\b(?:conclude|found|determined|recommended)\b|"
    r"\b(?:strategist|researcher).*\b(?:conclude|conclusion|findings|recommend|assessment)\b|"
    r"\bstrategist'?s?\s+(?:conclusion|findings|assessment|recommendation)\b",
    re.I,
)
_COMPLETION_WATCH_RX = re.compile(
    r"\blet me know\b.*\b(?:done|complete|finished|ready)\b|"
    r"\bnotify\b.*\b(?:done|complete|finished|ready)\b|"
    r"\bonce they(?:'re| are) done\b|"
    r"\bwhen they(?:'re| are) (?:done|finished|complete)\b|"
    r"\btell me when\b.*\b(?:done|complete|finished|ready)\b",
    re.I,
)
_PROGRESS_INQUIRY_RX = re.compile(
    r"\b(?:any|got)\s+updates?\b|\bhow(?:'s| is) the\b.*\b(?:research|analysis|work)\b|"
    r"\bare they done\b|\bstill (?:working|running|analyzing)\b|"
    r"\bprogress on\b|\bstatus of the\b.*\b(?:agent|research|analysis|workspace)\b",
    re.I,
)
_OPERATIONAL_CONTINUITY_RX = re.compile(
    r"\b(?:agent|researcher|strategist|research|workspace|analysis|job)\b|"
    r"\b(?:done|complete|finished|progress|update|conclude|waiting|monitor|running|failed)\b|"
    r"\blet me know\b|\bwaiting for\b",
    re.I,
)
_JOB_STATUS_RX = re.compile(
    r"\bwhat jobs are running\b|\bshow active agent jobs\b|\bactive jobs\b|"
    r"\bdid any job fail\b|\bany job fail\b|\bjob status\b",
    re.I,
)
_TARGET_AGENT_RX = re.compile(
    r"\b(product\s+strategist|market\s+researcher|strategist|researcher)\b",
    re.I,
)


def infer_progression_intent(user_text: str) -> dict[str, Any]:
    raw = (user_text or "").strip()
    if _AGENT_CONCLUSION_RX.search(raw):
        target = extract_target_agent(raw)
        return {"progression_prompt": True, "intent": "agent_conclusion", "target_agent": target}
    if _COMPLETION_WATCH_RX.search(raw):
        return {"progression_prompt": True, "intent": "completion_watch", "target_agent": extract_target_agent(raw)}
    if _PROGRESS_INQUIRY_RX.search(raw):
        return {"progression_prompt": True, "intent": "progress_inquiry", "target_agent": extract_target_agent(raw)}
    if _JOB_STATUS_RX.search(raw):
        return {"progression_prompt": True, "intent": "job_status", "target_agent": None}
    return {"progression_prompt": False, "intent": None, "target_agent": None}


def infer_operational_continuity_intercept(user_text: str) -> dict[str, Any]:
    raw = (user_text or "").strip()
    if not raw:
        return {"intercept": False}
    if infer_progression_intent(raw).get("progression_prompt"):
        return {"intercept": True, "reason": "progression_intent"}
    if _OPERATIONAL_CONTINUITY_RX.search(raw):
        return {"intercept": True, "reason": "operational_continuity"}
    return {"intercept": False}


def extract_target_agent(user_text: str) -> str | None:
    match = _TARGET_AGENT_RX.search(user_text or "")
    if not match:
        return None
    label = match.group(1).strip().title()
    if label in ("Strategist", "Researcher"):
        return f"Product {label}" if label == "Strategist" else f"Market {label}"
    return label
