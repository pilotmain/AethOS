# SPDX-License-Identifier: Apache-2.0
"""FIX 171 — bounded execution participation service (envelope-scoped agent coordination)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.governance.governance_friction_approval_contract import FIX_171_CERTIFICATION_REQUIREMENTS
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_contract import (
    ALLOWED_PARTICIPATION_LANES,
    AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
    AUTONOMOUS_APPROVAL_ENABLED_FIX_171,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
    AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
    BOUNDED_EXECUTION_PARTICIPATION_FIX,
    BOUNDED_EXECUTION_PARTICIPATION_INVARIANT,
    BOUNDED_EXECUTION_PARTICIPATION_PRINCIPLES,
    BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION,
    FORBIDDEN_PARTICIPATION_ACTIONS,
    FORBIDDEN_PARTICIPATION_LANES,
    GATE_BYPASS_ENABLED_FIX_171,
    GOVERNANCE_MUTATION_PERFORMED_FIX_171,
    MERGE_DEPLOY_ENABLED_FIX_171,
    MUTATION_PERFORMED_FIX_171,
    PARTICIPATION_TIER,
    PR_OPEN_ENABLED_FIX_171,
    RAILWAY_MUTATION_ENABLED_FIX_171,
    TIER_ESCALATION_ENABLED_FIX_171,
)
from aethos_core.mission_control.bounded_execution_participation.bounded_execution_participation_store import (
    list_bounded_execution_participation_records,
)
from aethos_core.mission_control.bounded_multi_agent_delivery_work_packages.bounded_multi_agent_delivery_work_packages_service import (
    build_bounded_delivery_work_packages,
)
from aethos_core.mission_control.mission_authorization.mission_authorization_service import build_mission_authorization


@dataclass(frozen=True)
class BoundedExecutionParticipationResult:
    ok: bool
    session_id: str
    bounded_execution_participation: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _by_kind(records: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [r for r in records if str(r.get("kind") or "") == kind]


def _sections(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("sections") or {}


def _authorization_envelope(mission_authorization: dict[str, Any]) -> dict[str, Any]:
    envelopes = _sections(mission_authorization).get("bounded_work_envelope") or []
    for row in reversed(envelopes):
        if row.get("envelope_id") == "bounded-work-envelope":
            return row
    return {}


def _authorization_envelope_read(*, mission_authorization: dict[str, Any]) -> list[dict[str, Any]]:
    envelope = _authorization_envelope(mission_authorization)
    if not envelope:
        return [
            {
                "read_id": "pending-mission-authorization",
                "detail": "No FIX 170 mission authorization envelope — participation blocked until authorization granted.",
                "participation_ready": False,
                "read_only": True,
            }
        ]
    return [
        {
            "read_id": "authorized-envelope-read",
            "selected_path": envelope.get("selected_path"),
            "allowed_lanes": envelope.get("allowed_lanes") or [],
            "authorization_tier": envelope.get("authorization_tier"),
            "authorization_granted": envelope.get("authorization_granted"),
            "gate_bypass": envelope.get("gate_bypass", False),
            "participation_ready": bool(envelope.get("authorization_granted")),
            "read_only": True,
        }
    ]


def _participation_scope(
    *,
    mission_authorization: dict[str, Any],
    work_packages: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "participation_artifact")]
    envelope = _authorization_envelope(mission_authorization)
    if not envelope.get("authorization_granted"):
        return stored + [
            {
                "scope_id": "no-participation-scope",
                "detail": "Participation scope unavailable without authorized Tier 1–2 envelope.",
                "participation_ready": False,
                "read_only": True,
            }
        ]

    allowed_lanes = [lane for lane in (envelope.get("allowed_lanes") or []) if lane in ALLOWED_PARTICIPATION_LANES]
    package_rows = (_sections(work_packages).get("role_scoped_work_packages") or [])[:4]
    scopes: list[dict[str, Any]] = [
        {
            "scope_id": "envelope-participation-scope",
            "allowed_lanes": allowed_lanes,
            "forbidden_lanes": list(FORBIDDEN_PARTICIPATION_LANES),
            "participation_tier": PARTICIPATION_TIER,
            "autonomous_lane_entry": False,
            "execution_authority": False,
            "agent_participation_within_envelope": True,
            "detail": "Agents may participate inside authorized Tier 1–2 envelope only.",
            "read_only": True,
        }
    ]
    for idx, pkg in enumerate(package_rows, start=1):
        scopes.append(
            {
                "scope_id": f"work-package-{idx}",
                "package_id": pkg.get("package_id"),
                "lane": pkg.get("lane") or "software_delivery",
                "agent_participation_within_envelope": True,
                "autonomous_lane_entry": False,
                "read_only": True,
            }
        )
    return stored + scopes


def _gate_routed_participation(
    *,
    mission_authorization: dict[str, Any],
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "gate_routed_action_note")]
    gate_rows = _sections(mission_authorization).get("existing_gate_checks") or []
    routed: list[dict[str, Any]] = list(stored)
    for row in gate_rows[:6]:
        routed.append(
            {
                "participation_action_id": row.get("gate_check_id") or row.get("validation_id"),
                "status": row.get("status") or "enforced",
                "gate_bypass": False,
                "approval_bypass": False,
                "passes_existing_gates": True,
                "detail": row.get("detail") or "Every participation action routes through existing gates.",
                "read_only": True,
            }
        )
    if not routed:
        routed.append(
            {
                "participation_action_id": "gate-routed-participation-default",
                "gate_bypass": False,
                "approval_bypass": False,
                "passes_existing_gates": True,
                "detail": "Participation never bypasses existing gate checks.",
                "read_only": True,
            }
        )
    return routed


def _tier_boundary_enforcement() -> list[dict[str, Any]]:
    return [
        {
            "boundary_id": "tier-1-2-participation-only",
            "participation_tier": PARTICIPATION_TIER,
            "tier_3_4_satisfied": False,
            "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_171,
            "detail": "Tier 1–2 participation never performs Tier 3–4 actions.",
            "read_only": True,
        },
        {
            "boundary_id": "cert-requirements-bound",
            "requirement_count": len(FIX_171_CERTIFICATION_REQUIREMENTS),
            "all_cert_requirements_acknowledged": True,
            "read_only": True,
        },
    ]


def _forbidden_participation_actions(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "forbidden_participation_note")]
    catalog = [
        {"action_id": aid, "detail": detail, "executable": False, "read_only": True}
        for aid, detail in FORBIDDEN_PARTICIPATION_ACTIONS
    ]
    return stored + catalog


def _reengagement_triggers(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stored = [{**r, "read_only": True} for r in _by_kind(records, "reengagement_note")]
    return stored + [
        {
            "trigger_id": "scope-expansion",
            "reengagement_required": True,
            "autonomous_expansion": False,
            "detail": "Human re-engagement when participation scope expands beyond envelope.",
            "read_only": True,
        },
        {
            "trigger_id": "lane-escalation",
            "reengagement_required": True,
            "detail": "Human re-engagement when Railway or production participation is requested.",
            "read_only": True,
        },
        {
            "trigger_id": "tier-escalation",
            "reengagement_required": True,
            "detail": "Human re-engagement when Tier 3–4 action would be required.",
            "read_only": True,
        },
        {
            "trigger_id": "merge-deploy-request",
            "reengagement_required": True,
            "detail": "Human re-engagement when merge or deploy is requested.",
            "read_only": True,
        },
        {
            "trigger_id": "not-required-bounded-stage",
            "reengagement_required": False,
            "detail": "Bounded agent stage completion within envelope does not require re-engagement.",
            "read_only": True,
        },
    ]


def _next_step_participation_sequence(
    *,
    participation_ready: bool,
    allowed_lanes: list[str],
) -> list[dict[str, Any]]:
    if not participation_ready:
        return [
            {
                "step": 1,
                "command_hint": "mission authorization — grant bounded Tier 1–2 envelope before participation",
                "autonomous_lane_entry": False,
                "read_only": True,
            }
        ]
    steps: list[dict[str, Any]] = [
        {
            "step": 1,
            "command_hint": "participation artifact: <agent scope within envelope> — persist participation record",
            "autonomous_lane_entry": False,
            "read_only": True,
        },
        {
            "step": 2,
            "command_hint": "agents participate inside authorized envelope — every action passes existing gates",
            "autonomous_lane_entry": False,
            "read_only": True,
        },
    ]
    for idx, lane in enumerate(allowed_lanes[:3], start=3):
        steps.append(
            {
                "step": idx,
                "command_hint": f"coordinate agent work in `{lane}` — gate-routed, no autonomous lane entry",
                "lane": lane,
                "gate_bypass": False,
                "read_only": True,
            }
        )
    return steps


def _participation_integrity_scoring(
    *,
    records: list[dict[str, Any]],
    participation_ready: bool,
    allowed_lanes: list[str],
) -> list[dict[str, Any]]:
    score = 25 + (35 if participation_ready else 0) + min(len(allowed_lanes) * 8, 24)
    if _by_kind(records, "participation_artifact"):
        score += 10
    score = min(100, score)
    label = "participating" if score >= 80 else "partial" if score >= 50 else "blocked"
    return [
        {
            "score_id": "bounded-execution-participation-integrity",
            "integrity_score": score,
            "integrity_label": label,
            "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
            "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_171,
            "execution_authority": False,
            "detail": "Participation integrity — envelope-scoped coordination without authority expansion.",
            "read_only": True,
        }
    ]


def build_bounded_execution_participation(*, session_id: str) -> BoundedExecutionParticipationResult:
    sid = (session_id or "default").strip()[:64] or "default"

    auth_result = build_mission_authorization(session_id=sid)
    mission_authorization = auth_result.mission_authorization if auth_result.ok else {}
    packages_result = build_bounded_delivery_work_packages(session_id=sid)
    work_packages = packages_result.bounded_delivery_work_packages if packages_result.ok else {}

    plan_id = str(mission_authorization.get("plan_id") or work_packages.get("plan_id") or "") or None
    correlation_id = (
        str(mission_authorization.get("correlation_id") or work_packages.get("correlation_id") or "") or None
    )

    records = list_bounded_execution_participation_records(session_id=sid, plan_id=plan_id)
    envelope = _authorization_envelope(mission_authorization)
    allowed_lanes = [str(lane) for lane in (envelope.get("allowed_lanes") or [])]
    participation_ready = bool(envelope.get("authorization_granted"))

    sections = {
        "authorization_envelope_read": _authorization_envelope_read(mission_authorization=mission_authorization),
        "participation_scope": _participation_scope(
            mission_authorization=mission_authorization,
            work_packages=work_packages,
            records=records,
        ),
        "gate_routed_participation": _gate_routed_participation(
            mission_authorization=mission_authorization,
            records=records,
        ),
        "tier_boundary_enforcement": _tier_boundary_enforcement(),
        "forbidden_participation_actions": _forbidden_participation_actions(records=records),
        "reengagement_triggers": _reengagement_triggers(records=records),
        "next_step_participation_sequence": _next_step_participation_sequence(
            participation_ready=participation_ready,
            allowed_lanes=allowed_lanes,
        ),
        "participation_integrity_scoring": _participation_integrity_scoring(
            records=records,
            participation_ready=participation_ready,
            allowed_lanes=allowed_lanes,
        ),
    }

    bounded_execution_participation: dict[str, Any] = {
        "schema_version": BOUNDED_EXECUTION_PARTICIPATION_SCHEMA_VERSION,
        "fix": BOUNDED_EXECUTION_PARTICIPATION_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_171,
        "governance_mutation_performed": GOVERNANCE_MUTATION_PERFORMED_FIX_171,
        "automatic_policy_mutation_enabled": AUTOMATIC_POLICY_MUTATION_ENABLED_FIX_171,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_171,
        "autonomous_lane_entry_enabled": AUTONOMOUS_LANE_ENTRY_ENABLED_FIX_171,
        "autonomous_approval_enabled": AUTONOMOUS_APPROVAL_ENABLED_FIX_171,
        "tier_escalation_enabled": TIER_ESCALATION_ENABLED_FIX_171,
        "gate_bypass_enabled": GATE_BYPASS_ENABLED_FIX_171,
        "pr_open_enabled": PR_OPEN_ENABLED_FIX_171,
        "merge_deploy_enabled": MERGE_DEPLOY_ENABLED_FIX_171,
        "railway_mutation_enabled": RAILWAY_MUTATION_ENABLED_FIX_171,
        "invariant": BOUNDED_EXECUTION_PARTICIPATION_INVARIANT,
        "session_id": sid,
        "plan_id": plan_id,
        "correlation_id": correlation_id,
        "sections": sections,
        "participation_record_count": len(records),
        "selected_path_id": mission_authorization.get("selected_path_id"),
        "allowed_lane_count": len(allowed_lanes),
        "participation_tier": PARTICIPATION_TIER if participation_ready else None,
        "participation_ready": participation_ready,
        "fix_171_certification_requirements": list(FIX_171_CERTIFICATION_REQUIREMENTS),
        "all_recommendations_executable": False,
        "bounded_execution_participation_cognition": True,
        "envelope_scoped_participation_only": True,
        "bounded_execution_participation_principles": [
            {"principle_id": pid, "statement": stmt, "read_only": True}
            for pid, stmt in BOUNDED_EXECUTION_PARTICIPATION_PRINCIPLES
        ],
        "sources": {
            "mission_authorization": auth_result.ok,
            "bounded_delivery_work_packages": packages_result.ok,
            "authorization_granted": participation_ready,
            "participation_records": len(records),
        },
    }
    return BoundedExecutionParticipationResult(
        ok=True,
        session_id=sid,
        bounded_execution_participation=bounded_execution_participation,
        detail="Bounded execution participation assembled (envelope-scoped — existing gates remain enforced).",
    )
