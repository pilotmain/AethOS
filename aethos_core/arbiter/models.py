# SPDX-License-Identifier: Apache-2.0
"""Arbiter data contracts — all types for sessions, responses, critiques, consensus."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from time import time
from typing import Any
from uuid import uuid4


class ArbiterStatus(str, Enum):
    PENDING = "pending"
    DISPATCHING = "dispatching"
    CRITIQUING = "critiquing"
    CONSENSUS = "consensus"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    NO_CONSENSUS = "no_consensus"


@dataclass
class ModelResponse:
    """One model's raw response from the dispatch round."""

    response_id: str
    provider: str
    model_id: str
    model_label: str
    text: str
    input_tokens: int = 0
    output_tokens: int = 0
    latency_ms: int = 0
    used_llm: bool = True
    error: str | None = None

    @classmethod
    def error_response(
        cls, provider: str, model_id: str, model_label: str, error: str
    ) -> "ModelResponse":
        return cls(
            response_id=f"resp-{uuid4().hex[:10]}",
            provider=provider,
            model_id=model_id,
            model_label=model_label,
            text="",
            error=error,
            used_llm=False,
        )


@dataclass
class CritiqueScore:
    """One model's critique of another model's response."""

    critic_model_id: str
    target_response_id: str
    accuracy_score: float  # 0.0–1.0
    completeness_score: float  # 0.0–1.0
    reasoning_score: float  # 0.0–1.0
    overall_score: float  # weighted composite
    critique_text: str  # the model's critique in its own words
    recommended: bool  # does this critic recommend this response?
    error: str | None = None

    @property
    def composite(self) -> float:
        return self.overall_score


@dataclass
class ConsensusResult:
    """Final arbiter verdict after all rounds."""

    winning_response_id: str | None
    winning_model_id: str | None
    winning_model_label: str | None
    winning_text: str | None
    agreement_score: float  # 0.0–1.0: fraction of eligible critics that agreed
    consensus_reached: bool
    consensus_threshold: float
    total_models: int
    responding_models: int  # models that returned a non-error response
    agreeing_models: int
    dissenting_model_ids: list[str]
    round_count: int
    summary: str  # 1–2 sentence human-readable verdict


@dataclass
class ArbiterSession:
    """Full lifecycle of one arbiter session."""

    session_id: str = field(default_factory=lambda: f"arb-{uuid4().hex[:12]}")
    chat_session_id: str = "default"
    # Owning tenant, stamped at creation from the request context. Detached fan-out
    # (dispatch/critique threads) re-establishes this tenant so it never resolves
    # another tenant's credentials (Correction 1). "default" in single-tenant mode.
    tenant_id: str = "default"
    prompt: str = ""
    status: ArbiterStatus = ArbiterStatus.PENDING
    model_pool: list[dict[str, str]] = field(default_factory=list)
    responses: list[ModelResponse] = field(default_factory=list)
    critiques: list[CritiqueScore] = field(default_factory=list)
    consensus: ConsensusResult | None = None
    rounds_completed: int = 0
    # Debate history: one entry per revise→re-critique round, capturing each model's
    # revised answer preview + that round's agreement score. Drives the UI timeline.
    debate_rounds: list[dict[str, Any]] = field(default_factory=list)
    started_at: float = field(default_factory=time)
    completed_at: float | None = None
    artifact_id: str | None = None
    error: str | None = None

    @property
    def duration_ms(self) -> int:
        end = self.completed_at or time()
        return int((end - self.started_at) * 1000)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "chat_session_id": self.chat_session_id,
            "tenant_id": self.tenant_id,
            "status": self.status.value,
            "prompt_preview": self.prompt[:300],
            "model_count": len(self.model_pool),
            "response_count": len(self.responses),
            "critique_count": len(self.critiques),
            "rounds_completed": self.rounds_completed,
            "debate_round_count": len(self.debate_rounds),
            "duration_ms": self.duration_ms,
            "consensus": (
                {
                    "reached": self.consensus.consensus_reached,
                    "agreement_score": self.consensus.agreement_score,
                    "winning_model": self.consensus.winning_model_label,
                    "summary": self.consensus.summary,
                }
                if self.consensus
                else None
            ),
            "error": self.error,
        }
