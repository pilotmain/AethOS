# SPDX-License-Identifier: Apache-2.0
"""Bounded post-rerun downstream deployment polling configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PostRerunPollConfig:
    deploy_poll_seconds: int = 120
    deploy_poll_interval_seconds: int = 10
    runtime_settle_seconds: int = 30

    @classmethod
    def from_env(cls) -> PostRerunPollConfig:
        return cls(
            deploy_poll_seconds=max(0, _env_int("POST_RERUN_DEPLOY_POLL_SECONDS", 120)),
            deploy_poll_interval_seconds=max(1, _env_int("POST_RERUN_DEPLOY_POLL_INTERVAL_SECONDS", 10)),
            runtime_settle_seconds=max(0, _env_int("POST_RERUN_RUNTIME_SETTLE_SECONDS", 30)),
        )


def _env_int(name: str, default: int) -> int:
    raw = (os.environ.get(name) or "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default
