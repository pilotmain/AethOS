# SPDX-License-Identifier: Apache-2.0
"""FIX 137 — build read-only mission/job replay from evidence bundle data."""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.job_replay.job_replay_contract import (
    JOB_REPLAY_DEEP_LINK_FIX,
    JOB_REPLAY_FIX,
    JOB_REPLAY_SCHEMA_VERSION,
    JOB_REPLAY_SOURCE_FIX,
    MUTATION_PERFORMED_FIX_137,
)
from aethos_core.mission_control.job_replay.job_replay_deep_link import (
    build_link_index,
    link_key_from_candidate,
    link_refs_from_candidate,
    resolve_step_index,
)


@dataclass(frozen=True)
class JobReplayResult:
    ok: bool
    session_id: str
    replay: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _parse_timestamp(value: Any) -> float:
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return 0.0


def _drilldown_section(bundle: dict[str, Any], lane: str, section_id: str) -> dict[str, Any] | None:
    lane_payload = (bundle.get("lane_drilldowns") or {}).get(lane) or {}
    for section in lane_payload.get("sections") or []:
        if section.get("section_id") == section_id:
            return section
    return None


def _initial_mission_state(bundle: dict[str, Any]) -> dict[str, Any]:
    mission = bundle.get("mission") or {}
    sd = ((bundle.get("snapshot") or {}).get("lanes") or {}).get("software_delivery") or {}
    gates_section = _drilldown_section(bundle, "software_delivery", "governance_gates")
    gate_items = list((gates_section or {}).get("items") or [])
    passed = [str(g.get("gate") or g.get("label") or "") for g in gate_items if g.get("passed")]
    pending = list(sd.get("pending_gates") or [])
    return {
        "plan_id": mission.get("plan_id") or sd.get("plan_id"),
        "plan_status": sd.get("plan_status") or "unknown",
        "correlation_id": mission.get("correlation_id"),
        "gates_passed": passed,
        "pending_gates": pending,
        "open_blockers": len(bundle.get("blockers") or []),
        "jobs_tracked": len(bundle.get("jobs") or []),
    }


def _apply_action_to_state(state: dict[str, Any], *, action: str, detail: str = "") -> dict[str, Any]:
    after = copy.deepcopy(state)
    action_l = action.lower()
    detail_l = detail.lower()
    gate_hints = (
        "planning_approved",
        "branch_create",
        "implementation_branch_created",
        "patch_proposal_approved",
        "workspace_apply",
        "workspace_verification",
        "github_preflight",
        "branch_push",
        "github_pr_open",
        "pr_draft",
    )
    for hint in gate_hints:
        if hint in action_l or hint in detail_l:
            if hint not in after["gates_passed"]:
                after["gates_passed"] = list(after["gates_passed"]) + [hint]
            after["pending_gates"] = [g for g in after.get("pending_gates") or [] if hint not in str(g)]
    if "planning_approved" in action_l:
        after["plan_status"] = "planning_approved"
    if "pr_draft" in action_l or "pr_open" in action_l:
        after["plan_status"] = action
    if "job_completed" in action_l or "job_failed" in action_l:
        after["last_job_event"] = action
    return after


