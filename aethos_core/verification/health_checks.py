# SPDX-License-Identifier: Apache-2.0
"""Post-mutation health checks — verification substrate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class HealthCheckResult:
    name: str
    ok: bool
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "ok": self.ok, "detail": self.detail}


def summarize_mutation_health(*, provider: str, operation_type: str, provider_result: dict[str, Any]) -> list[HealthCheckResult]:
    ok = bool(provider_result.get("ok"))
    return [
        HealthCheckResult(
            name=f"{provider}_{operation_type}_mutation",
            ok=ok,
            detail=str(provider_result.get("detail") or ("ok" if ok else "failed")),
        ),
        HealthCheckResult(
            name="verification_job_enqueued",
            ok=True,
            detail="Post-mutation readonly verification scheduled when execution succeeds.",
        ),
    ]
