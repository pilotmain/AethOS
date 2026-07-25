# SPDX-License-Identifier: Apache-2.0
"""Capability audit — end-to-end verification rollup."""

from __future__ import annotations

from typing import Any

AUDIT_CATEGORIES = [
    "provider_mutations",
    "restart_flows",
    "deployments",
    "browser_evidence",
    "research_runtime",
    "replay_reconstruction",
    "engineering_execution",
    "sandbox_integrity",
    "rollback_logic",
    "operational_memory",
]


def run_capability_audit() -> dict[str, Any]:
    from aethos_core.operational_truth.capability_truth_matrix import build_capability_truth_matrix

    matrix = build_capability_truth_matrix()
    by_category: dict[str, list[dict[str, Any]]] = {}
    for row in matrix:
        cat = str(row.get("category") or "other")
        by_category.setdefault(cat, []).append(row)

    audits: list[dict[str, Any]] = []
    category_map = {
        "provider_mutations": "provider_mutations",
        "observation": "browser_evidence",
        "channels": "research_runtime",
        "engineering": "engineering_execution",
        "reliability": "replay_reconstruction",
    }

    for category in AUDIT_CATEGORIES:
        rows = []
        for cap_cat, audit_cat in category_map.items():
            if audit_cat == category:
                rows.extend(by_category.get(cap_cat, []))
        if category == "sandbox_integrity":
            rows = [r for r in matrix if r.get("id") == "sandbox_execution"]
        if category == "rollback_logic":
            rows = [r for r in matrix if "restart" in str(r.get("operation") or "") or "redeploy" in str(r.get("operation") or "")]
        if not rows:
            audits.append({
                "category": category,
                "status": "not_audited",
                "coverage_pct": 0,
                "summary": f"No capabilities mapped for {category.replace('_', ' ')}.",
            })
            continue
        avg = sum(r.get("verification_coverage_pct", 0) for r in rows) / len(rows)
        verified = sum(1 for r in rows if r.get("verified") in ("partial", "mostly", "full"))
        status = "verified" if avg >= 75 else "partial" if avg >= 45 else "gaps"
        audits.append({
            "category": category,
            "status": status,
            "coverage_pct": round(avg, 1),
            "capabilities_audited": len(rows),
            "verified_count": verified,
            "summary": f"{category.replace('_', ' ').title()}: {round(avg)}% verification coverage ({verified}/{len(rows)} verified).",
        })

    return {
        "audit_categories": audits,
        "total_categories": len(AUDIT_CATEGORIES),
        "categories_with_gaps": sum(1 for a in audits if a["status"] in ("gaps", "not_audited")),
        "summary": "Full operational audit — no capability implicitly trusted.",
    }
