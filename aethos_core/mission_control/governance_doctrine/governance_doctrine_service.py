# SPDX-License-Identifier: Apache-2.0
"""FIX 151 — institutional governance doctrine from topology + charter records."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_doctrine.governance_doctrine_contract import (
    AMENDMENT_PROPOSAL_EXECUTABLE,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
    AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
    CONSTITUTIONAL_REFERENCES,
    DOCTRINE_VERSION_BASE,
    GOVERNANCE_DOCTRINE_FIX,
    GOVERNANCE_DOCTRINE_INVARIANT,
    GOVERNANCE_DOCTRINE_SCHEMA_VERSION,
    GOVERNANCE_MUTATION_PERFORMED_FIX_151,
    GOVERNANCE_PRINCIPLES,
    MUTATION_PERFORMED_FIX_151,
    SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151,
)
from aethos_core.mission_control.governance_doctrine.governance_doctrine_store import (
    list_governance_doctrine_records,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
    SEPARATION_OF_DUTY_POLICIES,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_service import (
    build_governance_role_architecture,
)


@dataclass(frozen=True)
class GovernanceDoctrineResult:
    ok: bool
    session_id: str
    doctrine: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _governance_charter_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    charters = _by_kind(records, "governance_charter")
    if not charters:
        return [
            {
                "charter_id": "default_constitutional_charter",
                "title": "AethOS Institutional Governance Charter",
                "content": (
                    "Human authority primacy; deliberation memory does not grant execution; "
                    "review delegation allowed, execution delegation forbidden."
                ),
                "source": "FIX_151_default",
                "read_only": True,
            }
        ]
    return [{**c, "read_only": True} for c in charters]


def _doctrine_versioning(*, records: list[dict[str, Any]]) -> dict[str, Any]:
    versions = _by_kind(records, "doctrine_version")
    current = DOCTRINE_VERSION_BASE
    if versions:
        current = str(versions[-1].get("content") or current)
    return {
        "base_version": DOCTRINE_VERSION_BASE,
        "current_version": current,
        "version_records": len(versions),
        "recorded_versions": [v.get("content") for v in versions[-5:]],
        "autonomous_evolution": False,
        "read_only": True,
    }


def _policy_rationale_history(*, records: list[dict[str, Any]], architecture: dict[str, Any]) -> list[dict[str, Any]]:
    history = [{**r, "read_only": True} for r in _by_kind(records, "policy_rationale")]
    for policy in (architecture.get("sections") or {}).get("separation_of_duty_policies") or []:
        history.append(
            {
                "kind": "topology_derived_rationale",
                "policy": policy.get("policy"),
                "rationale": "Enforced via FIX 150 governance role architecture.",
                "read_only": True,
            }
        )
    return history[:20]


def _governance_principle_registry() -> list[dict[str, Any]]:
    return [
        {"principle_id": pid, "statement": stmt, "constitutional": True, "read_only": True}
        for pid, stmt in GOVERNANCE_PRINCIPLES
    ]


def _institutional_rule_lineage(*, architecture: dict[str, Any]) -> list[dict[str, Any]]:
    lineage: list[dict[str, Any]] = []
    for idx, policy in enumerate(SEPARATION_OF_DUTY_POLICIES):
        lineage.append(
            {
                "rule_id": f"sod-{idx + 1}",
                "rule": policy,
                "origin_fix": "FIX 150",
                "lineage_depth": 1,
                "read_only": True,
            }
        )
    for boundary in (architecture.get("sections") or {}).get("governance_delegation_boundaries") or []:
        lineage.append(
            {
                "rule_id": f"delegation-{boundary.get('delegation_type')}",
                "rule": boundary.get("detail"),
                "allowed": boundary.get("allowed"),
                "origin_fix": "FIX 150",
                "read_only": True,
            }
        )
    return lineage


def _policy_amendment_proposals(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            **r,
            "executable": AMENDMENT_PROPOSAL_EXECUTABLE,
            "status": "proposed",
            "requires_human_ratification": True,
            "read_only": True,
        }
        for r in _by_kind(records, "policy_amendment_proposal")
    ]


def _governance_precedent_tracking(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{**r, "precedent_weight": "institutional", "read_only": True} for r in _by_kind(records, "governance_precedent")]


def _doctrine_conflict_detection(*, records: list[dict[str, Any]], architecture: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    amendments = _by_kind(records, "policy_amendment_proposal")
    for amendment in amendments:
        text = str(amendment.get("content") or "").lower()
        if "auto approve" in text or "autonomous" in text or "self-modify" in text:
            conflicts.append(
                {
                    "conflict_id": f"conflict-{amendment.get('record_id')}",
                    "amendment_record_id": amendment.get("record_id"),
                    "conflict": "amendment_conflicts_with_constitutional_principles",
                    "detail": "Proposal language suggests autonomous or auto-approval behavior — constitutionally incompatible.",
                    "severity": "high",
                    "read_only": True,
                }
            )

    delegation = (architecture.get("sections") or {}).get("governance_delegation_boundaries") or []
    if any(d.get("delegation_type") == "delegated_execution_authority" and d.get("allowed") for d in delegation):
        conflicts.append(
            {
                "conflict_id": "topology-delegation-conflict",
                "conflict": "topology_would_allow_execution_delegation",
                "detail": "Unexpected execution delegation in topology — review required.",
                "severity": "critical",
                "read_only": True,
            }
        )

    if not conflicts:
        conflicts.append(
            {
                "conflict_id": "none-detected",
                "conflict": "no_doctrine_conflicts_detected",
                "detail": "No amendment or topology conflicts against constitutional principles.",
                "severity": "none",
                "read_only": True,
            }
        )
    return conflicts


def _policy_freeze_snapshots(*, architecture: dict[str, Any], records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    snapshots = [{**r, "read_only": True} for r in _by_kind(records, "policy_freeze_snapshot")]
    snapshots.append(
        {
            "snapshot_id": "topology-freeze-implicit",
            "kind": "implicit_topology_snapshot",
            "fix": architecture.get("fix"),
            "schema_version": architecture.get("schema_version"),
            "trust_zones": architecture.get("trust_zones"),
            "exported_at": architecture.get("exported_at"),
            "read_only": True,
        }
    )
    return snapshots


def _constitutional_governance_references(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = [
        {"fix": fix, "reference": ref, "constitutional": True, "read_only": True}
        for fix, ref in CONSTITUTIONAL_REFERENCES
    ]
    refs.extend({**r, "read_only": True} for r in _by_kind(records, "constitutional_reference"))
    return refs


def build_governance_doctrine(*, session_id: str) -> GovernanceDoctrineResult:
    sid = (session_id or "default").strip()[:64] or "default"

    architecture_result = build_governance_role_architecture(session_id=sid)
    architecture = architecture_result.architecture if architecture_result.ok else {}
    plan_id = str(architecture.get("plan_id") or "") or None
    correlation_id = str(architecture.get("correlation_id") or "") or None

    records = list_governance_doctrine_records(session_id=sid, plan_id=plan_id)

    sections = {
        "governance_charter_records": _governance_charter_records(records),
        "doctrine_versioning": _doctrine_versioning(records=records),
        "policy_rationale_history": _policy_rationale_history(records=records, architecture=architecture),
        "governance_principle_registry": _governance_principle_registry(),
        "institutional_rule_lineage": _institutional_rule_lineage(architecture=architecture),
        "policy_amendment_proposals": _policy_amendment_proposals(records),
        "governance_precedent_tracking": _governance_precedent_tracking(records),
        "doctrine_conflict_detection": _doctrine_conflict_detection(records=records, architecture=architecture),
        "policy_freeze_snapshots": _policy_freeze_snapshots(architecture=architecture, records=records),
        "constitutional_governance_references": _constitutional_governance_references(records=records),
    }

    doctrine: dict[str, Any] = {
        "schema_version": GOVERNANCE_DOCTRINE_SCHEMA_VERSION,
        "fix": GOVERNANCE_DOCTRINE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_151,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_151,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_151,
        "autonomous_doctrine_evolution_enabled": AUTONOMOUS_DOCTRINE_EVOLUTION_ENABLED_FIX_151,
        "self_modifying_governance_enabled": SELF_MODIFYING_GOVERNANCE_ENABLED_FIX_151,
        "invariant": GOVERNANCE_DOCTRINE_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "amendment_proposal_count": len(sections["policy_amendment_proposals"]),
        "all_amendments_executable": False,
        "institutional_governance_constitutionality": True,
        "sources": {
            "governance_role_architecture": architecture_result.ok,
            "doctrine_records": len(records),
        },
    }
    return GovernanceDoctrineResult(
        ok=True,
        session_id=sid,
        doctrine=doctrine,
        detail="Governance doctrine assembled (amendment proposals only — no autonomous policy mutation).",
    )
