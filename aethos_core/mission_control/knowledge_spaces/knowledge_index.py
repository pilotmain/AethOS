# SPDX-License-Identifier: Apache-2.0
"""FIX 141 — build mission-centric knowledge documents for semantic retrieval."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from aethos_core.mission_control.operational_memory.cross_session.cross_session_store import (
    list_operational_memory_records,
)
from aethos_core.mission_control.operational_memory.operational_memory_service import build_operational_memory_graph

_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"


def _space_id(*, plan_id: str = "", correlation_id: str = "", session_id: str = "") -> str:
    if plan_id:
        return f"mission:plan:{plan_id}"
    if correlation_id:
        return f"mission:correlation:{correlation_id}"
    return f"session:{session_id or 'default'}"


def _doc(
    *,
    doc_id: str,
    space_id: str,
    category: str,
    text: str,
    session_id: str = "",
    recorded_at: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "doc_id": doc_id,
        "space_id": space_id,
        "category": category,
        "text": text,
        "session_id": session_id,
        "recorded_at": recorded_at,
        "metadata": metadata or {},
        "read_only": True,
    }


def _read_json_dir(relative: str, *, limit: int = 25) -> list[dict[str, Any]]:
    root = _DATA_ROOT / relative
    if not root.is_dir():
        return []
    import json

    rows: list[dict[str, Any]] = []
    for path in sorted(root.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(payload, dict):
            rows.append(payload)
        if len(rows) >= limit:
            break
    return rows


def documents_from_persisted_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for row in records:
        sid = str(row.get("session_id") or "")
        plan_id = str(row.get("plan_id") or "")
        cid = str(row.get("correlation_id") or "")
        space = _space_id(plan_id=plan_id, correlation_id=cid, session_id=sid)
        recorded = str(row.get("recorded_at") or "")
        rid = str(row.get("record_id") or "")

        docs.append(
            _doc(
                doc_id=f"{rid}:mission",
                space_id=space,
                category="mission",
                text=f"mission session={sid} plan={plan_id} correlation={cid} nodes={(row.get('graph_stats') or {}).get('node_count', 0)}",
                session_id=sid,
                recorded_at=recorded,
                metadata={"record_id": rid, "plan_id": plan_id},
            )
        )

        for sig in row.get("blocker_signatures") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:blocker:{sig[:32]}",
                    space_id=space,
                    category="blocker",
                    text=f"blocker {sig} session={sid} plan={plan_id}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for sig in row.get("failure_signatures") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:failure:{sig[:32]}",
                    space_id=space,
                    category="failure",
                    text=f"failure {sig} session={sid}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for pr in row.get("pr_keys") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:pr:{pr[:32]}",
                    space_id=space,
                    category="pr",
                    text=f"github pr {pr} plan={plan_id} session={sid}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for inc in row.get("incident_keys") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:incident:{inc[:32]}",
                    space_id=space,
                    category="incident",
                    text=f"production incident {inc} session={sid}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for gate in row.get("gate_keys") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:approval:{gate}",
                    space_id=space,
                    category="approval",
                    text=f"governance gate {gate} approval session={sid} plan={plan_id}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for appr in row.get("approval_rows") or []:
            gate = str(appr.get("gate_id") or "")
            outcome = str(appr.get("outcome") or appr.get("state") or "")
            docs.append(
                _doc(
                    doc_id=f"{rid}:approval_row:{gate}",
                    space_id=space,
                    category="approval",
                    text=f"approval gate={gate} outcome={outcome} session={sid}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for stage in row.get("rollout_stages") or []:
            docs.append(
                _doc(
                    doc_id=f"{rid}:rollout:{stage}",
                    space_id=space,
                    category="rollout",
                    text=f"production rollout stage {stage} session={sid}",
                    session_id=sid,
                    recorded_at=recorded,
                )
            )

        for sig in row.get("learning_signals") or []:
            if isinstance(sig, dict):
                docs.append(
                    _doc(
                        doc_id=f"{rid}:finding:{sig.get('signal', '')[:24]}",
                        space_id=space,
                        category="agent_finding",
                        text=f"operational signal {sig.get('signal', '')} {sig.get('detail', '')}",
                        session_id=sid,
                        recorded_at=recorded,
                    )
                )

    return docs


def documents_from_current_graph(graph: dict[str, Any]) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    sid = str(graph.get("session_id") or "")
    plan_id = str(graph.get("plan_id") or "")
    cid = str(graph.get("correlation_id") or "")
    space = _space_id(plan_id=plan_id, correlation_id=cid, session_id=sid)
    recorded = str(graph.get("exported_at") or "")

    for node in (graph.get("graph") or {}).get("nodes") or []:
        kind = str(node.get("kind") or "mission")
        if kind not in {
            "incident",
            "blocker",
            "approval",
            "pr",
            "verification",
            "rerun_plan",
            "agent_finding",
            "rollout",
        }:
            continue
        key = str(node.get("key") or "")
        text = f"{kind} {key} " + " ".join(f"{k}={v}" for k, v in node.items() if k not in {"id", "kind", "key"} and v)
        docs.append(
            _doc(
                doc_id=f"live:{kind}:{key[:40]}",
                space_id=space,
                category=kind if kind != "rerun_plan" else "rerun_plan",
                text=text,
                session_id=sid,
                recorded_at=recorded,
                metadata={"live": True},
            )
        )

    ver = graph.get("verification") or {}
    if ver.get("sections"):
        docs.append(
            _doc(
                doc_id=f"live:verification:{sid}",
                space_id=space,
                category="verification",
                text=f"workspace verification evidence sections={len(ver.get('sections') or [])} session={sid}",
                session_id=sid,
                recorded_at=recorded,
            )
        )

    rp = graph.get("rerun_blockers") if "rerun_blockers" in graph else None
    if isinstance(graph.get("historical_blast_radius"), dict):
        br = graph["historical_blast_radius"]
        docs.append(
            _doc(
                doc_id=f"live:rerun_plan:{sid}",
                space_id=space,
                category="rerun_plan",
                text=f"rerun plan blast radius risk={br.get('risk_tier', '')} session={sid} planning only",
                session_id=sid,
                recorded_at=recorded,
            )
        )

    for b in graph.get("recurring_blockers") or []:
        docs.append(
            _doc(
                doc_id=f"live:blocker:{b.get('blocker', '')[:32]}",
                space_id=space,
                category="blocker",
                text=f"recurring blocker {b.get('blocker', '')} occurrences={b.get('occurrences', 0)}",
                session_id=sid,
                recorded_at=recorded,
            )
        )

    for f in graph.get("repeated_failures") or []:
        docs.append(
            _doc(
                doc_id=f"live:failure:{f.get('signature', '')[:32]}",
                space_id=space,
                category="failure",
                text=f"repeated failure {f.get('signature', '')}",
                session_id=sid,
                recorded_at=recorded,
            )
        )

    return docs


def documents_from_global_sources() -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []
    for inc in _read_json_dir("railway_production_incidents", limit=20):
        iid = str(inc.get("incident_id") or inc.get("title") or "")
        docs.append(
            _doc(
                doc_id=f"global:incident:{iid[:40]}",
                space_id="organizational:incidents",
                category="incident",
                text=f"incident {iid} status={inc.get('status', '')} title={inc.get('title', '')}",
                recorded_at=str(inc.get("recorded_at") or inc.get("opened_at") or ""),
                metadata={"global": True},
            )
        )
    for roll in _read_json_dir("railway_production_rollout_journal", limit=15):
        docs.append(
            _doc(
                doc_id=f"global:rollout:{roll.get('execution_id', '')[:24]}",
                space_id="organizational:rollouts",
                category="rollout",
                text=f"rollout stage={roll.get('current_stage', '')} execution={roll.get('execution_id', '')}",
                recorded_at=str(roll.get("recorded_at") or ""),
                metadata={"global": True},
            )
        )
    return docs


def build_knowledge_corpus(*, session_id: str, include_live: bool = True) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Return (documents, knowledge_spaces index)."""
    records = list_operational_memory_records(limit=200)
    docs = documents_from_persisted_records(records)
    docs.extend(documents_from_global_sources())

    if include_live:
        live = build_operational_memory_graph(session_id=session_id)
        if live.ok:
            docs.extend(documents_from_current_graph(live.graph))

    spaces: dict[str, dict[str, Any]] = {}
    for doc in docs:
        sid = str(doc.get("space_id") or "")
        if not sid:
            continue
        entry = spaces.setdefault(
            sid,
            {
                "space_id": sid,
                "document_count": 0,
                "categories": set(),
                "session_ids": set(),
            },
        )
        entry["document_count"] = int(entry["document_count"]) + 1
        entry["categories"].add(str(doc.get("category") or ""))
        if doc.get("session_id"):
            entry["session_ids"].add(str(doc["session_id"]))

    space_list = []
    for sid, entry in sorted(spaces.items()):
        space_list.append(
            {
                "space_id": sid,
                "document_count": entry["document_count"],
                "categories": sorted(entry["categories"]),
                "session_ids": sorted(entry["session_ids"]),
                "read_only": True,
            }
        )

    return docs, space_list
