# SPDX-License-Identifier: Apache-2.0
"""Infrastructure truth score — runtime operational truth."""

from __future__ import annotations

from typing import Any


def compute_infrastructure_truth_score(*, components: dict[str, float]) -> dict[str, Any]:
    weights = {"topology": 0.25, "cluster": 0.25, "dependency": 0.25, "recovery": 0.25}
    score = sum(components.get(k, 0.5) * w for k, w in weights.items())
    return {"infrastructure_truth_score": round(score, 2)}
