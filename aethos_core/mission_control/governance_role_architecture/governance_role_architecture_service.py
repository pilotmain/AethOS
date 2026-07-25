# SPDX-License-Identifier: Apache-2.0
"""FIX 150 — institutional governance role topology from collaboration + trust contracts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.governance_collaboration.governance_collaboration_service import (
    build_governance_collaboration_workspace,
)
from aethos_core.mission_control.governance_role_architecture.governance_role_architecture_contract import (
    AUTOMATIC_APPROVAL_ENABLED_FIX_150,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150,
    AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
    DEFAULT_ADVISORY_QUORUM_SIZE,
    DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
    ESCALATION_PATHS,
    GOVERNANCE_MUTATION_PERFORMED_FIX_150,
    GOVERNANCE_ROLE_ARCHITECTURE_FIX,
    GOVERNANCE_ROLE_ARCHITECTURE_INVARIANT,
    GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION,
    GOVERNANCE_ROLE_TAXONOMY,
    MUTATION_PERFORMED_FIX_150,
    QUORUM_ROLE_COMPOSITION,
    SEPARATION_OF_DUTY_POLICIES,
    TRUST_ZONES,
)


@dataclass(frozen=True)
class GovernanceRoleArchitectureResult:
    ok: bool
    session_id: str
    architecture: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _governance_role_taxonomy(*, collaboration: dict[str, Any]) -> list[dict[str, Any]]:
    observed: dict[str, set[str]] = {role: set() for role in GOVERNANCE_ROLE_TAXONOMY}
    for reviewer in (collaboration.get("sections") or {}).get("named_reviewers") or []:
        role = str(reviewer.get("reviewer_role") or "observer")
        name = str(reviewer.get("reviewer_name") or "")
        if role in observed and name:
            observed[role].add(name)

    taxonomy: list[dict[str, Any]] = []
    for role in GOVERNANCE_ROLE_TAXONOMY:
        taxonomy.append(
            {
                "role": role,
                "observed_operators": sorted(observed.get(role, set())),
                "observed_count": len(observed.get(role, set())),
                "institutional_role": True,
                "read_only": True,
            }
        )
    return taxonomy


def _trust_boundary_modeling() -> list[dict[str, Any]]:
    boundaries = [
        ("observability", "deliberation_memory", "read_only_cognition_to_memory"),
        ("deliberation_memory", "collaboration_memory", "single_to_multi_operator"),
        ("collaboration_memory", "readiness_advisory", "memory_to_advisory"),
        ("readiness_advisory", "chat_governed_approval", "advisory_to_human_approval"),
        ("chat_governed_approval", "execution_substrate", "approval_to_execution"),
    ]
    return [
        {
            "from_zone": src,
            "to_zone": dst,
            "boundary": label,
            "crossing_requires_human_authority": dst in {"chat_governed_approval", "execution_substrate"},
            "automatic_crossing_allowed": False,
            "read_only": True,
        }
        for src, dst, label in boundaries
    ]


def _role_capability_matrix() -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    capabilities = {
        "primary_reviewer": {
            "can": ["view_readiness", "record_deliberation", "request_secondary_review", "acknowledge_review"],
            "cannot": ["auto_approve", "auto_deploy", "elevate_role", "mutate_policy"],
        },
        "secondary_reviewer": {
            "can": ["view_readiness", "record_dissent", "acknowledge_review"],
            "cannot": ["auto_approve", "bypass_primary", "execute_mutation"],
        },
        "observer": {
            "can": ["view_mission_control", "record_notes"],
            "cannot": ["approve", "execute", "assign_authority"],
        },
        "escalation_owner": {
            "can": ["view_incidents", "coordinate_escalation", "record_concerns"],
            "cannot": ["auto_resolve_incident", "auto_promote"],
        },
        "mission_owner": {
            "can": ["view_full_stack", "authorize_chat_governance_phrases"],
            "cannot": ["bypass_governance", "autonomous_execution"],
        },
        "approval_operator": {
            "can": ["ui_approval_to_chat", "governed_phrase_approval"],
            "cannot": ["direct_provider_mutation", "bypass_audit"],
        },
        "execution_operator": {
            "can": ["execute_after_explicit_approval"],
            "cannot": ["autonomous_rollout", "self_elevate"],
        },
    }
    for role, caps in capabilities.items():
        matrix.append({"role": role, **caps, "read_only": True})
    return matrix


def _escalation_path_definitions(*, collaboration: dict[str, Any]) -> list[dict[str, Any]]:
    paths: list[dict[str, Any]] = []
    for src, dst in ESCALATION_PATHS:
        paths.append(
            {
                "from_role": src,
                "to_role": dst,
                "kind": "institutional_default",
                "automatic_escalation": False,
                "read_only": True,
            }
        )
    for rec in (collaboration.get("sections") or {}).get("unresolved_concern_escalation") or []:
        paths.append(
            {
                "from_role": rec.get("reviewer_role") or "unknown",
                "to_role": "escalation_owner",
                "kind": "recorded_escalation",
                "content": rec.get("content"),
                "recorded_at": rec.get("recorded_at"),
                "automatic_escalation": False,
                "read_only": True,
            }
        )
    return paths


def _separation_of_duty_policies() -> list[dict[str, Any]]:
    return [
        {"policy": policy, "enforced": True, "automation_override": False, "read_only": True}
        for policy in SEPARATION_OF_DUTY_POLICIES
    ]


def _review_authority_scopes() -> list[dict[str, Any]]:
    return [
        {
            "role": "primary_reviewer",
            "scope": "readiness_review_advisory",
            "authority_type": "recommendation_only",
            "executable": False,
            "read_only": True,
        },
        {
            "role": "approval_operator",
            "scope": "chat_governed_gate_approval",
            "authority_type": "human_governed",
            "executable": True,
            "requires_chat_phrase": True,
            "read_only": True,
        },
        {
            "role": "execution_operator",
            "scope": "post_approval_execution_substrate",
            "authority_type": "explicit_human_only",
            "executable": True,
            "requires_prior_approval": True,
            "read_only": True,
        },
    ]


def _quorum_role_composition_rules(*, collaboration: dict[str, Any]) -> dict[str, Any]:
    quorum = (collaboration.get("sections") or {}).get("quorum_aware_discussion") or {}
    return {
        "required_roles": list(QUORUM_ROLE_COMPOSITION),
        "advisory_quorum_size": DEFAULT_ADVISORY_QUORUM_SIZE,
        "current_acknowledgments": quorum.get("unique_reviewers_acknowledged", 0),
        "quorum_advisory_met": quorum.get("quorum_advisory_met", False),
        "automatic_quorum_approval": False,
        "composition_rules": [
            "At least one primary_reviewer acknowledgment recommended.",
            "Secondary reviewer provides separation-of-duty counterweight.",
            "Quorum advisory never triggers auto-approval.",
        ],
        "read_only": True,
    }


def _governance_delegation_boundaries() -> list[dict[str, Any]]:
    return [
        {
            "delegation_type": "delegated_review_request",
            "allowed": True,
            "grants_execution_authority": False,
            "detail": "FIX 149 review handoff — memory only.",
            "read_only": True,
        },
        {
            "delegation_type": "delegated_execution_authority",
            "allowed": False,
            "grants_execution_authority": False,
            "detail": "Always forbidden — human chat governance required.",
            "read_only": True,
        },
        {
            "delegation_type": "autonomous_role_elevation",
            "allowed": False,
            "grants_execution_authority": False,
            "detail": "Roles are observed, never auto-elevated.",
            "read_only": True,
        },
    ]


def _operator_trust_zones(*, collaboration: dict[str, Any]) -> list[dict[str, Any]]:
    zones: list[dict[str, Any]] = []
    for reviewer in (collaboration.get("sections") or {}).get("named_reviewers") or []:
        role = str(reviewer.get("reviewer_role") or "observer")
        zone = "collaboration_memory"
        if role in {"primary_reviewer", "secondary_reviewer"}:
            zone = "readiness_advisory"
        elif role == "escalation_owner":
            zone = "observability"
        zones.append(
            {
                "operator": reviewer.get("reviewer_name"),
                "role": role,
                "trust_zone": zone,
                "max_authority": "recommendation_only" if role != "mission_owner" else "chat_governed",
                "read_only": True,
            }
        )
    if not zones:
        zones.append(
            {
                "operator": None,
                "role": "observer",
                "trust_zone": "observability",
                "max_authority": "read_only",
                "detail": "No named reviewers recorded — default observer topology.",
                "read_only": True,
            }
        )
    return zones


def _institutional_responsibility_maps(*, collaboration: dict[str, Any]) -> list[dict[str, Any]]:
    maps: list[dict[str, Any]] = []
    for rec in (collaboration.get("sections") or {}).get("review_ownership") or []:
        maps.append(
            {
                "responsible_party": rec.get("owner") or rec.get("reviewer_name"),
                "responsibility": rec.get("content"),
                "kind": "review_ownership",
                "read_only": True,
            }
        )
    for rec in (collaboration.get("sections") or {}).get("reviewer_assignments") or []:
        maps.append(
            {
                "responsible_party": rec.get("reviewer_name"),
                "responsibility": rec.get("content"),
                "role": rec.get("reviewer_role"),
                "kind": "reviewer_assignment",
                "read_only": True,
            }
        )
    if not maps:
        maps.append(
            {
                "responsible_party": "mission_owner",
                "responsibility": "Ultimate governance authority via chat-governed approvals.",
                "kind": "institutional_default",
                "read_only": True,
            }
        )
    return maps


def build_governance_role_architecture(*, session_id: str) -> GovernanceRoleArchitectureResult:
    sid = (session_id or "default").strip()[:64] or "default"

    collaboration_result = build_governance_collaboration_workspace(session_id=sid)
    collaboration = collaboration_result.collaboration if collaboration_result.ok else {}

    sections = {
        "governance_role_taxonomy": _governance_role_taxonomy(collaboration=collaboration),
        "trust_boundary_modeling": _trust_boundary_modeling(),
        "role_capability_matrix": _role_capability_matrix(),
        "escalation_path_definitions": _escalation_path_definitions(collaboration=collaboration),
        "separation_of_duty_policies": _separation_of_duty_policies(),
        "review_authority_scopes": _review_authority_scopes(),
        "quorum_role_composition_rules": _quorum_role_composition_rules(collaboration=collaboration),
        "governance_delegation_boundaries": _governance_delegation_boundaries(),
        "operator_trust_zones": _operator_trust_zones(collaboration=collaboration),
        "institutional_responsibility_maps": _institutional_responsibility_maps(collaboration=collaboration),
    }

    architecture: dict[str, Any] = {
        "schema_version": GOVERNANCE_ROLE_ARCHITECTURE_SCHEMA_VERSION,
        "fix": GOVERNANCE_ROLE_ARCHITECTURE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_150,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_150,
        "delegated_execution_authority_enabled": DELEGATED_EXECUTION_AUTHORITY_ENABLED_FIX_150,
        "automatic_approval_enabled": AUTOMATIC_APPROVAL_ENABLED_FIX_150,
        "autonomous_role_elevation_enabled": AUTONOMOUS_ROLE_ELEVATION_ENABLED_FIX_150,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_150,
        "invariant": GOVERNANCE_ROLE_ARCHITECTURE_INVARIANT,
        "session_id": sid,
        "plan_id": collaboration.get("plan_id"),
        "correlation_id": collaboration.get("correlation_id"),
        "trust_zones": list(TRUST_ZONES),
        "sections": sections,
        "institutional_governance_topology": True,
        "sources": {
            "governance_collaboration": collaboration_result.ok,
            "named_reviewers": len((collaboration.get("sections") or {}).get("named_reviewers") or []),
        },
    }
    return GovernanceRoleArchitectureResult(
        ok=True,
        session_id=sid,
        architecture=architecture,
        detail="Governance role architecture assembled (read-only institutional topology).",
    )
