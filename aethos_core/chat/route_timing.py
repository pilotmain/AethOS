# SPDX-License-Identifier: Apache-2.0
"""Per-turn route timing — attached to internal route trace only."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from time import perf_counter
from typing import Any

_turn_timing: contextvars.ContextVar["TurnTiming | None"] = contextvars.ContextVar("chat_turn_timing", default=None)


@dataclass
class TurnTiming:
    started_at: float = field(default_factory=perf_counter)
    router_started_at: float | None = None
    router_marked: bool = False
    hydration_ms: int = 0
    router_ms: int = 0
    finalizer_ms: int = 0
    provider_calls_ms: int = 0
    model_ms: int = 0
    tools_ms: int = 0

    def total_ms(self) -> int:
        return int((perf_counter() - self.started_at) * 1000)

    def to_trace_dict(self) -> dict[str, str]:
        return {
            "total_ms": str(self.total_ms()),
            "hydration_ms": str(self.hydration_ms),
            "router_ms": str(self.router_ms),
            "finalizer_ms": str(self.finalizer_ms),
            "provider_calls_ms": str(self.provider_calls_ms),
            "model_ms": str(self.model_ms),
            "tools_ms": str(self.tools_ms),
        }


def begin_turn_timing() -> TurnTiming:
    timing = TurnTiming()
    _turn_timing.set(timing)
    return timing


def get_turn_timing() -> TurnTiming | None:
    return _turn_timing.get()


def clear_turn_timing() -> None:
    _turn_timing.set(None)


def add_hydration_ms(ms: int) -> None:
    timing = get_turn_timing()
    if timing is not None and ms > 0:
        timing.hydration_ms += ms


def mark_router_started() -> None:
    timing = get_turn_timing()
    if timing is not None and timing.router_started_at is None:
        timing.router_started_at = perf_counter()


def mark_router_complete() -> None:
    timing = get_turn_timing()
    if timing is None or timing.router_marked or timing.router_started_at is None:
        return
    timing.router_ms = int((perf_counter() - timing.router_started_at) * 1000)
    timing.router_marked = True


def set_router_ms(ms: int) -> None:
    timing = get_turn_timing()
    if timing is not None:
        timing.router_ms = ms
        timing.router_marked = True


def add_finalizer_ms(ms: int) -> None:
    timing = get_turn_timing()
    if timing is not None and ms > 0:
        timing.finalizer_ms += ms


def set_provider_calls_ms(ms: int) -> None:
    timing = get_turn_timing()
    if timing is not None:
        timing.provider_calls_ms = ms


def add_model_ms(ms: int) -> None:
    """Accumulate wall time spent in LLM completion HTTP calls this turn."""
    timing = get_turn_timing()
    if timing is not None and ms > 0:
        timing.model_ms += ms


def add_tools_ms(ms: int) -> None:
    """Accumulate wall time spent executing agent tools this turn."""
    timing = get_turn_timing()
    if timing is not None and ms > 0:
        timing.tools_ms += ms


def timing_for_route_trace() -> dict[str, Any]:
    timing = get_turn_timing()
    if timing is None:
        return {}
    return timing.to_trace_dict()
