# SPDX-License-Identifier: Apache-2.0
"""
Consensus engine — compute an agreement matrix from critique scores and select
the winning response.

Algorithm:
1. For each response: collect critique scores from all models that reviewed it.
2. Count how many models "recommended" it (boolean vote).
3. The response with the highest recommendation count wins
   (tiebreak: highest mean critique score).
4. Consensus is reached if recommendation_count / eligible_critics >= threshold.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from aethos_core.arbiter.models import ConsensusResult, CritiqueScore, ModelResponse

_log = logging.getLogger("aethos.arbiter.consensus")


def compute_consensus(
    responses: list[ModelResponse],
    critiques: list[CritiqueScore],
    *,
    threshold: float = 0.6,
) -> ConsensusResult:
    valid = [r for r in responses if not r.error and r.text]
    total_models = len(responses)
    responding_models = len(valid)

    if not valid:
        return ConsensusResult(
            winning_response_id=None,
            winning_model_id=None,
            winning_model_label=None,
            winning_text=None,
            agreement_score=0.0,
            consensus_reached=False,
            consensus_threshold=threshold,
            total_models=total_models,
            responding_models=0,
            agreeing_models=0,
            dissenting_model_ids=[r.model_id for r in responses],
            round_count=0,
            summary="No valid responses were collected from the model pool.",
        )

    if not critiques:
        # No critique round — fall back to the first valid response.
        winner = valid[0]
        return ConsensusResult(
            winning_response_id=winner.response_id,
            winning_model_id=winner.model_id,
            winning_model_label=winner.model_label,
            winning_text=winner.text,
            agreement_score=1.0 / responding_models if responding_models > 0 else 0.0,
            consensus_reached=False,
            consensus_threshold=threshold,
            total_models=total_models,
            responding_models=responding_models,
            agreeing_models=1,
            dissenting_model_ids=[r.model_id for r in valid[1:]],
            round_count=0,
            summary="No critique round completed. First available response selected.",
        )

    scores_by_response: dict[str, list[CritiqueScore]] = defaultdict(list)
    recommenders_by_response: dict[str, set[str]] = defaultdict(set)

    for c in critiques:
        if c.error:
            continue
        scores_by_response[c.target_response_id].append(c)
        if c.recommended:
            recommenders_by_response[c.target_response_id].add(c.critic_model_id)

    resp_by_id = {r.response_id: r for r in valid}

    # Score each response: (mean_score, recommend_count, response_id).
    ranked: list[tuple[float, int, str]] = []
    for resp in valid:
        rid = resp.response_id
        scores = scores_by_response.get(rid, [])
        mean_score = sum(s.overall_score for s in scores) / len(scores) if scores else 0.0
        rec_count = len(recommenders_by_response.get(rid, set()))
        ranked.append((mean_score, rec_count, rid))

    # Sort: primary = recommendation count (desc), secondary = mean score (desc).
    ranked.sort(key=lambda x: (x[1], x[0]), reverse=True)

    best_mean, best_rec_count, best_rid = ranked[0]
    winner = resp_by_id.get(best_rid)

    # Eligible critics = distinct models that completed a (non-error) critique.
    eligible_critics = len({c.critic_model_id for c in critiques if not c.error})
    agreement_score = best_rec_count / eligible_critics if eligible_critics > 0 else 0.0
    consensus_reached = agreement_score >= threshold

    agreeing_ids = recommenders_by_response.get(best_rid, set())
    winner_model_id = winner.model_id if winner else ""
    dissenting = [
        r.model_id
        for r in valid
        if r.model_id not in agreeing_ids and r.model_id != winner_model_id
    ]

    winner_label = winner.model_label if winner else "unknown"
    failed = [r for r in responses if r.error]
    fail_note = ""
    if failed and valid:
        fail_parts = "; ".join(f"{r.model_label}: {r.error}" for r in failed)
        fail_note = f" {len(failed)} model(s) failed ({fail_parts})."

    if consensus_reached:
        summary = (
            f"Consensus reached ({best_rec_count}/{eligible_critics} models agreed, "
            f"{agreement_score:.0%} agreement). "
            f"Winner: {winner_label} (mean critique score: {best_mean:.2f}/1.0)."
            f"{fail_note}"
        )
    else:
        summary = (
            f"No consensus reached ({best_rec_count}/{eligible_critics} models agreed, "
            f"threshold {threshold:.0%} not met). "
            f"Best candidate: {winner_label} (mean score: {best_mean:.2f}/1.0). "
            f"Human review recommended."
            f"{fail_note}"
        )

    return ConsensusResult(
        winning_response_id=best_rid,
        winning_model_id=winner.model_id if winner else None,
        winning_model_label=winner.model_label if winner else None,
        winning_text=winner.text if winner else None,
        agreement_score=round(agreement_score, 4),
        consensus_reached=consensus_reached,
        consensus_threshold=threshold,
        total_models=total_models,
        responding_models=responding_models,
        agreeing_models=best_rec_count,
        dissenting_model_ids=dissenting,
        round_count=1,
        summary=summary,
    )
