# SPDX-License-Identifier: Apache-2.0
"""Materialize global Railway lifecycle records into session legacy stores."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
    lifecycle_plan_snapshot,
    lifecycle_preflight_snapshot,
    lifecycle_simulation_snapshot,
    materialize_lifecycle_to_legacy_stores,
)
from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_store import (
    _index_path,
    _session_path,
    _store_dir,
    inspect_global_lifecycle_index,
    load_lifecycle_by_id,
    load_latest_active_lifecycle,
    save_lifecycle_record,
)


def _lifecycle_stage(record: dict[str, Any] | None) -> str:
    if not record or not record.get("repo"):
        return "empty"
    plan = record.get("plan") or {}
    if not plan.get("exists"):
        return "pre_plan"
    if not plan.get("review_confirmed"):
        return "plan_unconfirmed"
    preflight = record.get("preflight") or {}
    if not preflight.get("exists"):
        return "plan_confirmed"
    simulation = record.get("simulation") or {}
    if not simulation.get("exists"):
        return "preflight_ready"
    return "simulated"


def _plan_snapshot_present(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    plan = record.get("plan") or {}
    snapshot = plan.get("snapshot") or {}
    return bool(plan.get("exists") and snapshot.get("repo"))


def is_corrupt_plan_lifecycle(record: dict[str, Any] | None) -> bool:
    """Plan section claims a plan exists but snapshot is missing or invalid."""
    if not record:
        return False
    plan = record.get("plan") or {}
    if not plan.get("exists"):
        return False
    return not _plan_snapshot_present(record)


def has_passed_readiness_without_plan(record: dict[str, Any] | None) -> bool:
    """Readiness passed and no materialized deployment plan snapshot (includes pre_plan staging)."""
    if not record or not record.get("repo"):
        return False
    if _plan_snapshot_present(record):
        return False
    from aethos_core.providers.railway.deployment_lifecycle.deployment_lifecycle_resolver import (
        lifecycle_readiness_passed,
    )

    return lifecycle_readiness_passed(record)


def is_readiness_only_lifecycle(record: dict[str, Any] | None) -> bool:
    """Readiness-only lifecycle for operator messaging (strict: not corrupt plan flags)."""
    if not record or not record.get("repo"):
        return False
    if _plan_snapshot_present(record) or is_corrupt_plan_lifecycle(record):
        return False
    return has_passed_readiness_without_plan(record)


def normalize_lifecycle_for_plan_creation(record: dict[str, Any] | None) -> dict[str, Any] | None:
    """Clear corrupt plan.exists flags so readiness-only acceptance is consistent."""
    if not record:
        return None
    if not is_corrupt_plan_lifecycle(record):
        return dict(record)
    normalized = dict(record)
    normalized["plan"] = {
        "exists": False,
        "mutation_ready": False,
        "review_confirmed": False,
        "snapshot": {},
    }
    return normalized


def _preflight_snapshot_present(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    preflight = record.get("preflight") or {}
    snapshot = preflight.get("snapshot") or {}
    return bool(preflight.get("exists") and snapshot.get("preflight_id"))


def _simulation_snapshot_present(record: dict[str, Any] | None) -> bool:
    if not record:
        return False
    simulation = record.get("simulation") or {}
    snapshot = simulation.get("snapshot") or {}
    return bool(simulation.get("exists") and snapshot.get("simulation_id"))


def entry_materialization_status(entry: dict[str, Any]) -> str:
    if not entry.get("file_exists"):
        return "stale_index_missing_file"
    if not entry.get("readable"):
        return "unreadable_or_corrupt_file"
    if entry.get("parse_error"):
        return "corrupt_file"
    if entry.get("plan_snapshot_present"):
        return "materializable"
    if entry.get("plan_exists") and not entry.get("plan_snapshot_present"):
        return "missing_plan_snapshot"
    if entry.get("readiness_status") == "passed" or entry.get("stage") in {
        "pre_plan",
        "readiness_passed",
    }:
        return "readiness_only"
    return "missing_plan_snapshot"


def inspect_lifecycle_file(*, session_id: str = "", lifecycle_id: str = "") -> dict[str, Any]:
    """Inspect on-disk lifecycle file for an index entry."""
    path: Path | None = None
    if session_id:
        path = _session_path(session_id)
    elif lifecycle_id:
        for candidate in _store_dir().glob("*_lifecycle.json"):
            if candidate.name == "global_lifecycle_index.json":
                continue
            try:
                raw = json.loads(candidate.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(raw, dict) and str(raw.get("lifecycle_id") or "") == lifecycle_id:
                path = candidate
                break

    diag: dict[str, Any] = {
        "file_path": str(path) if path else "",
        "file_exists": bool(path and path.is_file()),
        "readable": False,
        "parse_error": "",
    }
    if not path or not path.is_file():
        return diag
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        diag["parse_error"] = str(exc)
        return diag
    except OSError as exc:
        diag["parse_error"] = str(exc)
        return diag
    if not isinstance(raw, dict):
        diag["parse_error"] = "lifecycle file is not a JSON object"
        return diag
    diag["readable"] = True
    return diag


def inspect_global_lifecycle_entry(entry: dict[str, Any]) -> dict[str, Any]:
    """Deep diagnostics for one global lifecycle index entry."""
    lifecycle_id = str(entry.get("lifecycle_id") or "")
    session_id = str(entry.get("session_id") or "")
    repo = str(entry.get("repo") or "")
    file_diag = inspect_lifecycle_file(session_id=session_id, lifecycle_id=lifecycle_id)
    record = load_lifecycle_by_id(lifecycle_id) if lifecycle_id else None
    plan = (record or {}).get("plan") or {}
    preflight = (record or {}).get("preflight") or {}
    simulation = (record or {}).get("simulation") or {}
    inspected = {
        "lifecycle_id": lifecycle_id,
        "session_id": session_id,
        "repo": repo or str((record or {}).get("repo") or ""),
        "branch": str((record or {}).get("branch") or "main"),
        "project": str((record or {}).get("project") or ""),
        "environment": str((record or {}).get("environment") or ""),
        "service_name": str((record or {}).get("service_name") or ""),
        "stage": _lifecycle_stage(record),
        "plan_exists": bool(plan.get("exists")),
        "plan_snapshot_present": _plan_snapshot_present(record),
        "preflight_exists": bool(preflight.get("exists")),
        "preflight_snapshot_present": _preflight_snapshot_present(record),
        "simulation_exists": bool(simulation.get("exists")),
        "simulation_snapshot_present": _simulation_snapshot_present(record),
        "readiness_status": str((record or {}).get("readiness", {}).get("status") or ""),
        "readiness_only": is_readiness_only_lifecycle(record),
        "record_loaded": record is not None,
        "index_file_path": str(_index_path()),
        "lifecycle_file_path": str(file_diag.get("file_path") or ""),
        "updated_at": str(entry.get("updated_at") or (record or {}).get("updated_at") or ""),
        **file_diag,
    }
    inspected["materialization_status"] = entry_materialization_status(inspected)
    return inspected


def inspect_all_global_lifecycle_entries() -> list[dict[str, Any]]:
    index = inspect_global_lifecycle_index()
    if not index.get("readable"):
        return []
    raw_index = index.get("index") or {}
    entries = sorted(
        list(raw_index.get("entries") or []),
        key=lambda row: str(row.get("updated_at") or ""),
        reverse=True,
    )
    return [inspect_global_lifecycle_entry(dict(entry)) for entry in entries]


def _legacy_plan_fallback(repo: str) -> dict[str, Any] | None:
    if not repo:
        return None
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import load_plan_by_repo

    plan = load_plan_by_repo(repo)
    return dict(plan) if plan and plan.get("repo") else None


def enrich_lifecycle_with_legacy_plan(record: dict[str, Any]) -> dict[str, Any]:
    """Fill missing plan.snapshot from legacy plan stores when possible."""
    if _plan_snapshot_present(record):
        return record
    repo = str(record.get("repo") or "")
    plan = _legacy_plan_fallback(repo)
    if not plan:
        return record
    updated = dict(record)
    plan_section = dict(updated.get("plan") or {})
    plan_section["exists"] = True
    plan_section["snapshot"] = dict(plan)
    plan_section["mutation_ready"] = bool(plan.get("mutation_ready"))
    from aethos_core.providers.railway.deployment_plan.plan_review import is_plan_review_confirmed

    plan_section["review_confirmed"] = is_plan_review_confirmed(plan)
    updated["plan"] = plan_section
    updated.setdefault("project", plan.get("project"))
    updated.setdefault("environment", plan.get("environment"))
    updated.setdefault("service_name", plan.get("service_name"))
    updated.setdefault("branch", plan.get("branch"))
    return updated


def verify_session_materialization(*, session_id: str) -> dict[str, bool]:
    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import get_simulation

    session_id = (session_id or "default").strip()
    plan = get_deployment_plan_context(session_id=session_id)
    preflight = get_creation_preflight(session_id=session_id)
    simulation = get_simulation(session_id=session_id)
    return {
        "lifecycle_file": _session_path(session_id).is_file(),
        "plan_context": bool(plan and plan.get("repo")),
        "preflight_context": bool(preflight and preflight.get("preflight_id")),
        "simulation_context": bool(simulation and simulation.get("simulation_id")),
    }


def materialize_lifecycle_to_session(
    *,
    session_id: str,
    lifecycle: dict[str, Any],
) -> dict[str, Any]:
    """Materialize lifecycle snapshots into session stores and verify re-read."""
    session_id = (session_id or "default").strip()
    record = enrich_lifecycle_with_legacy_plan(dict(lifecycle))
    if not record.get("repo"):
        return {
            "ok": False,
            "reason": "lifecycle_record_missing_repo",
            "detail": "Lifecycle record has no repo target.",
        }
    if is_readiness_only_lifecycle(record):
        return {
            "ok": False,
            "reason": "readiness_only_no_plan",
            "detail": "Lifecycle record has readiness data only; no deployment plan snapshot yet.",
        }
    if not _plan_snapshot_present(record):
        return {
            "ok": False,
            "reason": "plan_snapshot_missing",
            "detail": "Lifecycle record exists but does not contain a deployment plan snapshot.",
        }

    persisted = save_lifecycle_record(session_id=session_id, record=record)
    materialize_lifecycle_to_legacy_stores(session_id=session_id, lifecycle=persisted)

    from aethos_core.providers.railway.deployment_plan.creation_preflight_context import (
        get_creation_preflight,
    )
    from aethos_core.providers.railway.deployment_plan.deployment_plan_context import (
        get_deployment_plan_context,
    )
    from aethos_core.providers.railway.service_creation_simulator.simulator_context import get_simulation

    plan = get_deployment_plan_context(session_id=session_id)
    preflight = get_creation_preflight(session_id=session_id)
    simulation = get_simulation(session_id=session_id)

    ok = bool(plan and plan.get("repo"))
    return {
        "ok": ok,
        "reason": "" if ok else "plan_context_missing_after_materialize",
        "detail": "" if ok else "Materialization wrote lifecycle but plan context is still missing in session.",
        "lifecycle": persisted,
        "plan_found": ok,
        "preflight_found": bool(preflight and preflight.get("preflight_id")),
        "simulation_found": bool(simulation and simulation.get("simulation_id")),
        "materialized": {
            "deployment_plan": ok,
            "creation_preflight": bool(preflight and preflight.get("preflight_id")),
            "simulation": bool(simulation and simulation.get("simulation_id")),
            "session_lifecycle_file": _session_path(session_id).is_file(),
        },
    }


def load_best_global_lifecycle_record() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load the best lifecycle record from the global index with failure diagnostics."""
    index = inspect_global_lifecycle_index()
    if not index.get("exists"):
        return None, {"reason": "index_missing", "detail": "Global lifecycle index does not exist."}
    if not index.get("readable"):
        return None, {
            "reason": "index_unreadable",
            "detail": str(index.get("error") or "Global lifecycle index is not readable."),
        }
    if int(index.get("entries") or 0) < 1:
        return None, {"reason": "index_empty", "detail": "Global lifecycle index has no entries."}

    entries = inspect_all_global_lifecycle_entries()
    for entry in entries:
        lifecycle_id = str(entry.get("lifecycle_id") or "")
        if not lifecycle_id:
            continue
        if not entry.get("file_exists"):
            continue
        record = load_lifecycle_by_id(lifecycle_id)
        if not record:
            continue
        enriched = enrich_lifecycle_with_legacy_plan(record)
        if _plan_snapshot_present(enriched):
            return enriched, {"reason": "", "detail": "", "entry": entry}

    latest = load_latest_active_lifecycle()
    if latest:
        enriched = enrich_lifecycle_with_legacy_plan(latest)
        if _plan_snapshot_present(enriched):
            return enriched, {"reason": "", "detail": ""}

    if entries and not any(e.get("file_exists") for e in entries):
        return None, {
            "reason": "stale_index",
            "detail": "Lifecycle index entry exists, but lifecycle file is missing. This index is stale.",
            "entries": entries,
        }
    loaded = [e for e in entries if e.get("record_loaded")]
    if loaded and any(
        e.get("plan_exists") and not e.get("plan_snapshot_present") for e in loaded
    ):
        return None, {
            "reason": "plan_snapshot_missing",
            "detail": "Lifecycle record exists but does not contain a deployment plan snapshot.",
            "entries": entries,
        }
    if loaded and all(e.get("materialization_status") == "readiness_only" for e in loaded):
        readiness_record: dict[str, Any] | None = None
        for entry in entries:
            lifecycle_id = str(entry.get("lifecycle_id") or "")
            if not lifecycle_id or not entry.get("file_exists"):
                continue
            candidate = load_lifecycle_by_id(lifecycle_id)
            if candidate and is_readiness_only_lifecycle(candidate):
                readiness_record = candidate
                break
        return None, {
            "reason": "readiness_only_no_plan",
            "detail": "Readiness exists, but no deployment plan has been created yet.",
            "entries": entries,
            "readiness_record": readiness_record,
        }
    return None, {
        "reason": "no_active_lifecycle",
        "detail": "No active lifecycle record could be loaded from the global index.",
        "entries": entries,
    }


