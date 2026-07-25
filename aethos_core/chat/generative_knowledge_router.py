# SPDX-License-Identifier: Apache-2.0
"""Route open-ended knowledge questions to provider + optional raw web evidence."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from aethos_core.provider.completion import complete_chat, provider_configured

if TYPE_CHECKING:
    from aethos_core.chat.service import ChatTurnResult

_COMPARE_RX = re.compile(
    r"\bcompare\b.*\b(vs|versus|to|with|and)\b|\b(vs|versus)\b.*\bcompare\b",
    re.I,
)
_CAPABILITY_COMPARE_RX = re.compile(
    r"\bcompare\b.*\b(capabilit(?:y|ies)|features?|stack)\b",
    re.I,
)
_TABLE_RX = re.compile(r"\btable\b|\bin columns\b|\bside by side\b", re.I)
_EXCLUDE_RX = re.compile(
    r"\b(railway|vercel|github|deploy|redeploy|restart|mission control|fix\s+\d+|pilot\s+\d+)\b",
    re.I,
)


def is_generative_knowledge_request(text: str) -> bool:
    """True for product/capability comparisons — not provider operational commands."""
    raw = (text or "").strip()
    if len(raw) < 8:
        return False
    if _EXCLUDE_RX.search(raw):
        return False
    return bool(_COMPARE_RX.search(raw) or _CAPABILITY_COMPARE_RX.search(raw))


def _raw_web_evidence_snippets(query: str, *, max_results: int = 5) -> str:
    """Return raw search snippets — no research polish pipeline."""
    from aethos_core.config import get_settings
    from aethos_core.research.research_config import is_research_search_configured
    from aethos_core.research.research_provider import get_research_provider

    settings = get_settings()
    if not settings.web_research_enabled or not is_research_search_configured(settings):
        return ""

    provider = get_research_provider()
    results = provider.search(query, max_results=max_results)
    if not results.ok or not results.results:
        return ""

    lines = [f"Query: {query}", ""]
    for idx, row in enumerate(results.results[:max_results], start=1):
        lines.append(f"{idx}. {row.title} — {row.url}")
        if row.snippet:
            lines.append(f"   {row.snippet[:400]}")
    return "\n".join(lines)


def _format_instruction(user_text: str) -> str:
    if _TABLE_RX.search(user_text):
        return "The user asked for a markdown table — use one and match their column focus."
    return (
        "The user did not ask for a table — answer in concise prose or short bullets; "
        "do not default to a comparison table."
    )


def route_generative_knowledge_turn(
    text: str,
    *,
    session_id: str = "default",
    channel: str = "chat",
) -> "ChatTurnResult | None":
    """Answer with raw web snippets + provider brain — no tracked jobs or research polish."""
    from aethos_core.chat.service import ChatTurnResult

    raw = (text or "").strip()
    if not is_generative_knowledge_request(raw):
        return None

    evidence_block = _raw_web_evidence_snippets(raw)
    research_meta = {
        "lane": "generative_knowledge",
        "web_research_used": "true" if evidence_block else "false",
        "presentation_mode": "direct",
        "suppress_governance_footer": "true",
    }

    if not provider_configured() and not evidence_block:
        return ChatTurnResult(
            reply=(
                "I can research and compare products once **generative intelligence** and optionally "
                "**web research** (Tavily) are configured in `.env`.\n\n"
                f"Your question: _{raw[:240]}_"
            ),
            intent="generative_knowledge_not_configured",
            used_llm=False,
            meta={"lane": "generative_knowledge", "configured": "false"},
        )

    format_hint = _format_instruction(raw)
    prompt_parts = [
        "You are AethOS answering an open knowledge question in chat.",
        "Match the user's exact wording and requested format — do not reuse a generic comparison template.",
        format_hint,
        "For AethOS facts, use your identity context honestly (capabilities and limits).",
        "For external products, ground claims in the web snippets below when present; label uncertainty.",
        "Do not claim missing session memory. Do not ask the user to paste product sheets.",
        "",
        f"User message (answer this exactly): {raw}",
    ]
    if evidence_block:
        prompt_parts.extend(["", "Raw web snippets (unprocessed):", evidence_block])

    prov = complete_chat(
        "\n".join(prompt_parts),
        session_id=session_id,
        channel=channel,
        include_identity=True,
        system_overlay=(
            "Open-knowledge mode: be direct, human, and format-faithful. "
            "Vary structure turn-to-turn based on what the user asked."
        ),
    )
    meta = {
        **research_meta,
        "provider": prov.provider,
        "model": prov.model,
    }
    return ChatTurnResult(
        reply=prov.text,
        intent="generative_knowledge",
        used_llm=prov.used_llm,
        provider=prov.provider,
        model=prov.model,
        meta=meta,
    )
