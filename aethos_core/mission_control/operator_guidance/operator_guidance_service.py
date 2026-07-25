# SPDX-License-Identifier: Apache-2.0
"""FIX 142 — contextual operator guidance from semantic intelligence + governance state."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.approval_inbox.approval_inbox_service import approval_inbox_payload
from aethos_core.mission_control.cross_lane.snapshot_service import build_mission_control_snapshot
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from aethos_core.mission_control.knowledge_spaces.knowledge_spaces_service import search_mission_knowledge_spaces
from aethos_core.mission_control.operator_guidance.operator_guidance_contract import (
    AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
    AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
    OPERATOR_APPROVAL_REQUIRED,
    OPERATOR_GUIDANCE_FIX,
    OPERATOR_GUIDANCE_INVARIANT,
    OPERATOR_GUIDANCE_SCHEMA_VERSION,
    MUTATION_PERFORMED_FIX_142,
    RECOMMENDATION_EXECUTABLE,
)
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan
from aethos_core.software_delivery.software_delivery_phase_2_contract import SOFTWARE_DELIVERY_LOOP_ORDER


@dataclass(frozen=True)
class OperatorGuidanceResult:
    ok: bool
    session_id: str
    guidance: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _rec(
    *,
    kind: str,
    guidance: str,
    rationale: str = "",
    suggested_phrase: str = "",
    priority: str = "medium",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "guidance": guidance,
        "rationale": rationale,
        "suggested_phrase": suggested_phrase,
        "priority": priority,
        "executable": RECOMMENDATION_EXECUTABLE,
        "operator_approval_required": OPERATOR_APPROVAL_REQUIRED,
        "read_only": True,
        **extra,
    }


def _gate_to_stage(gate_id: str) -> str | None:
    mapping = {
        "planning_approved": "implementation_plan",
        "branch_create": "implementation_branch",
        "patch_proposal_approved": "patch_proposal",
        "workspace_apply": "workspace_apply",
        "github_preflight_approved": "github_pr_preflight",
        "branch_push_completed": "branch_push",
        "github_pr_opened": "pr_open",
    }
    return mapping.get(gate_id)


def _likely_next_governed_steps(
    *,
    snapshot: dict[str, Any],
    inbox: dict[str, Any],
) -> list[dict[str, Any]]:
    steps: list[dict[str, Any]] = []
    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    pending_gates = list(sd.get("pending_gates") or [])

    for item in inbox.get("items") or []:
        if not item.get("ui_approval_eligible"):
            continue
        gate = str(item.get("gate_id") or "")
        phrase = (item.get("copy_phrase_text") or (item.get("required_phrases") or [""])[0] or "")
        steps.append(
            _rec(
                kind="next_governed_step",
                guidance=f"Consider governed approval for gate `{gate}` via chat (UI approval routes to chat governance).",
                rationale=f"Inbox item `{item.get('inbox_id')}` is pending with severity {item.get('severity', 'unknown')}.",
                suggested_phrase=str(phrase)[:200] if phrase else "",
                priority="high" if item.get("severity") in {"critical", "high"} else "medium",
                gate_id=gate,
                inbox_id=item.get("inbox_id"),
            )
        )

    for gate in pending_gates:
        if any(s.get("gate_id") == gate for s in steps):
            continue
        stage = _gate_to_stage(gate) or gate
        steps.append(
            _rec(
                kind="next_governed_step",
                guidance=f"Software delivery stage `{stage}` may need operator attention — review lane drilldown before proceeding.",
                rationale=f"Pending gate `{gate}` observed in snapshot.",
                priority="medium",
                gate_id=gate,
            )
        )

    if not steps:
        steps.append(
            _rec(
                kind="next_governed_step",
                guidance="No pending UI-eligible gates — review cross-lane snapshot and evidence bundle for drift.",
                rationale="Approval inbox empty or view-only.",
                priority="low",
            )
        )
    return steps[:8]


def _historical_mitigations(*, knowledge: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen = knowledge.get("seen_before") or {}
    if seen.get("likely_seen_before"):
        for match in seen.get("top_matches") or []:
            out.append(
                _rec(
                    kind="historical_mitigation",
                    guidance=(
                        f"Prior operational context exists for `{match.get('category')}` — "
                        "review cross-session memory before repeating the same governed path."
                    ),
                    rationale=f"Semantic match score {match.get('relevance_score')} in space `{match.get('space_id')}`.",
                    priority="medium",
                    reference_session=match.get("session_id"),
                )
            )
    for rec in knowledge.get("recommendations") or []:
        if rec.get("kind") == "historical_context":
            out.append(
                _rec(
                    kind="historical_mitigation",
                    guidance=str(rec.get("recommendation") or ""),
                    rationale="Derived from FIX 141 knowledge space recall.",
                    priority="medium",
                )
            )
    return out[:6]


def _recurring_blocker_resolutions(*, graph: dict[str, Any], knowledge: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for b in graph.get("recurring_blockers") or []:
        blocker = str(b.get("blocker") or "")
        n = int(b.get("occurrences") or 0)
        out.append(
            _rec(
                kind="recurring_blocker_resolution",
                guidance=(
                    f"Recurring blocker `{blocker[:80]}` (×{n}) — resolve via approval inbox or clear forbidden capability "
                    "before advancing delivery."
                ),
                rationale="Observed in session operational graph (FIX 139).",
                priority="high" if n >= 2 else "medium",
                blocker=blocker,
            )
        )
    for hit in knowledge.get("search_results") or []:
        if hit.get("category") != "blocker":
            continue
        out.append(
            _rec(
                kind="recurring_blocker_resolution",
                guidance=f"Knowledge space match: {str(hit.get('text', ''))[:120]}",
                rationale=f"Semantic relevance {hit.get('relevance_score')}.",
                priority="medium",
            )
        )
    return out[:8]


def _relevant_incidents_prs(*, snapshot: dict[str, Any], knowledge: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    inc = snapshot.get("incident_linkage") or {}
    if int(inc.get("open_incidents") or 0) > 0:
        out.append(
            _rec(
                kind="relevant_incident",
                guidance=(
                    f"{inc.get('open_incidents')} open production incident(s) — pause promotion thinking; "
                    "review incident command lane and rollout visibility."
                ),
                rationale=f"Latest incident id: {inc.get('latest_incident_id', 'unknown')}.",
                priority="critical",
            )
        )
    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    if sd.get("pr_url") or sd.get("pr_number"):
        out.append(
            _rec(
                kind="relevant_pr",
                guidance="Active PR context in software delivery — verify human_review gate before merge assumptions.",
                rationale=f"PR: {sd.get('pr_url') or sd.get('pr_number')}",
                priority="medium",
            )
        )
    for hit in knowledge.get("search_results") or []:
        cat = str(hit.get("category") or "")
        if cat in {"incident", "pr"}:
            out.append(
                _rec(
                    kind=f"relevant_{cat}",
                    guidance=str(hit.get("text", ""))[:140],
                    rationale=f"Semantic match in organizational memory.",
                    priority="high" if cat == "incident" else "medium",
                )
            )
    return out[:8]


def _rollout_caution(*, snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    pg = snapshot.get("rollout_visibility") or ((snapshot.get("lanes") or {}).get("production_governance") or {})
    stage = str(pg.get("latest_rollout_stage") or "")
    records = int(pg.get("rollout_records") or 0)
    inc_open = int((snapshot.get("incident_linkage") or {}).get("open_incidents") or 0)

    if inc_open > 0:
        level = "halt_promotion_thinking"
    elif stage and stage.lower() not in {"stable", "complete", "verified", ""}:
        level = "elevated_caution"
    elif records > 0:
        level = "standard_governed_caution"
    else:
        level = "baseline"

    out.append(
        _rec(
            kind="rollout_caution",
            guidance=f"Rollout caution level: **{level}** — production governance lane remains separate from software delivery.",
            rationale=f"rollout_records={records} latest_stage={stage or 'n/a'} open_incidents={inc_open}",
            priority="critical" if level == "halt_promotion_thinking" else "medium",
            caution_level=level,
        )
    )
    return out


def _verification_gaps(*, graph: dict[str, Any], snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    ver_nodes = [
        n
        for n in ((graph.get("graph") or {}).get("nodes") or [])
        if n.get("kind") == "verification"
    ]
    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    plan_status = str(sd.get("plan_status") or "")

    if not ver_nodes and plan_status not in {"", "unknown", "planning"}:
        out.append(
            _rec(
                kind="verification_gap",
                guidance="No verification evidence indexed in operational graph — run workspace_verify stage review.",
                rationale="Missing verification nodes while delivery plan is active.",
                priority="high",
            )
        )
    for node in ver_nodes:
        out.append(
            _rec(
                kind="verification_gap",
                guidance="Verification evidence present — confirm workspace_verify gate cleared before PR operations.",
                rationale=str(node.get("key", "")),
                priority="medium",
            )
        )
    return out[:4]


def _approval_sequencing(*, inbox: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    items = list(inbox.get("items") or [])
    if not items:
        return [
            _rec(
                kind="approval_sequencing",
                guidance="No pending approvals — sequencing is N/A; monitor attention queue.",
                rationale="Empty approval inbox.",
                priority="low",
            )
        ]

    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    ordered = sorted(
        items,
        key=lambda i: (
            severity_rank.get(str(i.get("severity") or "medium"), 2),
            str(i.get("gate_id") or ""),
        ),
    )
    sequence = [str(i.get("gate_id") or i.get("inbox_id")) for i in ordered]
    out.append(
        _rec(
            kind="approval_sequencing",
            guidance=f"Suggested approval order (operator discretion): {' → '.join(sequence[:6])}.",
            rationale="Ordered by severity then gate_id; each step still requires explicit governed approval.",
            priority="high",
            sequence=sequence,
        )
    )
    return out


def _replay_rerun_review_targets(
    *,
    replay: dict[str, Any] | None,
    rerun_plan: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if replay:
        steps = list(replay.get("steps") or [])
        if steps:
            last = steps[-1]
            out.append(
                _rec(
                    kind="replay_review_target",
                    guidance=(
                        f"Review job replay from step {last.get('step_index')} "
                        f"(`{last.get('action', '')}`) — use deep links for audit alignment."
                    ),
                    rationale="Latest replay step from FIX 137.",
                    suggested_phrase="show mission control timeline",
                    priority="medium",
                    link_key=last.get("link_key"),
                )
            )
    if rerun_plan:
        rp = rerun_plan.get("replay_derived_plan") or {}
        out.append(
            _rec(
                kind="rerun_review_target",
                guidance=(
                    "Review governed rerun plan (FIX 138 planning only) before any future rerun execution fix — "
                    f"target gate `{rp.get('would_replay_from', 'unknown')}`."
                ),
                rationale="Rerun execution remains disabled.",
                suggested_phrase="show governed rerun plan",
                priority="medium",
                target_step_index=rp.get("target_step_index"),
            )
        )
        for b in (rerun_plan.get("rerun_blockers") or [])[:3]:
            out.append(
                _rec(
                    kind="rerun_review_target",
                    guidance=f"Rerun blocker to understand: {b.get('code')} — {b.get('detail', '')}",
                    rationale="From governed rerun plan.",
                    priority="low",
                )
            )
    if not out:
        out.append(
            _rec(
                kind="replay_review_target",
                guidance="Build evidence bundle and job replay when investigating regressions.",
                rationale="No replay/rerun artifacts in current session scope.",
                priority="low",
            )
        )
    return out


def build_operator_contextual_guidance(
    *,
    session_id: str,
    focus: str | None = None,
) -> OperatorGuidanceResult:
    sid = (session_id or "default").strip()[:64] or "default"
    focus_text = (focus or "").strip()

    snap_result = build_mission_control_snapshot(session_id=sid)
    if not snap_result.ok or not snap_result.snapshot:
        return OperatorGuidanceResult(
            ok=False,
            session_id=sid,
            blockers=list(snap_result.blockers or ["snapshot_unavailable"]),
            detail=snap_result.detail or "snapshot_unavailable",
        )

    snapshot = snap_result.snapshot
    inbox = approval_inbox_payload(session_id=sid)
    graph_result = build_operational_memory_graph(session_id=sid)
    graph = graph_result.graph if graph_result.ok else {}

    query_parts = [focus_text] if focus_text else []
    sd = ((snapshot.get("lanes") or {}).get("software_delivery") or {})
    if sd.get("pending_gates"):
        query_parts.append(" ".join(str(g) for g in sd.get("pending_gates") or []))
    query_parts.extend(["blocker", "approval", "incident", "verification"])
    knowledge_result = search_mission_knowledge_spaces(
        session_id=sid,
        query=" ".join(query_parts),
        ingest_current=True,
    )
    knowledge = knowledge_result.payload if knowledge_result.ok else {}

    replay_result = build_job_replay(session_id=sid)
    replay = replay_result.replay if replay_result.ok else None

    rerun_result = build_governed_rerun_plan(session_id=sid)
    rerun_plan = rerun_result.plan if rerun_result.ok else None

    sections = {
        "likely_next_governed_steps": _likely_next_governed_steps(snapshot=snapshot, inbox=inbox),
        "historical_mitigations": _historical_mitigations(knowledge=knowledge),
        "recurring_blocker_resolutions": _recurring_blocker_resolutions(graph=graph, knowledge=knowledge),
        "relevant_incidents_and_prs": _relevant_incidents_prs(snapshot=snapshot, knowledge=knowledge),
        "rollout_caution": _rollout_caution(snapshot=snapshot),
        "verification_gaps": _verification_gaps(graph=graph, snapshot=snapshot),
        "approval_sequencing": _approval_sequencing(inbox=inbox),
        "replay_and_rerun_review_targets": _replay_rerun_review_targets(replay=replay, rerun_plan=rerun_plan),
    }

    all_recs: list[dict[str, Any]] = []
    for items in sections.values():
        all_recs.extend(items)

    guidance: dict[str, Any] = {
        "schema_version": OPERATOR_GUIDANCE_SCHEMA_VERSION,
        "fix": OPERATOR_GUIDANCE_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_142,
        "autonomous_execution_enabled": AUTONOMOUS_EXECUTION_ENABLED_FIX_142,
        "automatic_mutation_planning_enabled": AUTOMATIC_MUTATION_PLANNING_ENABLED_FIX_142,
        "invariant": OPERATOR_GUIDANCE_INVARIANT,
        "session_id": sid,
        "focus": focus_text or None,
        "correlation_id": snapshot.get("correlation_id"),
        "plan_id": snapshot.get("plan_id"),
        "delivery_loop_order": list(SOFTWARE_DELIVERY_LOOP_ORDER),
        "sections": sections,
        "recommendation_count": len(all_recs),
        "all_recommendations_executable": False,
        "operator_approval_required_for_all": True,
        "sources": {
            "snapshot": True,
            "approval_inbox": True,
            "operational_memory": graph_result.ok,
            "knowledge_spaces": knowledge_result.ok,
            "job_replay": replay is not None,
            "rerun_plan": rerun_plan is not None,
        },
    }
    return OperatorGuidanceResult(
        ok=True,
        session_id=sid,
        guidance=guidance,
        detail="Operator contextual guidance built (recommendation-only copiloting).",
    )
