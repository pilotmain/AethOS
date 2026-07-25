# SPDX-License-Identifier: Apache-2.0
"""Deterministic Railway provider-wide health fixture for certification runs."""

from __future__ import annotations

import os
from typing import Any


def is_certification_mode() -> bool:
    flag = (os.environ.get("AETHOS_CERTIFICATION_MODE") or "").strip().lower()
    return flag in {"1", "true", "yes", "on"}


def certification_fixture_rows() -> list[dict[str, Any]]:
    """Canned inventory: healthy + failed services for routing/render certification."""
    return [
        {
            "service": "pilotos-api",
            "project": "pilotos",
            "environment": "production",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-pilotos-api",
        },
        {
            "service": "MongoDB",
            "project": "pilotcore-sales-engine",
            "environment": "production",
            "status": "failed",
            "health": "failed",
            "deployment_state": "failed",
            "service_id": "svc-mongo",
        },
        {
            "service": "api",
            "project": "atlas-trader",
            "environment": "production",
            "status": "running",
            "health": "healthy",
            "deployment_state": "success",
            "service_id": "svc-atlas-api",
        },
    ]
