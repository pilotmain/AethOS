# SPDX-License-Identifier: Apache-2.0
"""Recommendation explanations — calm rationale."""

from __future__ import annotations

from typing import Any


def build_explanation(item: dict[str, Any]) -> str:
    desc = (item.get("description") or "").strip()
    if len(desc) > 160:
        desc = desc[:157] + "..."
    name = (item.get("name") or "").lower()
    if "toddler" in desc.lower() or "younger" in desc.lower():
        return desc or "Excellent for younger children with family-friendly amenities."
    if "dinosaur" in name or "dinosaur" in desc.lower():
        return desc or "Popular themed playground with toddler-friendly sections."
    if "shaded" in desc.lower():
        return desc or "Well-rated for shaded seating and accessibility."
    return desc or "Highly rated by family and regional sources."
