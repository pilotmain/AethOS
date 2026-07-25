# SPDX-License-Identifier: Apache-2.0
"""Recommendation constraints — strict recommendation limits."""

from __future__ import annotations

from typing import Any

from aethos_core.conversation.intent_contracts import IntentContract


def apply_recommendation_limits(*, items: list[dict[str, Any]], contract: IntentContract) -> list[dict[str, Any]]:
    if contract.result_count is not None:
        return items[: contract.result_count]
    return items
