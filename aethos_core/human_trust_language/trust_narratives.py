# SPDX-License-Identifier: Apache-2.0
"""Trust narratives — grounded trust phrasing."""

from __future__ import annotations


def trust_narrative(*, grounded: bool = True) -> str:
    if grounded:
        return "These recommendations consistently appeared across trusted family and regional sources."
    return "Source agreement was mixed — treat these as a starting point for further exploration."
