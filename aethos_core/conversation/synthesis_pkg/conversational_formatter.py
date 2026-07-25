# SPDX-License-Identifier: Apache-2.0
"""Conversational formatter — premium conversational structure."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract


def format_recommendations(
    *,
    contract: IntentContract,
    items: list[dict[str, Any]],
    confidence_phrase: str,
) -> str:
    count = len(items)
    intro = _intro(contract, count, confidence_phrase)
    lines = [intro, ""]
    for item in items:
        rank = item.get("rank", 0)
        name = item.get("name", "Recommendation")
        location = item.get("location") or ""
        explanation = item.get("explanation") or item.get("description", "")
        loc_suffix = f" — {location}" if location else ""
        lines.append(f"{rank}. **{name}**{loc_suffix}")
        if explanation:
            lines.append(f"   {explanation}")
        lines.append("")
    return "\n".join(lines).strip()


def _intro(contract: IntentContract, count: int, confidence_phrase: str) -> str:
    if contract.result_count and contract.geographic_filter:
        return (
            f"Here are the {count} that consistently appeared across {confidence_phrase} "
            f"for **{contract.geographic_filter}**:"
        )
    if contract.result_count:
        return f"Here are the {count} that consistently appeared across {confidence_phrase}:"
    return f"Here are {count} recommendations from {confidence_phrase}:"
