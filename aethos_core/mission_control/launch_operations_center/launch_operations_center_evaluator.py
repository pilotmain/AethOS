# SPDX-License-Identifier: Apache-2.0
"""FIX 313 — launch operations center evaluator."""

from __future__ import annotations

from typing import Any


def derive_launch_phase(
    *,
    overall_launch_status: str,
    beta_recommendation: str,
) -> str:
    if overall_launch_status == "BLOCKED":
        return "PRE_LAUNCH"
    if beta_recommendation == "EXPAND_BETA":
        return "BETA_EXPANSION"
    if beta_recommendation == "READY_FOR_PUBLIC_REVIEW":
        return "PUBLIC_REVIEW"
    if overall_launch_status == "READY_FOR_PUBLIC_LAUNCH":
        return "LAUNCH_REVIEW"
    if overall_launch_status in {"READY_FOR_LIMITED_BETA", "CONDITIONAL"}:
        return "LIMITED_BETA"
    return "PRE_LAUNCH"


def derive_launch_recommendation(
    *,
    overall_launch_status: str,
    beta_recommendation: str,
    blocker_count: int,
    critical_risk_count: int,
    at_risk_count: int,
    healthy_count: int,
    platform_healthy: bool,
) -> str:
    if overall_launch_status == "BLOCKED" or blocker_count > 0 or critical_risk_count > 0:
        return "BLOCK_LAUNCH"
    if beta_recommendation == "EXPAND_BETA" and platform_healthy and at_risk_count == 0:
        return "EXPAND_BETA"
    if beta_recommendation == "READY_FOR_PUBLIC_REVIEW" and healthy_count >= 1:
        return "PREPARE_PUBLIC_REVIEW"
    if overall_launch_status == "READY_FOR_PUBLIC_LAUNCH" and platform_healthy:
        return "READY_FOR_LAUNCH_REVIEW"
    if overall_launch_status in {"READY_FOR_LIMITED_BETA", "CONDITIONAL"}:
        return "CONTINUE_BETA"
    return "BLOCK_LAUNCH"


def aggregate_blockers(
    *,
    launch_blockers: list[str],
    beta_blockers: list[str],
    operational_blockers: list[str],
    customer_blockers: list[str],
) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for detail in launch_blockers:
        blockers.append(
            {
                "blocker_id": f"launch-{hash(detail) % 10000}",
                "source": "FIX 309",
                "category": "readiness",
                "detail": detail,
                "read_only": True,
            }
        )
    for detail in beta_blockers:
        blockers.append(
            {
                "blocker_id": f"beta-{hash(detail) % 10000}",
                "source": "FIX 312",
                "category": "beta",
                "detail": detail,
                "read_only": True,
            }
        )
    for detail in operational_blockers:
        blockers.append(
            {
                "blocker_id": f"ops-{hash(detail) % 10000}",
                "source": "FIX 200-230",
                "category": "operational",
                "detail": detail,
                "read_only": True,
            }
        )
    for detail in customer_blockers:
        blockers.append(
            {
                "blocker_id": f"customer-{hash(detail) % 10000}",
                "source": "FIX 310",
                "category": "customer",
                "detail": detail,
                "read_only": True,
            }
        )
    return blockers


def aggregate_risks(
    *,
    launch_risks: list[dict[str, Any]],
    beta_risks: list[dict[str, Any]],
    customer_risks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    product: list[dict[str, Any]] = []
    operational: list[dict[str, Any]] = []
    governance: list[dict[str, Any]] = []
    customer: list[dict[str, Any]] = []

    for risk in launch_risks + beta_risks + customer_risks:
        category = str(risk.get("category") or risk.get("domain") or "operational")
        row = {
            "risk_id": risk.get("risk_id"),
            "level": risk.get("level", "medium"),
            "detail": risk.get("detail"),
            "source": risk.get("source"),
            "read_only": True,
        }
        if category in {"product", "product_readiness", "commercial"}:
            product.append(row)
        elif category in {"governance", "permission_issue"}:
            governance.append(row)
        elif category in {"low_adoption", "adoption", "billing_concern", "customer"}:
            customer.append(row)
        else:
            operational.append(row)

    return {
        "product": product,
        "operational": operational,
        "governance": governance,
        "customer": customer,
    }
