# SPDX-License-Identifier: Apache-2.0
"""FIX 122 — canary + shadow deployment policy contract."""

from __future__ import annotations

from typing import Final, Literal

DeploymentStrategy = Literal["shadow_only", "shadow_then_canary", "canary_governed"]
TrafficSegmentKind = Literal["synthetic_verification", "shadow_mirror_simulated", "canary_slice_simulated"]
TrafficMutationBoundary = Literal["blocked", "synthetic_only"]

CANARY_SHADOW_POLICY_SCHEMA_VERSION: Final[str] = "production_canary_shadow_policy_v1"

AUTONOMOUS_PRODUCTION_DEPLOYMENT_PERMITTED: Final[bool] = False
AUTOMATIC_TRAFFIC_MUTATION_PERMITTED: Final[bool] = False
AUTOMATIC_PROMOTION_PERMITTED: Final[bool] = False

# Governed canary percentage ceiling (simulated; no real traffic mutation).
DEFAULT_MAX_CANARY_PERCENT: Final[int] = 5
CANARY_PERCENTAGE_TIERS: Final[tuple[int, ...]] = (0, 1, 5, 10, 25)

SHADOW_TRAFFIC_POLICY: Final[dict[str, str]] = {
    "mode": "shadow_rehearsal",
    "real_traffic_percent": "0",
    "synthetic_verification_required": "true",
    "production_infra_mutation": "blocked",
}

CANARY_TRAFFIC_POLICY: Final[dict[str, str]] = {
    "mode": "canary_governed",
    "real_traffic_percent": "capped_by_policy",
    "synthetic_verification_required": "true",
    "production_infra_mutation": "blocked",
}

SYNTHETIC_VERIFICATION_TRAFFIC_PHRASE: Final[str] = (
    "I authorize recording synthetic verification traffic for governed production Railway canary policy."
)
