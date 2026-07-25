# SPDX-License-Identifier: Apache-2.0
"""Ranking convergence — enforce exact ranking constraints."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.synthesis_pkg.intent_contracts import IntentContract
from aethos_core.recommendation_intelligence.deduplication import dedupe_recommendations
from aethos_core.recommendation_intelligence.recommendation_ranking import rank_recommendations


def converge_ranking(
    *,
    items: list[dict[str, Any]],
    contract: IntentContract,
) -> list[dict[str, Any]]:
    ranked = rank_recommendations(items)
    if contract.deduplicate:
        ranked = dedupe_recommendations(ranked)
    limit = contract.result_count or len(ranked)
    if contract.result_count is not None:
        ranked = ranked[: contract.result_count]
    else:
        ranked = ranked[:limit]
    for i, item in enumerate(ranked, start=1):
        item["rank"] = i
    return ranked
