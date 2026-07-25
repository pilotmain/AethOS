# SPDX-License-Identifier: Apache-2.0
"""FIX 316D — topic detection from user text."""

from __future__ import annotations

import re
from typing import Any

from aethos_core.conversation.continuity_pkg.conversation_continuity_contract import (
    ECOSYSTEM_TOPICS,
    HUMAN_SUPPORT_TOPICS,
    IDENTITY_TOPICS,
    OPERATIONAL_TOPICS,
)
from aethos_core.runtime_truth_alignment.governance_footer_policy import operational_action_detected

_FOLLOW_UP_RX = re.compile(
    r"^\s*(?:what else|tell me more|what other advice(?:\s+do you have)?|continue|go on|anything else|and then)(?:\s+do you have)?\s*[.?!]?\s*$",
    re.I,
)
_TOPIC_SHIFT_RX = re.compile(
    r"\b(?:what|how)\s+about\s+(?P<subject>.+?)\s*[.?!]?\s*$",
    re.I,
)
_HUMAN_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("depression", re.compile(r"\b(?:depressed|depression)\b", re.I)),
    ("anxiety", re.compile(r"\b(?:anxious|anxiety)\b", re.I)),
    ("stress", re.compile(r"\b(?:stressed|stress|overwhelmed)\b", re.I)),
    ("loneliness", re.compile(r"\b(?:lonely|loneliness)\b", re.I)),
    ("burnout", re.compile(r"\bburn(?:out|ed|ing)\b", re.I)),
)
_OPERATIONAL_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("deployment", re.compile(r"\b(?:deploy(?:ment)?|redeploy)\b", re.I)),
    ("rollback", re.compile(r"\brollback\b", re.I)),
    ("provider", re.compile(r"\b(?:provider|railway|vercel|github)\b", re.I)),
    ("workflow", re.compile(r"\bworkflow\b", re.I)),
)
_ECOSYSTEM_TOPIC_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("pilotos", re.compile(r"\bpilotos\b", re.I)),
    ("atlas", re.compile(r"\batlas(?:\s+trader)?\b", re.I)),
    ("nexora", re.compile(r"\bnexora\b", re.I)),
)
_MODEL_CREATOR_RX = re.compile(
    r"\b(?:what|how)\s+about\s+(?:claude|gpt|chatgpt)\b|\bwho\s+(?:created|made|built)\s+(?:claude|gpt|chatgpt)\b",
    re.I,
)
_IDENTITY_RX = re.compile(
    r"\b(?:who\s+are\s+you|who\s+created|who\s+built|who\s+owns|what\s+is\s+aethos)\b",
    re.I,
)
_CAPABILITY_RX = re.compile(r"\bwhat\s+can\s+(?:you|aethos)\s+do\b", re.I)
_CAREER_RX = re.compile(r"\bcareer\b", re.I)
_ARCHITECTURE_RX = re.compile(r"\b(?:software\s+architecture|system\s+design|architecture)\b", re.I)


def is_follow_up_prompt(text: str) -> bool:
    return bool(_FOLLOW_UP_RX.match((text or "").strip()))


def detect_topic_shift(text: str) -> dict[str, Any] | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if _MODEL_CREATOR_RX.search(raw):
        model = "claude" if "claude" in raw.lower() else "gpt"
        return {
            "shifted": True,
            "topic": "model_creator",
            "parent_topic": "identity",
            "mode": "identity",
            "classification_hint": f"model_creator_attribution_response:{model}",
        }

    shift_match = _TOPIC_SHIFT_RX.search(raw)
    if shift_match:
        subject = (shift_match.group("subject") or "").strip().lower()
        if subject in {"claude", "gpt", "chatgpt"}:
            model = "claude" if "claude" in subject else "gpt"
            return {
                "shifted": True,
                "topic": "model_creator",
                "parent_topic": "identity",
                "mode": "identity",
                "classification_hint": f"model_creator_attribution_response:{model}",
            }
        if "aethos" in subject:
            return {
                "shifted": True,
                "topic": "platform_identity",
                "parent_topic": "identity",
                "mode": "identity",
                "classification_hint": "platform_identity_response",
            }

    return None


