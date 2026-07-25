# SPDX-License-Identifier: Apache-2.0
"""Image intelligence — image version + risk analysis."""

from __future__ import annotations

from typing import Any


def analyze_images(*, containers: list[dict[str, Any]]) -> dict[str, Any]:
    risks: list[str] = []
    for c in containers:
        image = str(c.get("image") or "")
        if image.endswith(":latest"):
            risks.append(f"{c.get('name')}: floating latest tag")
        if "dev" in image.lower():
            risks.append(f"{c.get('name')}: development image in runtime")
    return {
        "image_risk_count": len(risks),
        "risks": risks,
        "summary": "Image versions stable." if not risks else f"{len(risks)} image risk signals detected.",
    }
