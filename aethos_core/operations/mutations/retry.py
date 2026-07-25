# SPDX-License-Identifier: Apache-2.0
"""Governed retry artifacts — verification polling only."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class RetryAttempt:
    attempt: int
    reason: str
    delay_ms: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "retry_attempt": self.attempt,
            "retry_reason": self.reason,
            "retry_delay_ms": self.delay_ms,
        }


def exponential_backoff_ms(attempt: int, *, base_ms: int = 1000) -> int:
    return min(base_ms * (2 ** max(0, attempt - 1)), 16000)
