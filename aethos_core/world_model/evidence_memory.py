# SPDX-License-Identifier: Apache-2.0
"""Evidence memory for investigations."""

from __future__ import annotations

from typing import Any

from aethos_core.world_model.investigation_state import InvestigationState


def evidence_tags_from_payload(evidence: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    root = dict(evidence.get("root_cause") or {})
    correlation = dict(evidence.get("evidence_correlation") or {})
    freshness = dict(correlation.get("freshness") or {})

    if evidence.get("logs_available"):
        if freshness.get("runtime_logs") == "fresh":
            tags.append("fresh_runtime_logs")
        else:
            tags.append("runtime_logs")
        corpus = " ".join(str(row.get("message") or "") for row in evidence.get("logs") or []).lower()
        if "wiredtiger" in corpus:
            tags.append("fresh_wiredtiger_logs")
        if any(token in corpus for token in ("exit code", "exited", "fatal", "error", "oom", "corrupt", "disk")):
            tags.append("high_signal_logs")
    else:
        tags.append("logs_unavailable")

    if evidence.get("events_available"):
        if freshness.get("service_events") == "fresh":
            tags.append("fresh_service_events")
        elif freshness.get("service_events") == "stale":
            tags.append("stale_service_events")
        else:
            tags.append("service_events")
    else:
        tags.append("service_events_missing")

    status = str(evidence.get("status") or evidence.get("deployment_state") or "").lower()
    if status in {"failed", "crashed", "error", "unhealthy"}:
        tags.append("failed_runtime_status")

    category = str(root.get("category") or "")
    if category:
        tags.append(f"root_category:{category}")
    for conflict in correlation.get("conflicts") or []:
        if "success" in str(conflict).lower():
            tags.append("success_event_conflict")
    return sorted(set(tags))


def missing_evidence_from_payload(evidence: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    root = dict(evidence.get("root_cause") or {})
    correlation = dict(evidence.get("evidence_correlation") or {})
    freshness = dict(correlation.get("freshness") or {})

    for gap in root.get("evidence_gaps") or []:
        missing.append(str(gap))
    if freshness.get("service_events") in {"stale", "unknown"}:
        missing.append("recent_failure_events")
    if not any("exit" in tag for tag in evidence_tags_from_payload(evidence)):
        missing.append("exit_code")
    if "fresh_wiredtiger_logs" in evidence_tags_from_payload(evidence):
        missing.append("storage-volume health")
    if not evidence.get("logs_available"):
        missing.append("deployment/runtime logs near failure window")
    return sorted(set(missing))


def merge_evidence_memory(state: InvestigationState, evidence: dict[str, Any]) -> InvestigationState:
    tags = evidence_tags_from_payload(evidence)
    state.evidence = sorted(set(state.evidence) | set(tags))
    state.missing_evidence = missing_evidence_from_payload(evidence)
    return state
