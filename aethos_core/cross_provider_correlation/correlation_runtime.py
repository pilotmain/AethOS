# SPDX-License-Identifier: Apache-2.0
"""Cross-provider correlation runtime orchestration."""

from __future__ import annotations

from typing import Any

from aethos_core.cross_provider_correlation.correlation_diagnosis import CorrelationDiagnosis, diagnose_correlation_graph
from aethos_core.cross_provider_correlation.correlation_graph import CorrelationGraph
from aethos_core.cross_provider_correlation.correlation_reply_composer import compose_correlation_reply
from aethos_core.cross_provider_correlation.correlation_store import (
    get_session_snapshot,
    publish_railway_health_rows,
)
from aethos_core.cross_provider_correlation.evidence_linker import link_cross_provider_evidence


def build_correlation_state(*, session_id: str = "default") -> dict[str, Any]:
    publish_railway_health_rows(session_id)
    snapshot = get_session_snapshot(session_id)
    graph = link_cross_provider_evidence(snapshot, session_id=session_id)
    diagnosis = diagnose_correlation_graph(graph, snapshot=snapshot)
    return {
        "ok": True,
        "session_id": session_id,
        "updated_at": snapshot.get("updated_at"),
        "cross_provider_correlation": {
            "github_commit": (graph.github.commit_sha if graph.github else "") or None,
            "github_repo": (graph.github.repo if graph.github else "") or None,
            "vercel_project": (graph.vercel.project if graph.vercel else "") or None,
            "vercel_deployment": (graph.vercel.deployment_id if graph.vercel else "") or None,
            "railway_service": (
                f"{graph.railway.project}/{graph.railway.service}" if graph.railway and graph.railway.service else None
            ),
            "matched_commit": graph.matched_commit or None,
            "failure_boundary": diagnosis.failure_boundary,
            "confidence": diagnosis.confidence,
            "conclusion": diagnosis.conclusion,
            "needs_binding": diagnosis.needs_binding,
            "links": [link.to_dict() for link in graph.links],
        },
        "graph": graph.to_dict(),
        "diagnosis": diagnosis.to_dict(),
    }


def run_correlation_analysis(
    *,
    session_id: str = "default",
    intent: str = "push_trace",
    repository: str = "",
    project: str = "",
) -> tuple[str, dict[str, str], CorrelationGraph, CorrelationDiagnosis]:
    publish_railway_health_rows(session_id)
    snapshot = get_session_snapshot(session_id)
    graph = link_cross_provider_evidence(snapshot, session_id=session_id)
    diagnosis = diagnose_correlation_graph(graph, snapshot=snapshot)

    if diagnosis.needs_binding and not graph.links:
        reply = _compose_binding_needed_reply(repository=repository, project=project)
    else:
        reply = compose_correlation_reply(
            intent=intent,
            diagnosis=diagnosis,
            graph=graph,
            snapshot=snapshot,
        )

    meta = {
        "route_id": "cross_provider_correlation",
        "matched_module": "cross_provider_correlation.correlation_runtime",
        "correlation_intent": intent,
        "failure_boundary": diagnosis.failure_boundary,
        "correlation_confidence": diagnosis.confidence,
        "github_correlation": "true" if graph.github else "false",
        "vercel_correlation": "true" if graph.vercel else "false",
        "railway_correlation": "true" if graph.railway else "false",
    }
    if graph.matched_commit:
        meta["matched_commit"] = graph.matched_commit[:12]
    return reply, meta, graph, diagnosis


def _compose_binding_needed_reply(*, repository: str, project: str) -> str:
    hints: list[str] = []
    if repository:
        hints.append(f"GitHub repo `{repository}`")
    if project:
        hints.append(f"Vercel project `{project}`")
    hint_text = " and ".join(hints) if hints else "your GitHub repo, Vercel project, and Railway service"
    return (
        "I could not correlate deployment evidence across providers yet.\n\n"
        f"Available evidence did not link {hint_text} on the same commit.\n\n"
        "Next step:\n"
        "Add or refresh provider source bindings, then rerun GitHub/Vercel/Railway readonly diagnostics.\n\n"
        "No mutation has been performed."
    )
