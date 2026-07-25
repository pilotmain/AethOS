# SPDX-License-Identifier: Apache-2.0
"""FIX 140 — cross-session organizational memory (read-only correlation + persistence)."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aethos_core.mission_control.operational_memory.cross_session.cross_session_contract import (
    AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
    AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140,
    CROSS_SESSION_MEMORY_FIX,
    CROSS_SESSION_MEMORY_INVARIANT,
    CROSS_SESSION_MEMORY_SCHEMA_VERSION,
    MAX_PERSISTED_RECORDS_DEFAULT,
    MUTATION_PERFORMED_FIX_140,
)
from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    list_operational_memory_records,
    persist_operational_memory_record,
    prune_operational_memory_records,
)
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph

_DATA_ROOT = Path(__file__).resolve().parents[3] / "data"


@dataclass(frozen=True)
class CrossSessionMemoryResult:
    ok: bool
    session_id: str
    memory: dict[str, Any] = field(default_factory=dict)
    blockers: list[str] = field(default_factory=list)
    detail: str = ""


def _exported_at() -> str:
    return datetime.now(UTC).isoformat()


def _read_json_dir(relative: str, *, limit: int = 20) -> list[dict[str, Any]]:
    root = _DATA_ROOT / relative
    if not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = __import__("json").loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            payload = dict(payload)
            payload["_source_file"] = path.name
            rows.append(payload)
        if len(rows) >= limit:
            break
    return rows


def ingest_session_operational_memory(*, session_id: str) -> dict[str, Any] | None:
    result = build_operational_memory_graph(session_id=session_id)
    if not result.ok:
        return None
    return persist_operational_memory_record(graph=result.graph)


def _missions_across_sessions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_correlation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        pid = str(row.get("plan_id") or "")
        cid = str(row.get("correlation_id") or "")
        if pid:
            by_plan[pid].append(row)
        if cid:
            by_correlation[cid].append(row)

    groups: list[dict[str, Any]] = []
    for plan_id, rows in by_plan.items():
        sessions = sorted({str(r.get("session_id") or "") for r in rows})
        if len(sessions) >= 1:
            groups.append(
                {
                    "kind": "plan_id",
                    "key": plan_id,
                    "session_ids": sessions,
                    "record_count": len(rows),
                    "read_only": True,
                }
            )
    for cid, rows in by_correlation.items():
        sessions = sorted({str(r.get("session_id") or "") for r in rows})
        if len(sessions) > 1:
            groups.append(
                {
                    "kind": "correlation_id",
                    "key": cid,
                    "session_ids": sessions,
                    "record_count": len(rows),
                    "read_only": True,
                }
            )
    return sorted(groups, key=lambda g: -int(g.get("record_count") or 0))[:30]


def _recurring_incidents(*, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    global_incidents = _read_json_dir("railway_production_incidents", limit=30)
    counts: Counter[str] = Counter()
    for inc in global_incidents:
        iid = str(inc.get("incident_id") or inc.get("title") or inc.get("_source_file") or "")
        if iid:
            counts[iid] += 1
    for row in records:
        for iid in row.get("incident_keys") or []:
            counts[str(iid)] += 1

    return [
        {
            "incident_id": iid,
            "occurrences": n,
            "sources": ["global_incidents", "persisted_records"],
            "read_only": True,
        }
        for iid, n in counts.most_common(15)
        if n >= 1
    ]


def _pr_lineage_across_sessions(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_pr: dict[str, list[str]] = defaultdict(list)
    for row in records:
        sid = str(row.get("session_id") or "")
        for pr in row.get("pr_keys") or []:
            by_pr[str(pr)].append(sid)
    return [
        {
            "pr_key": pr,
            "session_ids": sorted(set(sessions)),
            "session_count": len(set(sessions)),
            "read_only": True,
        }
        for pr, sessions in sorted(by_pr.items(), key=lambda x: -len(x[1]))
        if pr
    ][:25]


def _historical_blockers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    session_map: dict[str, set[str]] = defaultdict(set)
    for row in records:
        sid = str(row.get("session_id") or "")
        for sig in row.get("blocker_signatures") or []:
            sig = str(sig)
            if not sig:
                continue
            counts[sig] += 1
            session_map[sig].add(sid)
    return [
        {
            "blocker": sig,
            "occurrences": n,
            "session_ids": sorted(session_map[sig]),
            "cross_session": len(session_map[sig]) > 1,
            "read_only": True,
        }
        for sig, n in counts.most_common(20)
    ]


def _operator_history(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    history: list[dict[str, Any]] = []
    for row in sorted(records, key=lambda r: str(r.get("recorded_at") or ""), reverse=True):
        history.append(
            {
                "record_id": row.get("record_id"),
                "recorded_at": row.get("recorded_at"),
                "session_id": row.get("session_id"),
                "plan_id": row.get("plan_id"),
                "correlation_id": row.get("correlation_id"),
                "node_count": (row.get("graph_stats") or {}).get("node_count"),
                "read_only": True,
            }
        )
    return history[:50]


def _mission_ancestry(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Chain missions by shared plan_id prefix / sequential recorded_at within plan families."""
    by_plan: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        pid = str(row.get("plan_id") or "")
        if pid:
            by_plan[pid].append(row)

    chains: list[dict[str, Any]] = []
    for plan_id, rows in sorted(by_plan.items()):
        ordered = sorted(rows, key=lambda r: str(r.get("recorded_at") or ""))
        chains.append(
            {
                "plan_id": plan_id,
                "ancestry": [
                    {
                        "record_id": r.get("record_id"),
                        "session_id": r.get("session_id"),
                        "recorded_at": r.get("recorded_at"),
                    }
                    for r in ordered
                ],
                "depth": len(ordered),
                "read_only": True,
            }
        )
    return chains[:30]


