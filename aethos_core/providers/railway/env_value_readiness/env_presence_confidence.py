# SPDX-License-Identifier: Apache-2.0
"""Env presence confidence — metadata only, never secret values."""

from __future__ import annotations

from enum import Enum
from typing import Any


class EnvPresenceConfidence(str, Enum):
    CONFIRMED_PRESENT = "confirmed_present"
    INFERRED_PRESENT = "inferred_present"
    DEFAULTED = "defaulted"
    MISSING = "missing"
    STALE = "stale"
    UNREADABLE = "unreadable"


def resolve_presence_confidence(entry: dict[str, Any] | None) -> EnvPresenceConfidence:
    if not entry:
        return EnvPresenceConfidence.MISSING
    if entry.get("unreadable"):
        return EnvPresenceConfidence.UNREADABLE
    if not entry.get("present"):
        return EnvPresenceConfidence.MISSING
    rotation = str(entry.get("rotation_state") or "").lower()
    if rotation in {"expired", "aging"}:
        return EnvPresenceConfidence.STALE
    if entry.get("using_default") or str(entry.get("source") or "") in {
        "deployment_default",
        "deployment_defaults",
        "plan_default",
    }:
        return EnvPresenceConfidence.DEFAULTED
    source = str(entry.get("source") or "")
    if source in {"credential_center", "secure_store_reference"}:
        return EnvPresenceConfidence.CONFIRMED_PRESENT
    if source == "local_env_dev_only":
        return EnvPresenceConfidence.INFERRED_PRESENT
    return EnvPresenceConfidence.CONFIRMED_PRESENT
