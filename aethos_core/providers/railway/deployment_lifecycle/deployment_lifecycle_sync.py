# SPDX-License-Identifier: Apache-2.0
"""Merge legacy Railway deployment artifacts into the canonical lifecycle record."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    empty_lifecycle_record,
    get_lifecycle_session,
    save_lifecycle_record,
)


def _merge_records(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key in ("repo", "branch", "project", "environment", "service_name", "lifecycle_id"):
        if incoming.get(key) and not merged.get(key):
            merged[key] = incoming[key]
        elif incoming.get(key):
            merged[key] = incoming[key]

    for section in ("readiness", "plan", "preflight", "simulation"):
        cur = dict(merged.get(section) or {})
        inc = dict(incoming.get(section) or {})
        if section == "readiness":
            if inc.get("status") not in {None, "", "unknown"}:
                cur["status"] = inc["status"]
            if inc.get("checked_at"):
                cur["checked_at"] = inc["checked_at"]
            if inc.get("checks"):
                cur["checks"] = dict(inc["checks"])
        elif section == "plan":
            for flag in ("exists", "mutation_ready", "review_confirmed"):
                if inc.get(flag):
                    cur[flag] = inc[flag]
            if inc.get("snapshot"):
                cur["snapshot"] = dict(inc["snapshot"])
        elif section == "preflight":
            if inc.get("exists"):
                cur["exists"] = True
            if inc.get("preflight_id"):
                cur["preflight_id"] = inc["preflight_id"]
            if inc.get("approved"):
                cur["approved"] = True
            if inc.get("snapshot"):
                cur["snapshot"] = dict(inc["snapshot"])
        elif section == "simulation":
            if inc.get("exists"):
                cur["exists"] = True
            if "ready_to_execute" in inc:
                cur["ready_to_execute"] = inc["ready_to_execute"]
            if inc.get("blocking_reasons"):
                cur["blocking_reasons"] = list(inc["blocking_reasons"])
            if inc.get("snapshot"):
                cur["snapshot"] = dict(inc["snapshot"])
        merged[section] = cur
    return merged


def lifecycle_record_from_readiness(
    *,
    checks: dict[str, Any],
    repo: str = "",
    session_id: str = "default",
) -> dict[str, Any]:
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_checks import (
        extract_github_repo_target,
    )
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_plan import (
        readonly_checks_passed,
    )

    repo = repo or str(checks.get("referenced_github_repo") or extract_github_repo_target("") or "")
    record = empty_lifecycle_record(repo=repo)
    record["readiness"] = {
        "status": "passed" if readonly_checks_passed(checks) else "failed",
        "checked_at": datetime.now(UTC).isoformat(),
        "checks": dict(checks),
    }
    record["session_id"] = session_id
    return record


def lifecycle_record_from_plan(*, plan: dict[str, Any], session_id: str = "default") -> dict[str, Any]:
    from aethos_core.providers.railway.deployment_plan.plan_readiness_gate import assess_mutation_readiness_gate
    from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed

    repo = str(plan.get("repo") or "")
    record = empty_lifecycle_record(repo=repo)
    gate = assess_mutation_readiness_gate(plan)
    record.update(
        {
            "repo": repo,
            "branch": str(plan.get("branch") or "main"),
            "project": str(plan.get("project") or ""),
            "environment": str(plan.get("environment") or ""),
            "service_name": str(plan.get("service_name") or ""),
            "session_id": session_id,
            "plan": {
                "exists": bool(repo),
                "mutation_ready": bool(gate.get("mutation_ready")),
                "review_confirmed": is_plan_review_confirmed(plan),
                "snapshot": dict(plan),
            },
        }
    )
    if plan.get("readiness_passed"):
        record["readiness"]["status"] = "passed"
    return record


def lifecycle_record_from_preflight(*, preflight: dict[str, Any], session_id: str = "default") -> dict[str, Any]:
    plan = dict(preflight.get("plan_snapshot") or {})
    record = lifecycle_record_from_plan(plan=plan, session_id=session_id) if plan.get("repo") else empty_lifecycle_record()
    record["preflight"] = {
        "exists": True,
        "preflight_id": str(preflight.get("preflight_id") or ""),
        "approved": bool(preflight.get("preflight_approved")),
        "snapshot": dict(preflight),
    }
    record["repo"] = str(preflight.get("repo") or record.get("repo") or "")
    record["session_id"] = session_id
    return record


def lifecycle_record_from_simulation(*, simulation: dict[str, Any], session_id: str = "default") -> dict[str, Any]:
    record = empty_lifecycle_record(repo=str(simulation.get("repo") or ""))
    record.update(
        {
            "repo": str(simulation.get("repo") or ""),
            "branch": str(simulation.get("branch") or "main"),
            "project": str(simulation.get("project") or ""),
            "environment": str(simulation.get("environment") or ""),
            "service_name": str(simulation.get("service_name") or ""),
            "session_id": session_id,
            "simulation": {
                "exists": True,
                "ready_to_execute": bool(simulation.get("ready_to_execute")),
                "blocking_reasons": list(simulation.get("blocking_reasons") or []),
                "snapshot": dict(simulation),
            },
        }
    )
    return record


def upsert_lifecycle(*, session_id: str, partial: dict[str, Any]) -> dict[str, Any]:
    session_id = (session_id or "default").strip()
    existing = get_lifecycle_session(session_id=session_id)
    base = existing if existing else empty_lifecycle_record(repo=str(partial.get("repo") or ""))
    merged = _merge_records(base, partial)
    return save_lifecycle_record(session_id=session_id, record=merged)


def sync_lifecycle_after_readiness(*, session_id: str, checks: dict[str, Any]) -> None:
    partial = lifecycle_record_from_readiness(checks=checks, session_id=session_id)
    upsert_lifecycle(session_id=session_id, partial=partial)


def sync_lifecycle_after_plan(*, session_id: str, plan: dict[str, Any]) -> None:
    partial = lifecycle_record_from_plan(plan=plan, session_id=session_id)
    upsert_lifecycle(session_id=session_id, partial=partial)


def sync_lifecycle_after_preflight(*, session_id: str, preflight: dict[str, Any]) -> None:
    partial = lifecycle_record_from_preflight(preflight=preflight, session_id=session_id)
    upsert_lifecycle(session_id=session_id, partial=partial)


def sync_lifecycle_after_simulation(*, session_id: str, simulation: dict[str, Any]) -> None:
    partial = lifecycle_record_from_simulation(simulation=simulation, session_id=session_id)
    upsert_lifecycle(session_id=session_id, partial=partial)