def _approval_risk_patterns(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    gate_counts: Counter[str] = Counter()
    outcomes: Counter[str] = Counter()
    for row in records:
        for appr in row.get("approval_rows") or []:
            gate = str(appr.get("gate_id") or "")
            if gate:
                gate_counts[gate] += 1
            outcome = str(appr.get("outcome") or appr.get("state") or "")
            if outcome:
                outcomes[outcome] += 1
    patterns: list[dict[str, Any]] = []
    for gate, count in gate_counts.most_common(15):
        patterns.append(
            {
                "pattern": "gate_frequency",
                "gate_id": gate,
                "occurrences": count,
                "read_only": True,
            }
        )
    for outcome, count in outcomes.most_common(10):
        patterns.append(
            {
                "pattern": "approval_outcome",
                "outcome": outcome,
                "occurrences": count,
                "read_only": True,
            }
        )
    return patterns


def _rollout_lineage() -> list[dict[str, Any]]:
    rollouts = _read_json_dir("railway_production_rollout_journal", limit=15)
    lineage: list[dict[str, Any]] = []
    for row in rollouts:
        lineage.append(
            {
                "execution_id": row.get("execution_id"),
                "current_stage": row.get("current_stage"),
                "recorded_at": row.get("recorded_at"),
                "source_file": row.get("_source_file"),
                "read_only": True,
            }
        )
    return lineage


def _evidence_stitching(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Link persisted records that share plan_id, PR, or incident keys."""
    stitches: list[dict[str, Any]] = []
    plan_index: dict[str, list[str]] = defaultdict(list)
    pr_index: dict[str, list[str]] = defaultdict(list)
    inc_index: dict[str, list[str]] = defaultdict(list)

    for row in records:
        rid = str(row.get("record_id") or "")
        if not rid:
            continue
        pid = str(row.get("plan_id") or "")
        if pid:
            plan_index[pid].append(rid)
        for pr in row.get("pr_keys") or []:
            pr_index[str(pr)].append(rid)
        for inc in row.get("incident_keys") or []:
            inc_index[str(inc)].append(rid)

    def _emit(kind: str, key: str, record_ids: list[str]) -> None:
        if len(record_ids) < 2:
            return
        stitches.append(
            {
                "stitch_kind": kind,
                "key": key,
                "record_ids": record_ids,
                "record_count": len(record_ids),
                "read_only": True,
            }
        )

    for pid, rids in plan_index.items():
        _emit("plan_id", pid, rids)
    for pr, rids in pr_index.items():
        _emit("pr", pr, rids)
    for inc, rids in inc_index.items():
        _emit("incident", inc, rids)

    return stitches[:40]


def _organizational_learning_signals(
    *,
    missions: list[dict[str, Any]],
    blockers: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    stitches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    cross_session_missions = [m for m in missions if len(m.get("session_ids") or []) > 1]
    if cross_session_missions:
        signals.append(
            {
                "signal": "cross_session_mission_correlation",
                "detail": f"{len(cross_session_missions)} mission group(s) span multiple sessions",
                "actionable": False,
            }
        )
    cross_blockers = [b for b in blockers if b.get("cross_session")]
    if cross_blockers:
        signals.append(
            {
                "signal": "historical_recurring_blockers",
                "detail": f"{len(cross_blockers)} blocker signature(s) recur across sessions",
                "actionable": False,
            }
        )
    hot_incidents = [i for i in incidents if int(i.get("occurrences") or 0) >= 2]
    if hot_incidents:
        signals.append(
            {
                "signal": "recurring_incident_pattern",
                "detail": f"{len(hot_incidents)} incident(s) show repeated presence",
                "actionable": False,
            }
        )
    if stitches:
        signals.append(
            {
                "signal": "cross_session_evidence_stitching",
                "detail": f"{len(stitches)} evidence stitch group(s) link persisted records",
                "actionable": False,
            }
        )
    if not signals:
        signals.append(
            {
                "signal": "organizational_baseline",
                "detail": "Cross-session memory layer active; build history by visiting sessions",
                "actionable": False,
            }
        )
    return signals


def build_cross_session_operational_memory(
    *,
    session_id: str,
    ingest_current: bool = True,
    limit: int = MAX_PERSISTED_RECORDS_DEFAULT,
) -> CrossSessionMemoryResult:
    sid = (session_id or "default").strip()[:64] or "default"
    ingested: dict[str, Any] | None = None

    if ingest_current:
        ingested = ingest_session_operational_memory(session_id=sid)

    records = list_operational_memory_records(limit=limit)
    prune_operational_memory_records(keep=limit * 2)

    missions = _missions_across_sessions(records)
    incidents = _recurring_incidents(records=records)
    pr_lineage = _pr_lineage_across_sessions(records)
    blockers = _historical_blockers(records)
    history = _operator_history(records)
    ancestry = _mission_ancestry(records)
    approval_patterns = _approval_risk_patterns(records)
    rollout_lineage = _rollout_lineage()
    stitches = _evidence_stitching(records)
    learning = _organizational_learning_signals(
        missions=missions,
        blockers=blockers,
        incidents=incidents,
        stitches=stitches,
    )

    memory: dict[str, Any] = {
        "schema_version": CROSS_SESSION_MEMORY_SCHEMA_VERSION,
        "fix": CROSS_SESSION_MEMORY_FIX,
        "exported_at": _exported_at(),
        "read_only": True,
        "mutation_performed": MUTATION_PERFORMED_FIX_140,
        "autonomous_adaptation_enabled": AUTONOMOUS_ADAPTATION_ENABLED_FIX_140,
        "autonomous_optimization_enabled": AUTONOMOUS_OPTIMIZATION_ENABLED_FIX_140,
        "invariant": CROSS_SESSION_MEMORY_INVARIANT,
        "focal_session_id": sid,
        "ingested_current_session": ingested is not None,
        "current_ingest_record_id": (ingested or {}).get("record_id"),
        "persisted_record_count": len(records),
        "organizational_memory": {
            "missions_across_sessions": missions,
            "recurring_incidents": incidents,
            "pr_lineage_across_sessions": pr_lineage,
            "historical_blockers": blockers,
            "operator_history": history,
            "mission_ancestry": ancestry,
            "approval_risk_patterns": approval_patterns,
            "rollout_lineage": rollout_lineage,
            "evidence_stitching": stitches,
        },
        "learning_signals": learning,
    }
    return CrossSessionMemoryResult(
        ok=True,
        session_id=sid,
        memory=memory,
        detail="Cross-session operational memory built (read-only organizational layer).",
    )
