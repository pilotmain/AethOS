# SPDX-License-Identifier: Apache-2.0
"""Recommendation ranking — quality ranking."""

from __future__ import annotations

from typing import Any


def rank_recommendations(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(items, key=lambda i: float(i.get("score") or 0), reverse=True)
