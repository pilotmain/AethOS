# SPDX-License-Identifier: Apache-2.0
"""Runtime provider/model question detection (broad phrasing)."""

from __future__ import annotations

import re

# Do not hijack research/eval or unrelated "model" uses.
_EXCLUDE_RX = re.compile(
    r"\b("
    r"blind\s+model\s+eval"
    r"|model\s+eval(?:uation)?"
    r"|data\s+model"
    r"|domain\s+model"
    r"|business\s+model"
    r"|mental\s+model"
    r")\b",
    re.I,
)

_PROVIDER_NAME_RX = re.compile(r"\b(anthropic|openai|claude|gpt|chatgpt|llm)\b", re.I)
_MODEL_OR_LLM_RX = re.compile(r"\b(models?|llms?)\b", re.I)
_CONFIG_SURFACE_RX = re.compile(
    r"\b(runtime\s+config|environment\s+variable|\.env\b|use_real_llm|anthropic_model)\b",
    re.I,
)
_CONFIG_VERB_RX = re.compile(
    r"\b("
    r"using|use|used|configured|configuration|config|active|running|set\s+to|powered|powers"
    r"|are\s+we|we\s+on|tell\s+me|show\s+me|check|know|what'?s|which|what"
    r")\b",
    re.I,
)


def is_runtime_provider_config_question(text: str) -> bool:
    """True when the user asks which LLM/provider/config powers the runtime (any phrasing)."""
    raw = (text or "").strip()
    if not raw or len(raw) > 800:
        return False
    if _EXCLUDE_RX.search(raw):
        return False

    if _CONFIG_SURFACE_RX.search(raw):
        return True

    if re.search(r"\b(which|what)\b.*\b(providers?|api|backend)\b", raw, re.I) and _CONFIG_VERB_RX.search(raw):
        return True

    if not _MODEL_OR_LLM_RX.search(raw) and not (
        _PROVIDER_NAME_RX.search(raw) and _CONFIG_VERB_RX.search(raw)
    ):
        return False

    # Broad-phrasing rule: "model" in the message → models/status intent,
    # unless clearly about creating or naming an agent/model artifact.
    if re.search(r"\b(create|spawn|set\s+default|configure)\b.*\bmodel\b", raw, re.I):
        return False
    if re.search(r"\bmodel\b.*\b(for|named|called)\b", raw, re.I) and not _CONFIG_VERB_RX.search(raw):
        return False

    if _MODEL_OR_LLM_RX.search(raw) and _CONFIG_VERB_RX.search(raw):
        return True

    if _PROVIDER_NAME_RX.search(raw) and _MODEL_OR_LLM_RX.search(raw):
        return True

    if _PROVIDER_NAME_RX.search(raw) and re.search(
        r"\b(which|what)\b.*\b(provider|api|backend)\b", raw, re.I
    ):
        return True

    return False
