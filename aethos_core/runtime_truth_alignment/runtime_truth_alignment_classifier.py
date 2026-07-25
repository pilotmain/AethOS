# SPDX-License-Identifier: Apache-2.0
"""FIX 316A — runtime prompt classification."""

from __future__ import annotations

import re

from aethos_core.runtime.runtime_config_intent import is_runtime_provider_config_question
from aethos_core.runtime_truth_alignment.governance_footer_policy import operational_action_detected

_MODEL_CREATOR_RX = re.compile(
    r"\bwho\s+(?:created|made|built)\s+(?P<model>claude|gpt|chatgpt)\b",
    re.I,
)
_PROVIDER_RX = re.compile(
    r"\b("
    r"which\s+model\s+(?:are\s+you(?:\s+using)?|do\s+you\s+use|powers\s+you)"
    r"|what\s+model\s+(?:are\s+you(?:\s+using)?|do\s+you\s+use)"
    r"|which\s+provider\s+(?:powers(?:\s+this\s+session)?|are\s+you(?:\s+using)?|do\s+you\s+use)"
    r"|what\s+provider\s+(?:powers(?:\s+this\s+session)?|are\s+you(?:\s+using)?)"
    r")\b",
    re.I,
)
_OWNERSHIP_RX = re.compile(
    r"\bwho\s+owns\s+(?:aethos|you|this\s+platform)\b",
    re.I,
)
_CREATOR_RX = re.compile(
    r"\b(?:who|whom)\s+(?:created|built|made|developed)\s+(?:you|aethos)\b"
    r"|\bwho\s+built\s+aethos\b"
    r"|\bwho\s+created\s+aethos\b",
    re.I,
)
_IDENTITY_RX = re.compile(
    r"\b("
    r"who\s+are\s+you"
    r"|what\s+are\s+you"
    r"|tell\s+me\s+about\s+(?:yourself|aethos)"
    r"|what\s+is\s+aethos"
    r"|what\s+makes\s+(?:you|aethos)\s+different"
    r"|why\s+aethos"
    r")\b",
    re.I,
)
_CAPABILITY_RX = re.compile(
    r"\b("
    r"what\s+can\s+(?:you|aethos)\s+do"
    r"|what\s+(?:are\s+you|can\s+you)\s+capable"
    r"|what\s+are\s+your\s+capabilities"
    r"|what\s+is\s+(?:implemented|operational|trusted|experimental|planned)"
    r"|what\s+can(?:\s+you)?\s+not\s+do"
    r")\b",
    re.I,
)
_PROVIDER_SUPPORT_RX = re.compile(
    r"\b(?:which|what)\s+providers?\s+do\s+you\s+support\b",
    re.I,
)
_READINESS_RX = re.compile(
    r"\b(?:are\s+you\s+launch\s+ready|ready\s+for\s+(?:public\s+)?launch|launch\s+ready)\b",
    re.I,
)
_HUMAN_SUPPORT_RX = re.compile(
    r"\b("
    r"i(?:'m|\s+am)\s+(?:depressed|anxious|stressed|lonely|hopeless|overwhelmed|burned\s+out|burnt\s+out)"
    r"|i\s+feel\s+(?:depressed|anxious|stressed|lonely|hopeless|overwhelmed|empty|burned\s+out|burnt\s+out)"
    r"|feeling\s+(?:depressed|anxious|stressed|lonely|hopeless|burned\s+out|burnt\s+out)"
    r")\b",
    re.I,
)
_GENERAL_RX = re.compile(
    r"^\s*("
    r"tell\s+me\s+a\s+joke"
    r"|explain\s+"
    r"|what\s+is\s+(?:java|kubernetes|python|react)"
    r")\b",
    re.I,
)
_MC_ENGINEERING_RX = re.compile(
    r"^\s*show\s+(?:autonomous\s+)?capability",
    re.I,
)


def classify_runtime_prompt(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None

    if operational_action_detected(text=raw):
        return "operational_action"

    if _MC_ENGINEERING_RX.match(raw):
        return None

    if _HUMAN_SUPPORT_RX.search(raw):
        return "human_support_response"

    if is_runtime_provider_config_question(raw):
        return "provider_attribution_response"

    model_creator_match = _MODEL_CREATOR_RX.search(raw)
    if model_creator_match:
        return f"model_creator_attribution_response:{model_creator_match.group('model').lower()}"

    if _PROVIDER_RX.search(raw):
        return "provider_attribution_response"

    if _OWNERSHIP_RX.search(raw):
        return "ownership_attribution_response"

    if _CREATOR_RX.search(raw):
        return "creator_attribution_response"

    if _READINESS_RX.search(raw):
        return "launch_readiness_response"

    if _PROVIDER_SUPPORT_RX.search(raw):
        return "provider_support_response"

    if _CAPABILITY_RX.search(raw):
        return "capability_response"

    if _IDENTITY_RX.search(raw):
        return "platform_identity_response"

    if _GENERAL_RX.search(raw):
        return "general_assistant_response"

    return None
