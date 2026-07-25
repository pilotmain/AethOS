# SPDX-License-Identifier: Apache-2.0
"""Operational cognition types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OperationalCognitionDecision:
    intent: str
    scope: str
    provider: str | None
    target: str | None
    capabilities: list[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_chain: list[str] = field(default_factory=list)
    execution_strategy: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent": self.intent,
            "scope": self.scope,
            "provider": self.provider,
            "target": self.target,
            "capabilities": list(self.capabilities),
            "confidence": self.confidence,
            "reasoning_chain": list(self.reasoning_chain),
            "execution_strategy": self.execution_strategy,
            "meta": dict(self.meta),
        }
