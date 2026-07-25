# SPDX-License-Identifier: Apache-2.0
"""Canonical verification artifacts."""

from __future__ import annotations

from time import time
from typing import Any


def build_verification_artifact(
    *,
    provider: str,
    operation: str,
    target: str | None,
    linked_mutation_execution: str,
    verification_result: str,
    evidence: dict[str, Any] | None = None,
    readonly_job_id: str | None = None,
) -> dict[str, Any]:
    return {
        "verification_type": "readonly_verification",
        "provider": provider,
        "operation": operation,
        "target": target,
        "verification_result": verification_result,
        "linked_mutation_execution": linked_mutation_execution,
        "readonly_verification_job_id": readonly_job_id,
        "verified_at": time(),
        "evidence": evidence or {},
    }
