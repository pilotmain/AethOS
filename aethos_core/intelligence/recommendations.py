# SPDX-License-Identifier: Apache-2.0
"""Governed recommendation queue — observe and recommend, never auto-execute."""

from __future__ import annotations

import json
from time import time
from typing import Any
from uuid import uuid4

from aethos_core.agents.runtime.paths import agent_artifacts_root
from aethos_core.intelligence.confidence_authority import score_recommendation_confidence


def _store_path():
    return agent_artifacts_root() / "operational_recommendations.json"


def _load() -> dict[str, Any]:
    path = _store_path()
    if not path.is_file():
        return {"recommendations": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"recommendations": {}}


def _save(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def generate_recommendations_from_anomalies(
    anomalies: list[dict[str, Any]],
    *,
    telemetry_quality: str = "medium",
) -> list[dict[str, Any]]:
    """Create governed recommendations — approval required for mutations."""
    created: list[dict[str, Any]] = []
    for anomaly in anomalies:
        rec = _recommendation_from_anomaly(anomaly, telemetry_quality=telemetry_quality)
        if rec and _upsert_recommendation(rec):
            created.append(rec)
    return created


def _recommendation_from_anomaly(anomaly: dict[str, Any], *, telemetry_quality: str) -> dict[str, Any]:
    action = str(anomaly.get("recommended_action") or "Review in Mission Control")
    approval_required = _approval_required(action)
    confidence = score_recommendation_confidence(
        anomaly_confidence=float(anomaly.get("confidence") or 0.7),
        telemetry_quality=telemetry_quality,
    )
    return {
        "recommendation_id": f"rec-{uuid4().hex[:12]}",
        "anomaly_id": anomaly.get("anomaly_id"),
        "severity": anomaly.get("severity") or "medium",
        "confidence": confidence,
        "title": _title_for_anomaly(anomaly),
        "observed": list(anomaly.get("evidence") or [])[:5],
        "related_systems": list(anomaly.get("related_systems") or []),
        "suggested_action": action,
        "approval_required": approval_required,
        "status": "active",
        "kind": anomaly.get("kind"),
        "created_at": time(),
        "snoozed_until": None,
        "dismissed": False,
        "preflight_id": None,
        "autonomous_execution_blocked": True,
    }


def _title_for_anomaly(anomaly: dict[str, Any]) -> str:
    kind = str(anomaly.get("kind") or "operational").replace("_", " ")
    return f"Operational recommendation: {kind}"


def _approval_required(action: str) -> bool:
    lower = action.lower()
    if "preflight" in lower or "patch" in lower or "mutation" in lower or "modernization" in lower:
        return True
    if "inspect" in lower or "review" in lower or "capture" in lower or "diagnostic" in lower:
        return False
    return "engineering" in lower


def _upsert_recommendation(rec: dict[str, Any]) -> bool:
    data = _load()
    recs = dict(data.get("recommendations") or {})
    fingerprint = f"{rec.get('kind')}:{rec.get('suggested_action')}"
    for existing in recs.values():
        if existing.get("status") == "active" and not existing.get("dismissed"):
            if f"{existing.get('kind')}:{existing.get('suggested_action')}" == fingerprint:
                return False
    recs[str(rec["recommendation_id"])] = rec
    data["recommendations"] = recs
    data["updated_at"] = time()
    _save(data)
    return True


def list_recommendations(*, include_snoozed: bool = False, limit: int = 30) -> list[dict[str, Any]]:
    data = _load()
    now = time()
    rows = list((data.get("recommendations") or {}).values())
    out: list[dict[str, Any]] = []
    for row in rows:
        if row.get("dismissed"):
            continue
        if row.get("status") == "snoozed" and not include_snoozed:
            if float(row.get("snoozed_until") or 0) > now:
                continue
            row["status"] = "active"
        out.append(row)
    out.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return out[:limit]


def get_recommendation(recommendation_id: str) -> dict[str, Any] | None:
    return (_load().get("recommendations") or {}).get(recommendation_id)


def dismiss_recommendation(recommendation_id: str) -> dict[str, Any]:
    row = get_recommendation(recommendation_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    row["dismissed"] = True
    row["status"] = "dismissed"
    row["updated_at"] = time()
    _update_row(recommendation_id, row)
    return {"ok": True, "recommendation": row}


def snooze_recommendation(recommendation_id: str, *, hours: float = 4.0) -> dict[str, Any]:
    row = get_recommendation(recommendation_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    row["status"] = "snoozed"
    row["snoozed_until"] = time() + hours * 3600
    row["updated_at"] = time()
    _update_row(recommendation_id, row)
    return {"ok": True, "recommendation": row}


def generate_preflight_from_recommendation(
    recommendation_id: str,
    *,
    repo_hint: str = "aethos",
) -> dict[str, Any]:
    """Trigger governed engineering preflight — still requires separate approval."""
    row = get_recommendation(recommendation_id)
    if not row:
        return {"ok": False, "error": "not_found"}
    if not row.get("approval_required"):
        return {"ok": False, "error": "approval_not_applicable", "detail": "Recommendation is readonly-only."}

    from aethos_core.engineering.governance.engineering_preflight import run_and_record_engineering_preflight
    from aethos_core.local_workspace.readonly.actions import _repo_from_hint

    user_request = _preflight_prompt_for_recommendation(row)
    repo = _repo_from_hint(repo_hint, session_id="operational_runtime")
    preflight = run_and_record_engineering_preflight(
        user_request=user_request,
        repo=repo,
        workspace_hint=repo_hint,
        session_id="operational_runtime",
        source="reality_loop_recommendation",
    )
    row["preflight_id"] = preflight.get("preflight_id")
    row["status"] = "preflight_generated"
    row["updated_at"] = time()
    _update_row(recommendation_id, row)
    return {"ok": True, "recommendation": row, "preflight": preflight}


def _preflight_prompt_for_recommendation(row: dict[str, Any]) -> str:
    kind = str(row.get("kind") or "")
    if "workflow" in kind:
        return "Fix the GitHub workflow rerun issue in AethOS"
    if "dependency" in kind:
        return "Prepare migration patch for Next.js 16 compatibility"
    if "deployment" in kind:
        return "Create a governed patch proposal for Railway deployment diagnostics"
    return f"Governed engineering preflight: {row.get('title') or kind}"


def _update_row(recommendation_id: str, row: dict[str, Any]) -> None:
    data = _load()
    recs = dict(data.get("recommendations") or {})
    recs[recommendation_id] = row
    data["recommendations"] = recs
    data["updated_at"] = time()
    _save(data)


def clear_recommendations_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
