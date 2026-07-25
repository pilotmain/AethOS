# SPDX-License-Identifier: Apache-2.0
"""Verification integrity — trust in execution verification."""

from __future__ import annotations

from typing import Any


def assess_verification_integrity(
    *,
    executed: bool = False,
    verified: bool = False,
    verification_errors: int = 0,
    stale_verification: bool = False,
) -> dict[str, Any]:
    """Assess whether verification state is trustworthy."""
    if not executed:
        return {
            "verified": False,
            "executed": False,
            "integrity": "not_applicable",
            "summary": "No execution recorded.",
        }
    if verified and verification_errors == 0 and not stale_verification:
        return {
            "verified": True,
            "executed": True,
            "integrity": "healthy",
            "summary": "Execution verified successfully.",
        }
    if verified and (verification_errors > 0 or stale_verification):
        return {
            "verified": True,
            "executed": True,
            "integrity": "degraded",
            "summary": "Verification present but degraded by errors or staleness.",
        }
    if executed and not verified:
        return {
            "verified": False,
            "executed": True,
            "integrity": "unverified",
            "summary": "Execution completed but verification pending or missing.",
        }
    return {
        "verified": False,
        "executed": executed,
        "integrity": "failed",
        "summary": "Verification failed or unhealthy.",
    }
