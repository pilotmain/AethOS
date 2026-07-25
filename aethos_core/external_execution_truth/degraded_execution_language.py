# SPDX-License-Identifier: Apache-2.0
"""Calm failure and retry narratives — Phase 11.8.1."""

from __future__ import annotations

from typing import Any


def describe_awaiting_callback(*, entity_name: str | None, job_type: str) -> str:
    agent = entity_name or "Operational agent"
    label = job_type.replace("_", " ")
    return (
        f"The latest **{agent}** {label} job was dispatched successfully, though the external execution "
        "runtime has not reported a fresh completion signal yet. Operational continuity remains intact, "
        "but current progression confidence is limited until the next callback window."
    )


def describe_orphaned_execution(*, entity_name: str | None, job_type: str) -> str:
    agent = entity_name or "Operational agent"
    label = job_type.replace("_", " ")
    return (
        f"Operational continuity for **{agent}** ({label}) remains partially unresolved because the external "
        "execution runtime has not produced a fresh callback within the expected verification window. "
        "You can retry the job or inspect the latest artifact — the system is not assuming completion or failure."
    )


def describe_degraded_fallback(*, reason: str = "external runner unavailable") -> str:
    return (
        f"External execution is temporarily unavailable ({reason}). "
        "AethOS is continuing through the governed embedded runner while preserving honest lifecycle state."
    )


def describe_recovery_verification_bounded(*, window: str | None = None) -> str:
    suffix = f" for the {window} window" if window else ""
    return (
        f"Primary recovery signals remain healthy{suffix}, though delayed verification is still waiting on "
        "external execution confirmation. Extended monitoring remains active — not fully proven until sustained verification holds."
    )