def materialize_readiness_only_to_session(
    *,
    session_id: str,
    lifecycle: dict[str, Any],
) -> dict[str, Any]:
    """Persist readiness-only lifecycle into session without requiring a plan snapshot."""
    session_id = (session_id or "default").strip()
    record = dict(lifecycle)
    if not record.get("repo"):
        return {
            "ok": False,
            "reason": "lifecycle_record_missing_repo",
            "detail": "Lifecycle record has no repo target.",
        }
    if not is_readiness_only_lifecycle(record):
        return {
            "ok": False,
            "reason": "not_readiness_only_lifecycle",
            "detail": "Lifecycle record is not readiness-only.",
        }
    persisted = save_lifecycle_record(session_id=session_id, record=record)
    materialize_lifecycle_to_legacy_stores(session_id=session_id, lifecycle=persisted)
    from aethos_core.providers.railway.deployment_readiness.deployment_readiness_context import (
        get_readiness_context,
    )

    readiness_ctx = get_readiness_context(session_id=session_id)
    ok = bool(readiness_ctx and readiness_ctx.get("checks"))
    return {
        "ok": ok,
        "reason": "" if ok else "readiness_context_missing_after_materialize",
        "detail": "" if ok else "Readiness lifecycle was saved but readiness context is still missing.",
        "lifecycle": persisted,
        "readiness_materialized": ok,
    }


