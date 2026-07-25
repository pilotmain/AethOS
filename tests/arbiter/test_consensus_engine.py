# SPDX-License-Identifier: Apache-2.0
"""Consensus engine unit tests."""

from aethos_core.arbiter.consensus_engine import compute_consensus
from aethos_core.arbiter.models import CritiqueScore, ModelResponse


def _resp(resp_id, model_id, label, text):
    return ModelResponse(
        response_id=resp_id,
        provider="test",
        model_id=model_id,
        model_label=label,
        text=text,
    )


def _critique(critic_id, target_id, score, recommended):
    return CritiqueScore(
        critic_model_id=critic_id,
        target_response_id=target_id,
        accuracy_score=score,
        completeness_score=score,
        reasoning_score=score,
        overall_score=score,
        critique_text="",
        recommended=recommended,
    )


def test_consensus_reached():
    responses = [
        _resp("r1", "model-a", "Model A", "Paris is the capital of France."),
        _resp("r2", "model-b", "Model B", "The capital is Paris."),
        _resp("r3", "model-c", "Model C", "Paris."),
    ]
    critiques = [
        _critique("model-b", "r1", 0.9, True),
        _critique("model-c", "r1", 0.85, True),
        _critique("model-a", "r2", 0.7, False),
        _critique("model-c", "r2", 0.75, False),
        _critique("model-a", "r3", 0.5, False),
        _critique("model-b", "r3", 0.5, False),
    ]
    result = compute_consensus(responses, critiques, threshold=0.6)
    assert result.consensus_reached
    assert result.winning_response_id == "r1"
    assert result.winning_model_label == "Model A"
    assert result.agreement_score >= 0.6


def test_no_consensus_below_threshold():
    responses = [
        _resp("r1", "model-a", "Model A", "Answer A"),
        _resp("r2", "model-b", "Model B", "Answer B"),
        _resp("r3", "model-c", "Model C", "Answer C"),
    ]
    critiques = [
        _critique("model-b", "r1", 0.5, False),
        _critique("model-c", "r1", 0.5, False),
        _critique("model-a", "r2", 0.5, False),
        _critique("model-c", "r2", 0.9, True),
        _critique("model-a", "r3", 0.9, True),
        _critique("model-b", "r3", 0.5, False),
    ]
    result = compute_consensus(responses, critiques, threshold=0.7)
    assert not result.consensus_reached


def test_no_valid_responses():
    responses = [
        ModelResponse(
            response_id="r1",
            provider="test",
            model_id="m1",
            model_label="M1",
            text="",
            error="timeout",
        )
    ]
    result = compute_consensus(responses, [], threshold=0.6)
    assert not result.consensus_reached
    assert result.winning_text is None


def test_no_critiques_falls_back_to_first_response():
    responses = [
        _resp("r1", "model-a", "Model A", "First answer"),
        _resp("r2", "model-b", "Model B", "Second answer"),
    ]
    result = compute_consensus(responses, [], threshold=0.6)
    assert result.winning_response_id == "r1"
    assert not result.consensus_reached
    assert result.round_count == 0


def test_tiebreak_by_mean_score():
    responses = [
        _resp("r1", "model-a", "Model A", "A"),
        _resp("r2", "model-b", "Model B", "B"),
        _resp("r3", "model-c", "Model C", "C"),
    ]
    # r1 and r2 each get exactly one recommendation; r1 has the higher mean.
    critiques = [
        _critique("model-b", "r1", 0.95, True),
        _critique("model-c", "r1", 0.9, False),
        _critique("model-a", "r2", 0.6, True),
        _critique("model-c", "r2", 0.6, False),
        _critique("model-a", "r3", 0.2, False),
        _critique("model-b", "r3", 0.2, False),
    ]
    result = compute_consensus(responses, critiques, threshold=0.9)
    assert result.winning_response_id == "r1"
