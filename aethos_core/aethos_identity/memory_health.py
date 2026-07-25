# SPDX-License-Identifier: Apache-2.0
"""Detect memory gaps before AethOS claims it has no context."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MemoryHealthReport:
    session_id: str
    active_thread_present: bool = False
    active_thread_expired: bool = False
    recent_execution_job: bool = False
    recent_preflight_job: bool = False
    topology_match: bool = False
    service_phrase: str = ""
    provider_matches: list[dict[str, Any]] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    reconstructable: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "active_thread_present": self.active_thread_present,
            "active_thread_expired": self.active_thread_expired,
            "recent_execution_job": self.recent_execution_job,
            "recent_preflight_job": self.recent_preflight_job,
            "topology_match": self.topology_match,
            "service_phrase": self.service_phrase,
            "provider_matches": list(self.provider_matches),
            "gaps": list(self.gaps),
            "reconstructable": self.reconstructable,
        }


def assess_memory_health(*, session_id: str, user_text: str = "") -> MemoryHealthReport:
    from aethos_core.aethos_identity.context_reconstructor import extract_operational_resource_phrase, search_provider_targets
    from aethos_core.operational_thread_memory.mutation_thread_memory import find_execution_job_for_service
    from aethos_core.operational_thread_memory.thread_persistence import get_active_thread, is_thread_expired, load_thread_state
    from aethos_core.runtime.jobs import job_store

    report = MemoryHealthReport(session_id=session_id)
    phrase = extract_operational_resource_phrase(user_text) or ""
    report.service_phrase = phrase

    thread = get_active_thread(session_id=session_id)
    if thread is not None:
        report.active_thread_present = True
    else:
        stale = load_thread_state(session_id=session_id)
        if stale is not None and is_thread_expired(stale):
            report.active_thread_expired = True

    if phrase:
        report.topology_match = bool(search_provider_targets(phrase).matches)
        report.provider_matches = [m.to_dict() for m in search_provider_targets(phrase).matches[:4]]
        job = find_execution_job_for_service(session_id=session_id, service_phrase=phrase)
        report.recent_execution_job = job is not None

    for row in reversed(job_store.list_all()):
        if str(getattr(row, "session_id", "") or "") != session_id:
            continue
        if row.job_type == "mutation_preflight":
            report.recent_preflight_job = True
            break
        if row.job_type == "mutation_execution":
            report.recent_execution_job = True

    if not report.active_thread_present and (report.topology_match or report.recent_execution_job):
        report.reconstructable = True
    elif report.active_thread_expired and (report.topology_match or report.recent_execution_job):
        report.reconstructable = True
    elif report.active_thread_present:
        report.reconstructable = True

    if not report.active_thread_present and not report.reconstructable:
        report.gaps.append("no_active_thread")
    if phrase and not report.topology_match and not report.recent_execution_job:
        report.gaps.append("service_not_in_topology")
    if report.active_thread_expired:
        report.gaps.append("thread_expired")

    return report
