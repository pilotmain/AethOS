# SPDX-License-Identifier: Apache-2.0
"""Research entity alignment — competitor/entity grounding for research pipeline."""

from __future__ import annotations

from typing import Any

from aethos_core.entity_grounding.entity_disambiguation import ground_entity_query


def align_research_entity(*, query: str, session_id: str = "default") -> dict[str, Any]:
    grounding = ground_entity_query(query=query, session_id=session_id)
    return {
        **grounding,
        "aligned_query": grounding.get("grounded_query") or query,
        "summary": grounding.get("summary", "Research entity alignment evaluated."),
    }
