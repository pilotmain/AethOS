# SPDX-License-Identifier: Apache-2.0
"""FIX 314 — public launch readiness freeze evaluator."""

from __future__ import annotations

from typing import Any


def derive_launch_recommendation_freeze(
    *,
    overall_launch_status: str,
    launch_recommendation: str,
    beta_recommendation: str,
    blocker_count: int,
    critical_risk_count: int,
    trust_baseline_count: int,
    platform_healthy: bool,
    product_ready: bool,
) -> str:
    if overall_launch_status == "BLOCKED" or blocker_count > 0 or critical_risk_count > 0:
        return "NOT_READY"
    if launch_recommendation in {"READY_FOR_LAUNCH_REVIEW", "PREPARE_PUBLIC_REVIEW"} and platform_healthy:
        return "READY_FOR_LAUNCH_DECISION"
    if launch_recommendation == "PREPARE_PUBLIC_REVIEW" or beta_recommendation == "READY_FOR_PUBLIC_REVIEW":
        return "PUBLIC_REVIEW_READY"
    if overall_launch_status in {"READY_FOR_LIMITED_BETA", "CONDITIONAL"} and product_ready:
        return "LIMITED_BETA_READY"
    if launch_recommendation in {"CONTINUE_BETA", "EXPAND_BETA"} and trust_baseline_count >= 1:
        return "LIMITED_BETA_READY"
    return "NOT_READY"


def summarize_trust_baselines(
    *,
    fix_186: dict[str, Any],
    fix_192: dict[str, Any],
    fix_194: dict[str, Any],
    fix_196: dict[str, Any],
    fix_186_ok: bool,
    fix_192_ok: bool,
    fix_194_ok: bool,
    fix_196_ok: bool,
) -> list[dict[str, Any]]:
    rows = [
        {
            "baseline_id": "aethos-dogfood",
            "product": "AethOS",
            "fix": "FIX 186",
            "available": fix_186_ok,
            "trust_recommendation": fix_186.get("trust_recommendation") if fix_186_ok else None,
            "trust_state": fix_186.get("trust_recommendation") or "unavailable",
            "frozen": True,
            "read_only": True,
        },
        {
            "baseline_id": "pilotos-ui",
            "product": "PilotOS UI",
            "fix": "FIX 192",
            "available": fix_192_ok,
            "trust_recommendation": fix_192.get("trust_recommendation") if fix_192_ok else None,
            "trust_state": fix_192.get("trust_recommendation") or "unavailable",
            "frozen": True,
            "read_only": True,
        },
        {
            "baseline_id": "atlas-trader",
            "product": "Atlas Trader",
            "fix": "FIX 194",
            "available": fix_194_ok,
            "trust_recommendation": fix_194.get("trust_recommendation") if fix_194_ok else None,
            "trust_state": fix_194.get("trust_recommendation") or "unavailable",
            "frozen": True,
            "read_only": True,
        },
        {
            "baseline_id": "nexora",
            "product": "Nexora",
            "fix": "FIX 196",
            "available": fix_196_ok,
            "trust_recommendation": fix_196.get("trust_recommendation") if fix_196_ok else None,
            "trust_state": fix_196.get("trust_recommendation") or "unavailable",
            "frozen": True,
            "read_only": True,
        },
    ]
    return rows


def build_evidence_timeline(
    *,
    trust_rows: list[dict[str, Any]],
    launch_status: str,
    beta_recommendation: str,
    ops_recommendation: str,
) -> list[dict[str, Any]]:
    timeline: list[dict[str, Any]] = []
    for row in trust_rows:
        if row.get("available"):
            timeline.append(
                {
                    "event_id": f"trust-{row['baseline_id']}",
                    "phase": "trust_baseline",
                    "fix": row["fix"],
                    "detail": f"{row['product']} trust freeze composed",
                    "read_only": True,
                }
            )
    timeline.extend(
        [
            {
                "event_id": "launch-readiness-assessment",
                "phase": "launch_readiness",
                "fix": "FIX 309",
                "detail": f"Launch readiness assessed: {launch_status}",
                "read_only": True,
            },
            {
                "event_id": "beta-launch-program",
                "phase": "beta_program",
                "fix": "FIX 312",
                "detail": f"Beta recommendation: {beta_recommendation}",
                "read_only": True,
            },
            {
                "event_id": "launch-operations-center",
                "phase": "launch_operations",
                "fix": "FIX 313",
                "detail": f"Operations recommendation: {ops_recommendation}",
                "read_only": True,
            },
        ]
    )
    return timeline
