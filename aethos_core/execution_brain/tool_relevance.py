# SPDX-License-Identifier: Apache-2.0
"""Tool/skill relevance routing — pick only the tools a query actually needs.

The agent ships ~37 model-facing tools. Sending all of them on every turn bloats the
prompt (cost) and dilutes the model's attention ("context rot"). This module scores each
tool against the user's prompt and keeps the most relevant ``max_tools`` plus a small
always-on core, so simple turns carry a tight, sharp toolset.

Default scorer is **lexical** (dependency-free, deterministic, zero token cost). It is
structured so an embedding-based scorer can be dropped in later behind the same interface.

Safety: this is opt-in (``TOOL_RELEVANCE_ENABLED``) and never trims when the prompt is
empty or the catalog already fits under ``max_tools`` — so default behaviour is unchanged.
"""

from __future__ import annotations

import re
from typing import Any

# Broadly-useful tools kept regardless of the query, so the agent is never crippled.
CORE_TOOL_NAMES = frozenset({"web_search", "skill_recall", "memory_recall", "canvas_render"})

_STOPWORDS = frozenset(
    """
    the a an and or of to for in on at is are was were be been being do does did with without
    from by as it this that these those my your our their his her its can could should would
    will shall may might please help me you we i need want get show tell give make let about
    """.split()
)

_TOKEN_RX = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN_RX.findall((text or "").lower()) if len(t) >= 3 and t not in _STOPWORDS}


def _tool_text(tool: dict[str, Any]) -> str:
    parts = [str(tool.get("name", "")).replace("_", " ")]
    desc = tool.get("description") or ""
    parts.append(str(desc))
    return " ".join(parts)


def score_tool(tool: dict[str, Any], prompt_tokens: set[str]) -> int:
    """Lexical relevance: overlap between prompt tokens and the tool's name/description.

    Name-token matches are weighted higher than description matches.
    """
    name_tokens = _tokens(str(tool.get("name", "")).replace("_", " "))
    desc_tokens = _tokens(str(tool.get("description") or ""))
    name_hits = len(prompt_tokens & name_tokens)
    desc_hits = len(prompt_tokens & desc_tokens)
    return name_hits * 3 + desc_hits


def select_relevant_tools(
    schemas: list[dict[str, Any]],
    prompt: str | None,
    *,
    max_tools: int = 14,
    core_names: frozenset[str] = CORE_TOOL_NAMES,
) -> list[dict[str, Any]]:
    """Return a relevance-trimmed copy of ``schemas`` preserving original order.

    No-ops (returns the input unchanged) when there is no prompt or the catalog already
    fits within ``max_tools`` — so enabling this can only ever shrink, never reorder under
    the threshold or drop tools when trimming isn't needed.
    """
    if not prompt or not prompt.strip():
        return schemas
    if len(schemas) <= max_tools:
        return schemas

    ptoks = _tokens(prompt)
    if not ptoks:
        return schemas

    kept: set[int] = set()
    # 1) Always keep the core tools that exist in this catalog.
    for i, t in enumerate(schemas):
        if str(t.get("name")) in core_names:
            kept.add(i)

    # 2) Rank the rest by score and fill up to max_tools (only scored > 0).
    scored = sorted(
        ((score_tool(t, ptoks), i) for i, t in enumerate(schemas) if i not in kept),
        key=lambda x: (x[0], -x[1]),
        reverse=True,
    )
    for sc, i in scored:
        if len(kept) >= max_tools:
            break
        if sc <= 0:
            break
        kept.add(i)

    # Preserve original order for output stability.
    return [t for i, t in enumerate(schemas) if i in kept]
