# SPDX-License-Identifier: Apache-2.0
"""Idempotency keys for Railway execution requests."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def execution_target_fields(*, plan: dict[str, Any]) -> dict[str, str]:
    return {
        "repo": str(plan.get("repo") or "").strip().lower(),
        "project": str(plan.get("project") or "").strip().lower(),
        "environment": str(plan.get("environment") or "").strip().lower(),
        "service_name": str(plan.get("service_name") or "").strip().lower(),
        "branch": str(plan.get("branch") or "main").strip().lower(),
    }


def derive_idempotency_key(*, plan: dict[str, Any]) -> str:
    """Stable sha256 idempotency key from repo/project/environment/service/branch."""
    fields = execution_target_fields(plan=plan)
    canonical = json.dumps(fields, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return f"ridem-{digest}"
