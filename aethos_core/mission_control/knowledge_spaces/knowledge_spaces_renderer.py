# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — Markdown renderer for knowledge space search."""

from __future__ import annotations

from typing import Any


def render_knowledge_spaces_search(payload: dict[str, Any]) -> str:
    lines = [
        "# Mission Knowledge Spaces (FIX 141 — semantic retrieval)",
        "",
        f"- query: `{payload.get('query', '')}`",
        f"- focal space: `{payload.get('focal_space_id') or 'all'}`",
        f"- knowledge spaces indexed: **{payload.get('knowledge_space_count', 0)}**",
        f"- corpus documents: **{payload.get('document_corpus_size', 0)}**",
        f"- autonomous action: **{payload.get('autonomous_action_enabled', False)}** _(always false)_",
        "",
        payload.get("invariant", ""),
        "",
        "## Have we seen this before?",
        "",
    ]
    seen = payload.get("seen_before") or {}
    lines.append(f"- likely seen before: **{seen.get('likely_seen_before', False)}** ({seen.get('match_count', 0)} strong matches)")
    for match in seen.get("top_matches") or []:
        lines.append(
            f"  - [{match.get('category')}] score={match.get('relevance_score')} — {match.get('text', '')[:120]}"
        )

    lines.extend(["", "## Search results", ""])
    for hit in payload.get("search_results") or []:
        lines.append(
            f"- **{hit.get('relevance_score', 0):.2f}** [{hit.get('category')}] `{hit.get('space_id', '')}` — "
            f"{str(hit.get('text', ''))[:140]}"
        )

    lines.extend(["", "## Related missions", ""])
    related = payload.get("related_missions") or []
    if not related:
        lines.append("_No related mission spaces above threshold._")
    for row in related:
        lines.append(
            f"- `{row.get('space_id', '')}` score={row.get('relevance_score')} "
            f"sessions={', '.join(row.get('session_ids') or [])}"
        )

    lines.extend(["", "## Recommendations (not executable)", ""])
    for rec in payload.get("recommendations") or []:
        lines.append(f"- [{rec.get('kind', '')}] {rec.get('recommendation', '')}")

    recall = payload.get("operational_context_recall") or {}
    lines.extend(
        [
            "",
            "## Operational context recall",
            "",
            f"- recall confidence: **{recall.get('recall_confidence', 0)}**",
            "",
            "_FIX 141 is read-only semantic retrieval — recommendations only, no autonomous action._",
        ]
    )
    return "\n".join(lines)
