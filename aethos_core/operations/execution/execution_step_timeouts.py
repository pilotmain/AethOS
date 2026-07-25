# SPDX-License-Identifier: Apache-2.0
"""Bounded timeouts for read-only execution steps."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Callable, TypeVar

T = TypeVar("T")


class ExecutionStepTimeoutError(TimeoutError):
    def __init__(self, step: str, *, timeout_sec: float) -> None:
        self.step = step
        self.timeout_sec = timeout_sec
        super().__init__(f"{step} timed out after {timeout_sec:.0f}s")


def run_with_timeout(
    fn: Callable[[], T],
    *,
    timeout_sec: float,
    step: str = "step",
) -> T:
    """Run ``fn`` in a worker thread with a hard timeout."""
    timeout = max(1.0, float(timeout_sec))
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="aethos-exec-step") as pool:
        fut = pool.submit(fn)
        try:
            return fut.result(timeout=timeout)
        except FuturesTimeoutError as exc:
            raise ExecutionStepTimeoutError(step, timeout_sec=timeout) from exc
