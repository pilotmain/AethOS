# SPDX-License-Identifier: Apache-2.0
"""FIX 139 — build read-only operational memory graph from evidence + replay + rerun plan."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from aethos_core.mission_control.evidence_bundle.evidence_bundle_service import build_evidence_bundle
from aethos_core.mission_control.job_replay.job_replay_service import build_job_replay
from aethos_core.mission_control.operational_memory.operational_memory_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
    MUTATION_PERFORMED_FIX_139,
    OPERATIONAL_MEMORY_EDGE_KINDS,
    OPERATIONAL_MEMORY_FIX,
    OPERATIONAL_MEMORY_INVARIANT,
    OPERATIONAL_MEMORY_NODE_KINDS,
    OPERATIONAL_MEMORY_SCHEMA_VERSION,
)
from aethos_core.mission_control.rerun_planning.rerun_plan_service import build_governed_rerun_plan


@dataclass(frozen=True)
class OperationalMemoryResult:
    ok: bool
    session_id: str
    graph: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _node_id(kind: str, key: str) -> str:
    return f"{kind}:{key}"


def _add_node(nodes: dict[str, dict[str, Any]], *, kind: str, key: str, **attrs: Any) -> str:
    nid = _node_id(kind, key)
    if nid not in nodes:
        nodes[nid] = {"id": nid, "kind": kind, "key": key, **attrs}
    else:
        nodes[nid].update({k: v for k, v in attrs.items() if v is not None})
    return nid


def _add_edge(edges: list[dict[str, Any]], *, kind: str, source: str, target: str, **attrs: Any) -> None:
    edges.append({"kind": kind, "source": source, "target": target, **attrs})


def _build_nodes_and_edges(
    *,
    bundle: dict[str, Any],
    replay: dict[str, Any] | None,
    rerun_plan: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, Any]] = []

    mission = bundle.get("mission") or {}
    sid = str(bundle.get("session_id") or mission.get("session_id") or "default")
    plan_id = str(mission.get("plan_id") or "")
    correlation_id = str(mission.get("correlation_id") or "")

    mission_nid = _add_node(
        nodes,
        kind="mission",
        key=correlation_id or sid,
        session_id=sid,
        plan_id=plan_id or None,
        correlation_id=correlation_id,
        snapshot_id=mission.get("snapshot_id"),
    )

    if plan_id:
        plan_nid = _add_node(nodes, kind="mission", key=f"plan:{plan_id}", plan_id=plan_id, session_id=sid)
        _add_edge(edges, kind="plan_governs", source=plan_nid, target=mission_nid, plan_id=plan_id)

    for job in bundle.get("jobs") or []:
        jid = str(job.get("id") or "")
        if not jid:
            continue
        job_nid = _add_node(
            nodes,
            kind="job",
            key=jid,
            status=job.get("status"),
            operation=job.get("operation"),
            provider=job.get("provider"),
        )
        _add_edge(edges, kind="session_contains", source=mission_nid, target=job_nid)
        _add_edge(edges, kind="job_in_session", source=job_nid, target=mission_nid, session_id=sid)

    pending = (bundle.get("approvals") or {}).get("pending_inbox") or {}
    for item in pending.get("items") or []:
        inbox_id = str(item.get("inbox_id") or "")
        gate_id = str(item.get("gate_id") or "")
        if not inbox_id:
            continue
        appr_nid = _add_node(
            nodes,
            kind="approval",
            key=inbox_id,
            gate_id=gate_id,
            lane=item.get("lane"),
            state=item.get("state") or "pending",
        )
        _add_edge(edges, kind="session_contains", source=mission_nid, target=appr_nid)
        if gate_id:
            gate_nid = _add_node(nodes, kind="gate", key=gate_id, gate_id=gate_id)
            _add_edge(edges, kind="approval_for_gate", source=appr_nid, target=gate_nid, gate_id=gate_id)

    audits = (bundle.get("approvals") or {}).get("ui_audit") or {}
    for audit in audits.get("audits") or []:
        approval_id = str(audit.get("approval_id") or "")
        if not approval_id:
            continue
        audit_nid = _add_node(
            nodes,
            kind="approval",
            key=f"audit:{approval_id}",
            approval_id=approval_id,
            gate_id=audit.get("gate_id"),
            outcome=audit.get("outcome"),
            state="audited",
        )
        _add_edge(edges, kind="session_contains", source=mission_nid, target=audit_nid)
        inbox_id = str(audit.get("inbox_id") or "")
        if inbox_id:
            _add_edge(
                edges,
                kind="audit_of_approval",
                source=audit_nid,
                target=_add_node(nodes, kind="approval", key=inbox_id, gate_id=audit.get("gate_id")),
            )

    for blocker in bundle.get("blockers") or []:
        detail = str(blocker.get("detail") or blocker.get("gate") or "unknown")
        code = f"{blocker.get('source', 'blocker')}:{detail[:48]}"
        blk_nid = _add_node(
            nodes,
            kind="blocker",
            key=code,
            source=blocker.get("source"),
            lane=blocker.get("lane"),
            gate=blocker.get("gate"),
            detail=detail,
        )
        _add_edge(edges, kind="session_contains", source=mission_nid, target=blk_nid)

    inc = bundle.get("incident_links") or {}
    for i in range(int(inc.get("incident_count") or 0)):
        iid = str(inc.get("latest_incident_id") or f"incident-{i}")
        inc_nid = _add_node(
            nodes,
            kind="incident",
            key=iid,
            open=bool(inc.get("open_incidents")),
            status=inc.get("latest_status"),
        )
        _add_edge(edges, kind="incident_blocks", source=inc_nid, target=mission_nid)
        _add_edge(edges, kind="correlates_with", source=inc_nid, target=mission_nid, domain="production")

    pg_lane = ((bundle.get("snapshot") or {}).get("lanes") or {}).get("production_governance") or {}
    rollout_count = int(pg_lane.get("rollout_records") or 0)
    if rollout_count:
        roll_nid = _add_node(
            nodes,
            kind="rollout",
            key=f"rollout:{correlation_id or sid}",
            records=rollout_count,
            latest_stage=pg_lane.get("latest_rollout_stage"),
        )
        _add_edge(edges, kind="rollout_observed", source=roll_nid, target=mission_nid)
        _add_edge(edges, kind="correlates_with", source=roll_nid, target=mission_nid, domain="production_governance")

    sd = ((bundle.get("snapshot") or {}).get("lanes") or {}).get("software_delivery") or {}
    pr_url = sd.get("pr_url") or sd.get("github_pr_url")
    if pr_url or sd.get("pr_number"):
        pr_key = str(pr_url or sd.get("pr_number"))
        pr_nid = _add_node(
            nodes,
            kind="pr",
            key=pr_key,
            pr_url=pr_url,
            pr_number=sd.get("pr_number"),
            branch=sd.get("branch_name"),
        )
        _add_edge(edges, kind="lineage", source=mission_nid, target=pr_nid, stage="github_pr")
        if plan_id:
            _add_edge(
                edges,
                kind="correlates_with",
                source=pr_nid,
                target=_node_id("mission", f"plan:{plan_id}"),
                domain="software_delivery",
            )

    ver = bundle.get("verification") or {}
    if ver.get("sections"):
        ver_nid = _add_node(
            nodes,
            kind="verification",
            key=f"verification:{sid}",
            section_count=len(ver.get("sections") or []),
        )
        _add_edge(edges, kind="evidence_of", source=ver_nid, target=mission_nid)

    ma = ((bundle.get("lane_drilldowns") or {}).get("multi_agent_collaboration") or {})
    for section in ma.get("sections") or []:
        if section.get("kind") != "agent_findings":
            continue
        for idx, finding in enumerate(section.get("items") or []):
            if not isinstance(finding, dict):
                continue
            fid = str(finding.get("agent") or finding.get("role") or idx)
            f_nid = _add_node(
                nodes,
                kind="agent_finding",
                key=f"{plan_id or sid}:{fid}:{idx}",
                agent=finding.get("agent"),
                summary=(finding.get("summary") or finding.get("detail") or "")[:200],
            )
            _add_edge(edges, kind="evidence_of", source=f_nid, target=mission_nid)

    for entry in bundle.get("operation_lifecycle") or []:
        eid = str(entry.get("lifecycle_id") or entry.get("operation") or entry.get("recorded_at") or "")
        if not eid:
            continue
        lc_nid = _add_node(
            nodes,
            kind="lifecycle",
            key=eid,
            operation=entry.get("operation"),
            preflight_job_id=entry.get("preflight_job_id"),
            execution_job_id=entry.get("execution_job_id"),
        )
        _add_edge(edges, kind="lineage", source=lc_nid, target=mission_nid)
        for jid in (entry.get("preflight_job_id"), entry.get("execution_job_id")):
            if jid and _node_id("job", str(jid)) in nodes:
                _add_edge(edges, kind="correlates_with", source=lc_nid, target=_node_id("job", str(jid)))

    for receipt in bundle.get("receipts") or []:
        rid = str(receipt.get("source_file") or receipt.get("recorded_at") or receipt.get("phase") or "")
        if not rid:
            continue
        r_nid = _add_node(nodes, kind="receipt", key=rid[:80], phase=receipt.get("phase"), lane=receipt.get("lane"))
        _add_edge(edges, kind="evidence_of", source=r_nid, target=mission_nid)

    if replay:
        for step in replay.get("steps") or []:
            idx = step.get("step_index")
            link_key = str(step.get("link_key") or f"step:{idx}")
            step_nid = _add_node(
                nodes,
                kind="replay_step",
                key=link_key,
                step_index=idx,
                action=step.get("action"),
                timestamp=step.get("timestamp"),
            )
            _add_edge(edges, kind="replay_of_timeline", source=step_nid, target=mission_nid, link_key=link_key)

    if rerun_plan:
        rp_nid = _add_node(
            nodes,
            kind="rerun_plan",
            key=f"rerun_plan:{sid}",
            eligible_for_planning=(rerun_plan.get("eligibility") or {}).get("eligible_for_planning"),
            execution_enabled=False,
        )
        _add_edge(edges, kind="session_contains", source=mission_nid, target=rp_nid)
        target_link = ((rerun_plan.get("replay_derived_plan") or {}).get("target_link_key") or "")
        if target_link:
            target_nid = _node_id("replay_step", target_link)
            if target_nid in nodes:
                _add_edge(edges, kind="rerun_plan_targets", source=rp_nid, target=target_nid)

    return list(nodes.values()), edges


def _correlated_executions(
    *,
    bundle: dict[str, Any],
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = {}
    for node in nodes:
        if node.get("kind") != "job":
            continue
        op = str(node.get("operation") or "unknown")
        groups.setdefault(op, []).append(str(node.get("key")))
    correlations: list[dict[str, Any]] = []
    for op, job_ids in sorted(groups.items()):
        if len(job_ids) < 2:
            continue
        correlations.append(
            {
                "operation": op,
                "job_ids": job_ids,
                "count": len(job_ids),
                "correlation_basis": "shared_operation_in_session",
            }
        )
    lifecycle_ops = Counter(
        str(e.get("operation") or "unknown") for e in bundle.get("operation_lifecycle") or []
    )
    for op, count in lifecycle_ops.items():
        if count >= 2:
            correlations.append(
                {
                    "operation": op,
                    "lifecycle_entries": count,
                    "correlation_basis": "repeated_lifecycle_operation",
                }
            )
    return correlations


def _repeated_failures(*, bundle: dict[str, Any], replay: dict[str, Any] | None) -> list[dict[str, Any]]:
    failure_tokens = ("fail", "error", "blocked", "rejected", "denied")
    counts: Counter[str] = Counter()

    for ev in bundle.get("timeline") or []:
        action = str(ev.get("action") or "").lower()
        detail = str(ev.get("detail") or "").lower()
        if any(t in action or t in detail for t in failure_tokens):
            sig = action or detail[:60]
            counts[sig] += 1

    for job in bundle.get("jobs") or []:
        status = str(job.get("status") or "").lower()
        if status in {"failed", "error", "blocked"}:
            counts[f"job_status:{status}"] += 1

    if replay:
        for step in replay.get("steps") or []:
            after = step.get("state_after") or {}
            if int(after.get("open_blockers") or 0) > 2:
                counts["replay:elevated_blockers"] += 1

    return [
        {"signature": sig, "occurrences": n, "read_only": True}
        for sig, n in counts.most_common(12)
        if n >= 1
    ]


def _historical_blast_radius(*, rerun_plan: dict[str, Any] | None, bundle: dict[str, Any]) -> dict[str, Any]:
    if rerun_plan:
        br = rerun_plan.get("blast_radius") or {}
        return {
            "source": "rerun_plan_fix_138",
            "risk_tier": br.get("risk_tier"),
            "blast_radius": br.get("blast_radius"),
            "forbidden_capabilities": br.get("forbidden_capabilities"),
            "read_only": True,
        }
    blockers = bundle.get("blockers") or []
    return {
        "source": "evidence_bundle_blockers",
        "blocker_count": len(blockers),
        "lanes_affected": sorted({str(b.get("lane") or "unknown") for b in blockers}),
        "read_only": True,
    }


def _recurring_blockers(*, bundle: dict[str, Any], rerun_plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for b in bundle.get("blockers") or []:
        key = str(b.get("detail") or b.get("gate") or b.get("source") or "unknown")
        counts[key] += 1
    if rerun_plan:
        for b in rerun_plan.get("rerun_blockers") or []:
            counts[str(b.get("code") or "rerun_blocker")] += 1
    return [
        {"blocker": key, "occurrences": n, "read_only": True}
        for key, n in counts.most_common(15)
        if n >= 1
    ]


def _mission_lineage(
    *,
    bundle: dict[str, Any],
    nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lineage: list[dict[str, Any]] = []
    mission = bundle.get("mission") or {}
    lineage.append({"stage": "session", "id": bundle.get("session_id"), "kind": "mission"})
    if mission.get("plan_id"):
        lineage.append({"stage": "plan", "id": mission.get("plan_id"), "kind": "mission"})
    if mission.get("correlation_id"):
        lineage.append({"stage": "correlation", "id": mission.get("correlation_id"), "kind": "mission"})

    gates = [
        n for n in nodes if n.get("kind") == "gate"
    ]
    for g in sorted(gates, key=lambda x: str(x.get("key"))):
        lineage.append({"stage": "gate", "id": g.get("key"), "kind": "gate"})

    jobs = [n for n in nodes if n.get("kind") == "job"]
    for j in jobs:
        lineage.append({"stage": "job", "id": j.get("key"), "kind": "job", "status": j.get("status")})

    prs = [n for n in nodes if n.get("kind") == "pr"]
    for pr in prs:
        lineage.append({"stage": "pr", "id": pr.get("key"), "kind": "pr"})

    return lineage


def _cross_domain_links(*, nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for edge in edges:
        if edge.get("kind") not in {"correlates_with", "incident_blocks", "rollout_observed", "approval_for_gate"}:
            continue
        links.append(
            {
                "kind": edge.get("kind"),
                "source": edge.get("source"),
                "target": edge.get("target"),
                "domain": edge.get("domain"),
            }
        )
    kinds_present = {n.get("kind") for n in nodes}
    if {"incident", "pr", "approval"}.issubset(kinds_present):
        links.append(
            {
                "kind": "synthetic_correlation",
                "detail": "incident ↔ production ↔ PR ↔ approval chain observable in session",
                "read_only": True,
            }
        )
    return links[:40]


def _learning_signals(
    *,
    correlated: list[dict[str, Any]],
    failures: list[dict[str, Any]],
    recurring: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    if correlated:
        signals.append(
            {
                "signal": "correlated_executions_detected",
                "detail": f"{len(correlated)} operation group(s) with multiple related executions",
                "actionable": False,
            }
        )
    repeated = [f for f in failures if int(f.get("occurrences") or 0) >= 2]
    if repeated:
        signals.append(
            {
                "signal": "repeated_failure_pattern",
                "detail": f"{len(repeated)} failure signature(s) occurred more than once",
                "actionable": False,
            }
        )
    hot_blockers = [b for b in recurring if int(b.get("occurrences") or 0) >= 2]
    if hot_blockers:
        signals.append(
            {
                "signal": "recurring_blocker_pattern",
                "detail": f"{len(hot_blockers)} blocker(s) recur in this session scope",
                "actionable": False,
            }
        )
    if not signals:
        signals.append(
            {
                "signal": "baseline_observed",
                "detail": "Operational memory graph built; no strong recurrence patterns in current scope",
                "actionable": False,
            }
        )
    return signals


def build_operational_memory_graph(
    *,
    session_id: str,
    job_id: str | None = None,
    include_replay: bool = True,
    include_rerun_plan: bool = True,
) -> OperationalMemoryResult:
    sid = (session_id or "default").strip()[:64] or "default"
    focus_job = (job_id or "").strip() or None

    bundle_result = build_evidence_bundle(session_id=sid, job_id=focus_job)
    if not bundle_result.ok:
        return OperationalMemoryResult(
            ok=False,
            session_id=sid,
            blockers=list(bundle_result.blockers or ["evidence_bundle_unavailable"]),
            detail=bundle_result.detail or "evidence_bundle_unavailable",
        )

    bundle = bundle_result.bundle
    replay: dict[str, Any] | None = None
    if include_replay:
        replay_result = build_job_replay(session_id=sid, job_id=focus_job)
        if replay_result.ok:
            replay = replay_result.replay

    rerun_plan: dict[str, Any] | None = None
    if include_rerun_plan:
        rp_result = build_governed_rerun_plan(session_id=sid, job_id=focus_job)
        if rp_result.ok:
            rerun_plan = rp_result.plan

    nodes, edges = _build_nodes_and_edges(bundle=bundle, replay=replay, rerun_plan=rerun_plan)
    correlated = _correlated_executions(bundle=bundle, nodes=nodes, edges=edges)
    failures = _repeated_failures(bundle=bundle, replay=replay)
    blast = _historical_blast_radius(rerun_plan=rerun_plan, bundle=bundle)
    recurring = _recurring_blockers(bundle=bundle, rerun_plan=rerun_plan)
    lineage = _mission_lineage(bundle=bundle, nodes=nodes)
    cross_links = _cross_domain_links(nodes=nodes, edges=edges)
    learning = _learning_signals(correlated=correlated, failures=failures, recurring=recurring)

    graph: dict[str, Any] = {
        "schema_version": OPERATIONAL_MEMORY_SCHEMA_VERSION,
        "fix": OPERATIONAL_MEMORY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_139,
        "autonomous_adaptation_enabled": AUTONOMOUS_ADAPTATION_ENABLED_FIX_139,
        "invariant": OPERATIONAL_MEMORY_INVARIANT,
        "session_id": sid,
        "job_id": focus_job,
        "plan_id": (bundle.get("mission") or {}).get("plan_id"),
        "correlation_id": (bundle.get("mission") or {}).get("correlation_id"),
        "graph": {
            "node_kinds": list(OPERATIONAL_MEMORY_NODE_KINDS),
            "edge_kinds": list(OPERATIONAL_MEMORY_EDGE_KINDS),
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "nodes_by_kind": dict(Counter(n.get("kind") for n in nodes)),
            },
        },
        "correlated_executions": correlated,
        "repeated_failures": failures,
        "historical_blast_radius": blast,
        "recurring_blockers": recurring,
        "mission_lineage": lineage,
        "cross_domain_links": cross_links,
        "learning_signals": learning,
        "sources": {
            "evidence_bundle": True,
            "job_replay": replay is not None,
            "rerun_plan": rerun_plan is not None,
        },
    }
    return OperationalMemoryResult(
        ok=True,
        session_id=sid,
        graph=graph,
        detail="Operational memory graph built (read-only).",
    )
