# SPDX-License-Identifier: Apache-2.0
"""Infrastructure trust score — overall production confidence."""

from __future__ import annotations

from typing import Any


def compute_infrastructure_trust_score(*, components: dict[str, float]) -> dict[str, Any]:
    weights = {
        "temporal": 0.2,
        "stabilization": 0.2,
        "topology": 0.2,
        "verification": 0.2,
        "recovery": 0.2,
    }
    score = sum(components.get(k, 0.5) * w for k, w in weights.items())
    recovery = components.get("recovery", 0.5)
    adjusted = max(0.0, score - max(0, 0.5 - recovery) * 0.1)
    tier = "production-reliable" if adjusted >= 0.85 else "production-ready" if adjusted >= 0.75 else "stable" if adjusted >= 0.65 else "beta"
    return {
        "infrastructure_trust_score": round(adjusted, 2),
        "qualification_tier": tier,
        "summary": f"Production confidence tier: {tier}.",
    }
