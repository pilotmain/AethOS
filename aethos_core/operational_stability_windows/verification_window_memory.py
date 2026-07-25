# SPDX-License-Identifier: Apache-2.0
"""Verification window memory — historical convergence."""

from __future__ import annotations

from typing import Any

_LOG: list[dict[str, Any]] = []


def record_window_convergence(*, qualified: bool) -> dict[str, Any]:
    entry = {"qualified": qualified}
    _LOG.append(entry)
    if len(_LOG) > 50:
        del _LOG[:-50]
    return {"window_history_count": len(_LOG), "latest": entry}
