# SPDX-License-Identifier: Apache-2.0
"""Pacing engine — conversational rhythm."""

from __future__ import annotations


def pace_response(text: str) -> str:
    # Preserve fenced code/HTML deliveries — pacing must not drop middle paragraphs.
    if "```" in text:
        return text
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if len(paragraphs) <= 3:
        return text
    return "\n\n".join(paragraphs[:3] + [paragraphs[-1]] if paragraphs else [])
