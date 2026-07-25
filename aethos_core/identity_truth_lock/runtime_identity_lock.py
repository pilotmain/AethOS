# SPDX-License-Identifier: Apache-2.0
"""FIX 316B — runtime identity lock helpers."""

from __future__ import annotations

from typing import Any

from aethos_core.identity_truth_lock.identity_truth_lock_contract import (
    AUTHORITY_FLAGS,
    IDENTITY_TRUTH_LOCK_FIX,
    IDENTITY_TRUTH_LOCK_ROUTE_ID,
)


def build_runtime_identity_lock(*, runtime_provider: str, runtime_model: str) -> dict[str, Any]:
    return {
        "fix": IDENTITY_TRUTH_LOCK_FIX,
        "route_id": IDENTITY_TRUTH_LOCK_ROUTE_ID,
        "identity_responses_bypass_provider_self_identity": True,
        "identity_source": "platform_identity_registry",
        "creator_source": "creator_attribution_registry",
        "provider_source": "provider_attribution_registry",
        "runtime_provider": runtime_provider,
        "runtime_model": runtime_model,
        "authority_flags": dict(AUTHORITY_FLAGS),
    }


def runtime_identity_lock_meta(*, classification: str) -> dict[str, str]:
    return {
        "runtime_identity_lock": "true",
        "identity_truth_lock_fix": IDENTITY_TRUTH_LOCK_FIX,
        "identity_source": "platform_identity_registry",
        "bypass_provider_self_identity": "true",
        "runtime_classification": classification,
    }
