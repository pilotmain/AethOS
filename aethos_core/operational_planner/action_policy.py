# SPDX-License-Identifier: Apache-2.0
"""Action policy — readonly vs mutation vs defer."""

from __future__ import annotations

from typing import Literal

ActionType = Literal[
    "provider_wide_readonly",
    "provider_readonly",
    "active_followup",
    "mutation",
    "defer",
    "clarify",
]


def resolve_action_type(*, scope: str, intent: str) -> ActionType:
    if intent == "mutation" and scope in {"provider_service", "active_target", "provider_wide"}:
        if scope == "provider_wide":
            return "clarify"
        return "mutation"

    if scope in {"provider_wide", "all_providers", "workspace_wide"}:
        if intent in {"inventory_health_report", "inventory_list", "discovery"}:
            return "provider_wide_readonly"
        return "provider_wide_readonly"

    if scope == "active_target" and intent in {
        "health_check",
        "verify_operation",
        "fetch_logs",
    }:
        return "active_followup"

    if scope == "provider_service" and intent in {"inventory_list", "inventory_health_report"}:
        return "provider_readonly"

    if intent in {"inventory_health_report", "inventory_list"}:
        return "provider_wide_readonly"

    return "defer"