def _collect_step_candidates(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []

    timeline_section = _drilldown_section(bundle, "software_delivery", "timeline")
    for item in list((timeline_section or {}).get("items") or []):
        if not isinstance(item, dict):
            continue
        candidates.append(
            {
                "source": "software_delivery_timeline",
                "lane": "software_delivery",
                "timestamp": item.get("recorded_at") or item.get("timestamp"),
                "action": item.get("action") or "",
                "detail": item.get("detail") or "",
                "actor": item.get("actor"),
                "mutation_performed": item.get("mutation_performed", False),
                "event_id": item.get("event_id"),
            }
        )

    for entry in bundle.get("timeline") or []:
        if not isinstance(entry, dict):
            continue
        candidates.append(
            {
                "source": "cross_lane_timeline",
                "lane": entry.get("lane") or "unknown",
                "timestamp": entry.get("timestamp"),
                "action": entry.get("action") or "",
                "detail": entry.get("detail") or "",
                "job_id": entry.get("job_id"),
            }
        )

    audits = ((bundle.get("approvals") or {}).get("ui_audit") or {}).get("audits") or []
    for audit in audits:
        if not isinstance(audit, dict):
            continue
        candidates.append(
            {
                "source": "ui_approval_audit",
                "lane": audit.get("lane") or "approval",
                "timestamp": audit.get("recorded_at"),
                "action": f"ui_approval:{audit.get('gate_id') or 'unknown'}",
                "detail": audit.get("outcome") or audit.get("reply_excerpt") or "",
                "gate_id": audit.get("gate_id"),
                "approval_id": audit.get("approval_id"),
                "mutation_performed": audit.get("mutation_performed", False),
            }
        )

    for job in bundle.get("jobs") or []:
        if not isinstance(job, dict):
            continue
        candidates.append(
            {
                "source": "tracked_job",
                "lane": "tracked_jobs",
                "timestamp": datetime.fromtimestamp(float(job.get("created_at") or 0), UTC).isoformat()
                if job.get("created_at")
                else "",
                "action": f"job_{job.get('status') or 'queued'}",
                "detail": job.get("title") or job.get("job_type") or "",
                "job_id": job.get("id"),
                "job_type": job.get("job_type"),
            }
        )

    candidates.sort(key=lambda row: _parse_timestamp(row.get("timestamp")))
    return candidates


def _match_receipts(*, step: dict[str, Any], receipts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action = str(step.get("action") or "").lower()
    detail = str(step.get("detail") or "").lower()
    matched: list[dict[str, Any]] = []
    for receipt in receipts:
        phase = str(receipt.get("phase") or "").lower()
        rec_detail = str(receipt.get("detail") or "").lower()
        if phase and phase in action:
            matched.append(receipt)
            continue
        if phase and phase in detail:
            matched.append(receipt)
            continue
        if action and action.split(":")[-1] in rec_detail:
            matched.append(receipt)
    return matched[:6]


def _match_blockers(*, state_before: dict[str, Any], bundle_blockers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pending = set(str(g) for g in state_before.get("pending_gates") or [])
    matched: list[dict[str, Any]] = []
    for blocker in bundle_blockers:
        gate = str(blocker.get("gate") or blocker.get("gate_id") or "")
        if gate and gate in pending:
            matched.append(blocker)
        elif blocker.get("source") == "execution_health":
            matched.append(blocker)
    return matched


def _match_approvals(*, step: dict[str, Any], gates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    action = str(step.get("action") or "").lower()
    matched: list[dict[str, Any]] = []
    for gate in gates:
        gate_name = str(gate.get("gate") or "")
        if gate_name and gate_name.lower() in action:
            matched.append(gate)
    if step.get("gate_id"):
        matched.append({"gate": step.get("gate_id"), "source": "ui_approval_audit", "approved": True})
    return matched


def _build_replay_steps(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    receipts = list(bundle.get("receipts") or [])
    bundle_blockers = list(bundle.get("blockers") or [])
    gates_section = _drilldown_section(bundle, "software_delivery", "governance_gates")
    gate_items = list((gates_section or {}).get("items") or [])
    approvals_section = _drilldown_section(bundle, "software_delivery", "approvals")
    approval_items = list((approvals_section or {}).get("items") or [])

    state = _initial_mission_state(bundle)
    steps: list[dict[str, Any]] = []
    candidates = _collect_step_candidates(bundle)

    if not candidates:
        start = {
            "step_index": 0,
            "step_id": "replay-start",
            "link_key": "rpl-mission-start",
            "link_refs": {"mission": "mission:start"},
            "source": "replay",
            "lane": "mission",
            "timestamp": bundle.get("exported_at"),
            "action": "mission_snapshot",
            "detail": "No timeline events yet — showing current mission state only.",
            "state_before": state,
            "state_after": copy.deepcopy(state),
            "receipts": receipts[:3],
            "gates": gate_items,
            "blockers": bundle_blockers,
            "approvals": approval_items,
        }
        steps.append(start)
        return steps

    for index, candidate in enumerate(candidates):
        state_before = copy.deepcopy(state)
        state_after = _apply_action_to_state(
            state,
            action=str(candidate.get("action") or ""),
            detail=str(candidate.get("detail") or ""),
        )
        state = state_after
        step = {
            "step_index": index,
            "step_id": f"replay-{index:03d}",
            "link_key": link_key_from_candidate(candidate),
            "link_refs": link_refs_from_candidate(candidate),
            "source": candidate.get("source"),
            "lane": candidate.get("lane"),
            "timestamp": candidate.get("timestamp"),
            "action": candidate.get("action"),
            "detail": candidate.get("detail"),
            "job_id": candidate.get("job_id"),
            "mutation_performed": candidate.get("mutation_performed", False),
            "state_before": state_before,
            "state_after": state_after,
            "receipts": _match_receipts(step=candidate, receipts=receipts),
            "gates": gate_items,
            "blockers": _match_blockers(state_before=state_before, bundle_blockers=bundle_blockers),
            "approvals": _match_approvals(step=candidate, gates=approval_items),
        }
        steps.append(step)
    return steps


def build_job_replay(*, session_id: str, job_id: str | None = None) -> JobReplayResult:
    sid = (session_id or "default").strip()[:64] or "default"
    focus = (job_id or "").strip() or None

    bundle_result = build_evidence_bundle(session_id=sid, job_id=focus)
    if not bundle_result.ok:
        return JobReplayResult(
            ok=False,
            session_id=sid,
            blockers=list(bundle_result.blockers or ["evidence_bundle_unavailable"]),
            detail=bundle_result.detail or "evidence_bundle_unavailable",
        )

    bundle = bundle_result.bundle
    steps = _build_replay_steps(bundle)
    link_index = build_link_index(steps)
    replay = {
        "schema_version": JOB_REPLAY_SCHEMA_VERSION,
        "fix": JOB_REPLAY_FIX,
        "deep_link_fix": JOB_REPLAY_DEEP_LINK_FIX,
        "source_fix": JOB_REPLAY_SOURCE_FIX,
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_137,
        "session_id": sid,
        "job_id": focus,
        "mission": bundle.get("mission") or {},
        "exported_at": bundle.get("exported_at"),
        "step_count": len(steps),
        "steps": steps,
        "link_index": link_index,
        "final_state": steps[-1]["state_after"] if steps else _initial_mission_state(bundle),
        "architecture_boundary": bundle.get("architecture_boundary"),
    }
    return JobReplayResult(
        ok=True,
        session_id=sid,
        replay=replay,
        detail="Job replay assembled from evidence bundle (read-only).",
    )


def resolve_job_replay_link(
    *,
    session_id: str,
    link: str,
    job_id: str | None = None,
) -> dict[str, Any]:
    """Resolve a deep link key or alias to a replay step index (read-only)."""
    needle = (link or "").strip()
    if not needle:
        return {"ok": False, "blockers": ["missing_link"]}

    result = build_job_replay(session_id=session_id, job_id=job_id)
    if not result.ok:
        return {"ok": False, "blockers": result.blockers, "detail": result.detail}

    steps = list(result.replay.get("steps") or [])
    link_index = dict(result.replay.get("link_index") or {})
    step_index = resolve_step_index(steps=steps, link_index=link_index, link=needle)
    if step_index is None:
        return {
            "ok": False,
            "blockers": ["link_not_found"],
            "link": needle,
            "session_id": session_id,
        }
    step = steps[step_index]
    return {
        "ok": True,
        "read_only": True,
        "mutation_performed": False,
        "deep_link_fix": JOB_REPLAY_DEEP_LINK_FIX,
        "session_id": session_id,
        "job_id": job_id,
        "link": needle,
        "step_index": step_index,
        "step_id": step.get("step_id"),
        "link_key": step.get("link_key"),
    }