def detect_topic_from_text(text: str, *, classification: str | None = None) -> dict[str, Any]:
    raw = (text or "").strip()
    lowered = raw.lower()

    shift = detect_topic_shift(raw)
    if shift:
        return {**shift, "confidence": 0.95}

    for topic, pattern in _HUMAN_TOPIC_PATTERNS:
        if pattern.search(raw):
            return {
                "topic": topic,
                "parent_topic": "human_support",
                "mode": "human_support",
                "confidence": 0.92,
                "classification_hint": "human_support_response",
            }

    if operational_action_detected(text=raw):
        for topic, pattern in _OPERATIONAL_TOPIC_PATTERNS:
            if pattern.search(raw):
                return {
                    "topic": topic,
                    "parent_topic": "operational",
                    "mode": "operational",
                    "confidence": 0.9,
                    "classification_hint": "operational_action",
                }
        return {
            "topic": "operational",
            "parent_topic": "operational",
            "mode": "operational",
            "confidence": 0.85,
            "classification_hint": "operational_action",
        }

    for topic, pattern in _OPERATIONAL_TOPIC_PATTERNS:
        if pattern.search(raw):
            return {
                "topic": topic,
                "parent_topic": "operational",
                "mode": "operational",
                "confidence": 0.88,
                "classification_hint": classification or "operational_action",
            }

    if _IDENTITY_RX.search(raw) or (classification or "").startswith(("platform_identity", "creator", "ownership")):
        topic = "creator_attribution"
        if "who are you" in lowered or "what is aethos" in lowered:
            topic = "platform_identity"
        elif "own" in lowered:
            topic = "ownership"
        return {
            "topic": topic,
            "parent_topic": "identity",
            "mode": "identity",
            "confidence": 0.9,
            "classification_hint": classification,
        }

    if (classification or "").startswith("model_creator"):
        return {
            "topic": "model_creator",
            "parent_topic": "identity",
            "mode": "identity",
            "confidence": 0.9,
            "classification_hint": classification,
        }

    if _CAPABILITY_RX.search(raw) or classification == "capability_response":
        return {
            "topic": "capabilities",
            "parent_topic": "capability",
            "mode": "capability",
            "confidence": 0.88,
            "classification_hint": "capability_response",
        }

    for topic, pattern in _ECOSYSTEM_TOPIC_PATTERNS:
        if pattern.search(raw):
            return {
                "topic": topic,
                "parent_topic": "ecosystem",
                "mode": "ecosystem",
                "confidence": 0.86,
                "classification_hint": classification,
            }

    if _CAREER_RX.search(raw):
        return {
            "topic": "career",
            "parent_topic": "general",
            "mode": "general",
            "confidence": 0.8,
            "classification_hint": classification,
        }

    if _ARCHITECTURE_RX.search(raw):
        return {
            "topic": "software_architecture",
            "parent_topic": "general",
            "mode": "general",
            "confidence": 0.8,
            "classification_hint": classification,
        }

    if classification == "human_support_response":
        return {
            "topic": "human_support",
            "parent_topic": "human_support",
            "mode": "human_support",
            "confidence": 0.85,
            "classification_hint": classification,
        }

    return {
        "topic": classification or "general",
        "parent_topic": "general",
        "mode": "general",
        "confidence": 0.5,
        "classification_hint": classification,
    }


def topic_in_human_support(topic: str | None) -> bool:
    return (topic or "") in HUMAN_SUPPORT_TOPICS or topic == "human_support"


def topic_in_operational(topic: str | None) -> bool:
    return (topic or "") in OPERATIONAL_TOPICS or topic == "operational"


def topic_in_identity(topic: str | None) -> bool:
    return (topic or "") in IDENTITY_TOPICS


def topic_in_ecosystem(topic: str | None) -> bool:
    return (topic or "") in ECOSYSTEM_TOPICS
