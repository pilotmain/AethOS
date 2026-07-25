# SPDX-License-Identifier: Apache-2.0
"""Realism runtime — conversational realism orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.realism.anti_generic import is_consultant_phrasing, is_generic_ai_response


def assess_conversational_realism(*, sample: str = "") -> dict[str, Any]:
    generic = is_generic_ai_response(sample) if sample else False
    consultant = is_consultant_phrasing(sample) if sample else False
    return {
        "generic_blocked": not generic,
        "consultant_blocked": not consultant,
        "realism_active": True,
        "summary": "Anti-generic conversational realism active — stateless fallback phrasing suppressed.",
    }