def load_best_readiness_only_lifecycle_record() -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Load the newest global lifecycle record that has readiness but no plan snapshot."""
    _record, diag = load_best_global_lifecycle_record()
    if _record:
        return None, {"reason": "plan_available", "detail": "A materializable deployment plan exists."}
    if diag.get("reason") != "readiness_only_no_plan":
        return None, diag
    readiness_record = diag.get("readiness_record")
    if isinstance(readiness_record, dict) and readiness_record.get("repo"):
        return readiness_record, {"reason": "", "detail": "", "entries": diag.get("entries")}
    entries = inspect_all_global_lifecycle_entries()
    for entry in entries:
        lifecycle_id = str(entry.get("lifecycle_id") or "")
        if not lifecycle_id or not entry.get("file_exists"):
            continue
        candidate = load_lifecycle_by_id(lifecycle_id)
        if candidate and is_readiness_only_lifecycle(candidate):
            return candidate, {"reason": "", "detail": "", "entry": entry}
    return None, diag


def compose_readiness_only_no_plan_reply(
    *,
    lifecycle: dict[str, Any] | None = None,
    for_simulator: bool = False,
) -> str:
    repo = str((lifecycle or {}).get("repo") or "pilotmain/aethos")
    project = str((lifecycle or {}).get("project") or "").strip()
    environment = str((lifecycle or {}).get("environment") or "").strip()
    if project and environment:
        plan_cmd = f"`create railway deployment plan for {repo} in {project} / {environment}`"
    else:
        plan_cmd = f"`create railway deployment plan for {repo} in pilotos / production`"
    lead = (
        "Railway readiness has passed, but no deployment plan has been created yet."
        if for_simulator
        else "Readiness exists, but no deployment plan has been created yet."
    )
    return "\n".join(
        [
            lead,
            "",
            "Next step:",
            plan_cmd,
            "",
            "No mutation has been performed.",
        ]
    )


def force_materialize_latest_global_lifecycle(*, session_id: str) -> dict[str, Any]:
    """Load latest global lifecycle and materialize into the current session."""
    record, diag = load_best_global_lifecycle_record()
    if not record:
        return {"ok": False, **diag}
    result = materialize_lifecycle_to_session(session_id=session_id, lifecycle=record)
    if diag.get("entry"):
        result["entry"] = diag["entry"]
    return result


def format_global_lifecycle_entry_lines(entries: list[dict[str, Any]]) -> list[str]:
    lines: list[str] = []
    for idx, entry in enumerate(entries[:5], start=1):
        lines.extend(
            [
                f"Entry {idx}:",
                f"- lifecycle_id: `{entry.get('lifecycle_id') or '—'}`",
                f"- repo: `{entry.get('repo') or '—'}`",
                f"- project/environment: `{entry.get('project') or '—'}` / `{entry.get('environment') or '—'}`",
                f"- stage: {entry.get('stage') or '—'}",
                f"- index file path: `{entry.get('index_file_path') or '—'}`",
                f"- lifecycle file path: `{entry.get('lifecycle_file_path') or entry.get('file_path') or '—'}`",
                f"- lifecycle file exists: **{'yes' if entry.get('file_exists') else 'no'}**",
                f"- lifecycle file readable: **{'yes' if entry.get('readable') else 'no'}**",
                f"- plan snapshot present: **{'yes' if entry.get('plan_snapshot_present') else 'no'}**",
                f"- preflight snapshot present: **{'yes' if entry.get('preflight_snapshot_present') else 'no'}**",
                f"- simulation snapshot present: **{'yes' if entry.get('simulation_snapshot_present') else 'no'}**",
                f"- last updated: {entry.get('updated_at') or '—'}",
                f"- materialization status: {entry.get('materialization_status') or '—'}",
            ]
        )
        if entry.get("materialization_status") == "readiness_only" or entry.get("readiness_only"):
            lines.append("- lifecycle kind: **readiness-only (not a deployment plan)**")
        if entry.get("parse_error"):
            lines.append(f"- parse error: {entry['parse_error']}")
        lines.append("")
    return lines


def global_lifecycle_index_has_entries() -> bool:
    index = inspect_global_lifecycle_index()
    return bool(index.get("exists") and index.get("readable") and int(index.get("entries") or 0) > 0)
