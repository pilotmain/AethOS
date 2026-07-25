# SPDX-License-Identifier: Apache-2.0
"""FIX 138 — build governed rerun plan from replay + evidence bundle (no execution)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.job_replay.job_replay_deep_link import resolve_step_index
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from aethos_core.mission_control.rerun_planning.rerun_plan_contract import (
    MUTATION_PERFORMED_FIX_138,
    RERUN_EXECUTION_ENABLED_FIX_138,
    RERUN_PLAN_FIX,
    RERUN_PLAN_INVARIANT,
    RERUN_PLAN_PHRASE_TEMPLATE,
    RERUN_PLAN_SCHEMA_VERSION,
)
from aethos_core.software_delivery.software_delivery_phase_2_contract import (
    SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES,
    SOFTWARE_DELIVERY_FROZEN_INVARIANTS,
    SOFTWARE_DELIVERY_LOOP_ORDER,
)


@dataclass(frozen=True)
class RerunPlanResult:
    ok: bool
    session_id: str
    plan: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


_GATE_STAGE_MAP: dict[str, str] = {
    "planning_approved": "implementation_plan",
    "branch_create": "implementation_branch",
    "implementation_branch_created": "implementation_branch",
    "patch_proposal_approved": "patch_proposal",
    "workspace_apply": "workspace_apply",
    "workspace_verification": "workspace_verify",
    "github_preflight_approved": "github_pr_preflight",
    "branch_push_completed": "branch_push",
    "github_pr_opened": "pr_open",
}


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _resolve_target_step(
    *,
    replay: dict[str, Any],
    from_step: int | None,
    link_key: str | None,
) -> tuple[int | None, dict[str, Any] | None]:
    steps = list(replay.get("steps") or [])
    if not steps:
        return None, None
    link_index = dict(replay.get("link_index") or {})
    if link_key:
        idx = resolve_step_index(steps=steps, link_index=link_index, link=link_key.strip())
        if idx is not None:
            return idx, steps[idx]
    if from_step is not None and 0 <= from_step < len(steps):
        return from_step, steps[from_step]
    return len(steps) - 1, steps[-1]


def _infer_gate_from_step(step: dict[str, Any]) -> str:
    action = str(step.get("action") or "").lower()
    for gate in _GATE_STAGE_MAP:
        if gate in action:
            return gate
    if action.startswith("ui_approval:"):
        return action.split(":", 1)[-1]
    return action.split()[0] if action else "unknown"


def _dependencies_for_gate(gate_id: str) -> list[dict[str, str]]:
    stage = _GATE_STAGE_MAP.get(gate_id, "")
    if not stage or stage not in SOFTWARE_DELIVERY_LOOP_ORDER:
        return [{"kind": "session", "detail": "active chat session and plan_id"}]
    idx = SOFTWARE_DELIVERY_LOOP_ORDER.index(stage)
    prior = SOFTWARE_DELIVERY_LOOP_ORDER[:idx]
    return [
        {"kind": "software_delivery_stage", "stage": s, "detail": f"prior stage must be satisfied: {s}"}
        for s in prior
    ]


def _stale_state_analysis(
    *,
    bundle: dict[str, Any],
    target_step: dict[str, Any],
    final_state: dict[str, Any],
) -> dict[str, Any]:
    signals: list[dict[str, str]] = []
    before = target_step.get("state_before") or {}
    if str(before.get("plan_status")) != str(final_state.get("plan_status")):
        signals.append(
            {
                "signal": "plan_status_changed",
                "detail": f"{before.get('plan_status')} → {final_state.get('plan_status')}",
            }
        )
    before_gates = set(before.get("gates_passed") or [])
    after_gates = set(final_state.get("gates_passed") or [])
    if after_gates - before_gates:
        signals.append(
            {
                "signal": "gates_advanced_since_step",
                "detail": ", ".join(sorted(after_gates - before_gates)),
            }
        )
    exported = bundle.get("exported_at")
    if exported:
        signals.append({"signal": "bundle_point_in_time", "detail": f"evidence exported_at={exported}"})
    return {
        "is_stale": len(signals) > 0,
        "signals": signals,
        "recommendation": "Re-run governed rerun plan after new activity before assuming replay-derived targets.",
    }


def _blast_radius(*, gate_id: str, bundle: dict[str, Any]) -> dict[str, Any]:
    inbox_items = ((bundle.get("approvals") or {}).get("pending_inbox") or {}).get("items") or []
    for item in inbox_items:
        if str(item.get("gate_id") or "") == gate_id:
            return {
                "gate_id": gate_id,
                "risk_tier": item.get("risk_tier", "medium"),
                "blast_radius": item.get("blast_radius") or {},
                "unlocks": item.get("unlocks") or [],
                "remains_forbidden": item.get("remains_forbidden") or [],
            }
    return {
        "gate_id": gate_id,
        "risk_tier": "medium",
        "blast_radius": {
            "scope": "software_delivery_session",
            "workspace": "governed workspace tree only until certified push/open stages",
            "github": "no direct mutation from Mission Control",
            "infrastructure": "separate lane — not coupled",
        },
        "unlocks": ["hypothetical re-execution of downstream governed stages if rerun were enabled"],
        "remains_forbidden": list(SOFTWARE_DELIVERY_FORBIDDEN_CAPABILITIES[:6]),
    }


def _required_approvals(*, gate_id: str, bundle: dict[str, Any]) -> list[dict[str, Any]]:
    approvals: list[dict[str, Any]] = []
    inbox_items = ((bundle.get("approvals") or {}).get("pending_inbox") or {}).get("items") or []
    for item in inbox_items:
        approvals.append(
            {
                "gate_id": item.get("gate_id"),
                "severity": item.get("severity"),
                "ui_eligible": item.get("ui_approval_eligible", False),
                "execution_mode": item.get("execution_mode", "chat"),
            }
        )
    if not approvals and gate_id:
        approvals.append(
            {
                "gate_id": gate_id,
                "severity": "high",
                "ui_eligible": gate_id
                in {
                    "planning_approved",
                    "branch_create",
                    "patch_proposal_approved",
                    "workspace_apply",
                    "github_preflight_approved",
                },
                "execution_mode": "chat",
            }
        )
    return approvals


def _rerun_blockers(
    *,
    bundle: dict[str, Any],
    stale: dict[str, Any],
    gate_id: str,
) -> list[dict[str, str]]:
    blockers: list[dict[str, str]] = [
        {
            "code": "rerun_execution_disabled",
            "detail": "FIX 138 is planning-only — no rerun execution path exists",
        }
    ]
    for row in bundle.get("blockers") or []:
        blockers.append(
            {
                "code": str(row.get("source") or "attention"),
                "detail": str(row.get("detail") or row.get("gate") or ""),
            }
        )
    inc = bundle.get("incident_links") or {}
    if int(inc.get("open_incidents") or 0) > 0:
        blockers.append(
            {
                "code": "open_incident",
                "detail": f"{inc.get('open_incidents')} open incident(s) — resolve before hypothetical rerun",
            }
        )
    if stale.get("is_stale"):
        blockers.append(
            {
                "code": "stale_replay_state",
                "detail": "Mission state advanced since target step — replan from fresh evidence",
            }
        )
    if gate_id in {"branch_push_completed", "github_pr_opened"}:
        blockers.append(
            {
                "code": "coupled_mutation_stage",
                "detail": f"{gate_id} is coupled mutation — chat-only even when execution ships",
            }
        )
    return blockers


def _mutation_preview(*, gate_id: str) -> dict[str, Any]:
    stage = _GATE_STAGE_MAP.get(gate_id, "unknown")
    hypothetical: list[str] = []
    if stage in SOFTWARE_DELIVERY_LOOP_ORDER:
        idx = SOFTWARE_DELIVERY_LOOP_ORDER.index(stage)
        hypothetical = list(SOFTWARE_DELIVERY_LOOP_ORDER[idx:])
    return {
        "execution_enabled": False,
        "mutation_performed_in_fix_138": False,
        "hypothetical_stages_if_rerun_executed_later": hypothetical,
        "forbidden_in_fix_138": [
            "rerun_execution",
            "rerun_button",
            "direct_provider_mutation",
            "deploy",
            "restart",
            "merge",
        ],
        "coupled_mutations_note": (
            "branch_push and pr_open remain chat-governed mutations per FIX 125H/I even after rerun execution exists"
        ),
    }


def _exact_rerun_phrases(*, session_id: str, gate_id: str) -> list[dict[str, str]]:
    from aethos_core.mission_control.approval_inbox.approval_phrase_templates import build_copy_phrase_text

    phrases = [
        {
            "kind": "rerun_plan",
            "phrase": RERUN_PLAN_PHRASE_TEMPLATE.format(gate_id=gate_id, session_id=session_id),
            "executable": False,
            "note": "Planning phrase only — not wired to execution in FIX 138",
        }
    ]
    if gate_id in {
        "planning_approved",
        "branch_create",
        "patch_proposal_approved",
        "workspace_apply",
        "github_preflight_approved",
    }:
        copy = build_copy_phrase_text(gate_id=gate_id, required_phrases=[])
        phrases.append(
            {
                "kind": "stage_recovery",
                "phrase": copy,
                "executable": False,
                "note": "Would be required via chat governance if operator manually recovers stage",
            }
        )
    return phrases


def _eligibility(
    *,
    blockers: list[dict[str, str]],
    stale: dict[str, Any],
    target_step: dict[str, Any] | None,
) -> dict[str, Any]:
    hard = [b for b in blockers if b["code"] not in {"rerun_execution_disabled"}]
    eligible = target_step is not None and len(hard) == 0
    summary = (
        "Eligible for governed rerun **planning** — execution remains disabled (FIX 138)."
        if eligible
        else "Rerun planning available with blockers — resolve before any future rerun execution fix."
    )
    if stale.get("is_stale"):
        summary += " Evidence is stale relative to target step."
    return {
        "eligible_for_planning": eligible,
        "eligible_for_execution": False,
        "summary": summary,
    }


def build_governed_rerun_plan(
    *,
    session_id: str,
    job_id: str | None = None,
    from_step: int | None = None,
    link_key: str | None = None,
) -> RerunPlanResult:
    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None

    bundle_result = build_evidence_bundle(session_id=sid, job_id=focus)
    if not bundle_result.ok:
        return RerunPlanResult(
            ok=False,
            session_id=sid,
            blockers=list(bundle_result.blockers or ["evidence_bundle_unavailable"]),
            detail=bundle_result.detail,
        )

    replay_result = build_job_replay(session_id=sid, job_id=focus)
    if not replay_result.ok:
        return RerunPlanResult(
            ok=False,
            session_id=sid,
            blockers=list(replay_result.blockers or ["replay_unavailable"]),
            detail=replay_result.detail,
        )

    bundle = bundle_result.bundle
    replay = replay_result.replay
    step_index, target_step = _resolve_target_step(
        replay=replay, from_step=from_step, link_key=link_key
    )
    final_state = replay.get("final_state") or {}
    gate_id = _infer_gate_from_step(target_step or {})
    stale = _stale_state_analysis(bundle=bundle, target_step=target_step or {}, final_state=final_state)
    blockers = _rerun_blockers(bundle=bundle, stale=stale, gate_id=gate_id)
    eligibility = _eligibility(blockers=blockers, stale=stale, target_step=target_step)

    plan: dict[str, Any] = {
        "schema_version": RERUN_PLAN_SCHEMA_VERSION,
        "fix": RERUN_PLAN_FIX,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_138,
        "rerun_execution_enabled": RERUN_EXECUTION_ENABLED_FIX_138,
        "invariant": RERUN_PLAN_INVARIANT,
        "session_id": sid,
        "job_id": focus,
        "plan_id": (bundle.get("mission") or {}).get("plan_id"),
        "correlation_id": (bundle.get("mission") or {}).get("correlation_id"),
        "generated_at": _exported_at(),
        "eligibility": eligibility,
        "replay_derived_plan": {
            "source_fix": "FIX 137",
            "target_step_index": step_index,
            "target_step_id": (target_step or {}).get("step_id"),
            "target_link_key": (target_step or {}).get("link_key"),
            "target_action": (target_step or {}).get("action"),
            "target_lane": (target_step or {}).get("lane"),
            "would_replay_from": gate_id,
            "step_count": replay.get("step_count"),
        },
        "blast_radius": _blast_radius(gate_id=gate_id, bundle=bundle),
        "dependencies": _dependencies_for_gate(gate_id),
        "stale_state": stale,
        "rollback_posture": {
            "workspace_rollback": "governed workspace rollback available per FIX 125D (chat phrase)",
            "autonomous_rollback": "forbidden",
            "snapshot_required": "mandatory per phase 2 freeze",
            "invariants": list(SOFTWARE_DELIVERY_FROZEN_INVARIANTS[:4]),
        },
        "required_approvals": _required_approvals(gate_id=gate_id, bundle=bundle),
        "rerun_blockers": blockers,
        "mutation_preview": _mutation_preview(gate_id=gate_id),
        "exact_rerun_phrases": _exact_rerun_phrases(session_id=sid, gate_id=gate_id),
        "architecture_boundary": bundle.get("architecture_boundary"),
    }
    return RerunPlanResult(
        ok=True,
        session_id=sid,
        plan=plan,
        detail="Governed rerun plan generated (planning only — no execution).",
    )
