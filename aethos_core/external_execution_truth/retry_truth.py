# SPDX-License-Identifier: Apache-2.0
"""Retry-aware continuity realism — Phase 11.8.1."""

from __future__ import annotations

from typing import Any


def describe_retry_state(*, retries: int, max_retries: int, error: str | None = None) -> dict[str, Any]:
    if retries <= 0:
        return {"retrying": False, "phrase": ""}
    remaining = max(0, max_retries - retries)
    err = (error or "transient execution issue")[:120]
    return {
        "retrying": True,
        "retries": retries,
        "remaining_retries": remaining,
        "phrase": (
            f"The latest verification cycle encountered a {err} and is being retried automatically. "
            "No recovery regression has been observed so far."
            if retries == 1
            else (
                f"External execution is retrying after a transient issue (attempt {retries} of {max_retries}). "
                "Operational continuity remains intact, but progression confidence is bounded until a fresh callback arrives."
            )
        ),
    }


def compose_retry_notification(*, job_type: str, retries: int) -> str | None:
    if retries <= 0:
        return None
    label = job_type.replace("_", " ")
    return (
        f"The latest **{label}** encountered a transient execution issue and is retrying automatically. "
        "I'll surface a grouped update when meaningful progression changes."
    )
