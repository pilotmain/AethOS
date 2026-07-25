# SPDX-License-Identifier: Apache-2.0
"""Deployment runtime — rollout + recovery verification."""

from __future__ import annotations

from typing import Any


def assess_deployment_runtime(*, runtime_snapshot: dict[str, Any]) -> dict[str, Any]:
    deployment = runtime_snapshot.get("deployment") or {}
    if not isinstance(deployment, dict):
        deployment = {}
    desired = int(deployment.get("replicas_desired") or deployment.get("replicas") or 0)
    ready = int(deployment.get("replicas_ready") or 0)
    updated = bool(deployment.get("updated") or deployment.get("rollout_complete"))
    return {
        "replicas_desired": desired,
        "replicas_ready": ready,
        "rollout_complete": updated and ready >= desired and desired > 0,
        "summary": (
            f"Deployment {ready}/{desired} replicas ready."
            if desired
            else "Deployment state not provided."
        ),
    }
