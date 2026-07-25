# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from aethos_core.api.event_poll import safe_event_poll
from aethos_core.browser.runtime.browser_artifacts import (
    artifact_file_path,
    get_artifact,
    list_artifacts,
)
from aethos_core.browser.runtime.browser_audit import _audit_path
from aethos_core.browser.runtime.browser_policy import evaluate_capture_request, normalize_capture_type
from aethos_core.browser.runtime.browser_runtime import run_browser_evidence_capture
from aethos_core.runtime.browser_capability import (
    get_browser_capability_status,
    get_browser_runtime_diagnostics,
)
from aethos_core.runtime.browser_executor import get_browser_executor_status
from aethos_core.runtime.browser_jobs import (
    BROWSER_ACTION_TYPES,
    infer_browser_intent_from_text,
    propose_browser_job_record,
)
from aethos_core.runtime.browser_profile_store import browser_profile_store, store_diagnostics
from aethos_core.runtime.browser_session import browser_session_store
from aethos_core.runtime.vercel_readonly_inspector import run_profile_session_check

router = APIRouter(tags=["browser"])


class ProposeBrowserJobIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    source: str = Field(default="api", max_length=32)
    session_id: str = Field(default="default", max_length=64)


class SaveBrowserProfileIn(BaseModel):
    session_id: str = Field(min_length=1, max_length=64)
    site: str | None = Field(default=None, max_length=128)
    persistence_mode: str = Field(
        default="use_once",
        description="use_once | persistent | expires_7d | expires_30d",
    )


class BrowserCaptureIn(BaseModel):
    url: str = Field(min_length=1, max_length=2000)
    capture_type: str = Field(default="screenshot", max_length=32)
    session_id: str = Field(default="default", max_length=64)
    approved: bool = Field(default=True)
    user_request: str = Field(default="", max_length=2000)


@router.get("/browser/status")
def get_browser_status() -> dict[str, Any]:
    status = get_browser_capability_status()
    status["executor_status"] = get_browser_executor_status()
    return status


@router.get("/browser/executor/status")
def get_browser_executor_status_route() -> dict[str, Any]:
    return get_browser_executor_status()


@router.get("/browser/diagnostics")
def get_browser_diagnostics() -> dict[str, Any]:
    return {"diagnostics": get_browser_runtime_diagnostics()}


@router.get("/browser/sessions/events")
def get_browser_session_events(
    ids: str | None = None,
    session_id: str | None = None,
    chat_session_id: str | None = None,
    since: float = 0.0,
    since_event_id: str | None = None,
) -> dict[str, Any]:
    session_ids = [x.strip() for x in (ids or "").split(",") if x.strip()] or None
    sid = (session_id or "").strip()[:64] or None
    csid = (chat_session_id or "").strip()[:64] or None
    cursor = (since_event_id or "").strip()[:128] or None

    def _fetch() -> list[dict[str, Any]]:
        return browser_session_store.list_events(
            session_ids=session_ids,
            session_id=sid,
            chat_session_id=csid,
            since=since,
            since_event_id=cursor,
        )

    return safe_event_poll(_fetch)


@router.get("/browser/sessions")
def list_browser_sessions() -> dict[str, Any]:
    sessions = [s.to_dict() for s in browser_session_store.list_all()]
    active = browser_session_store.active_sessions()
    return {
        "sessions": sessions,
        "count": len(sessions),
        "active_session": active[0].to_dict() if active else None,
        "active_sessions": [s.to_dict() for s in active],
        "active_session_count": browser_session_store.active_count(),
    }


@router.get("/browser/sessions/{session_id}")
def get_browser_session(session_id: str) -> dict[str, Any]:
    session = browser_session_store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Browser session not found")
    events = browser_session_store.list_events(session_ids=[session_id])
    return {"session": session.to_dict(), "events": events}


@router.post("/browser/sessions/{session_id}/close")
def post_close_browser_session(session_id: str) -> dict[str, Any]:
    try:
        session = browser_session_store.close(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Browser session not found") from exc
    return {"session": session.to_dict()}


@router.post("/browser/sessions/{session_id}/cancel")
def post_cancel_browser_session(session_id: str) -> dict[str, Any]:
    try:
        session = browser_session_store.cancel(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Browser session not found") from exc
    return {"session": session.to_dict()}


@router.post("/browser/sessions/{session_id}/terminate")
def post_terminate_browser_session(session_id: str) -> dict[str, Any]:
    try:
        session = browser_session_store.terminate(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Browser session not found") from exc
    return {"session": session.to_dict()}


@router.get("/browser/profiles")
def list_browser_profiles() -> dict[str, Any]:
    profiles = [p.to_public_dict() for p in browser_profile_store.list_all(refresh=True)]
    active = [p for p in profiles if p.get("status") == "active"]
    diag = store_diagnostics()
    return {
        "profiles": profiles,
        "count": len(profiles),
        "active_count": len(active),
        "profile_store_path": diag["profile_store_path"],
        "store_diagnostics": diag,
    }


@router.post("/browser/profiles/save")
def post_save_browser_profile(body: SaveBrowserProfileIn) -> dict[str, Any]:
    from aethos_core.runtime.browser_profile_errors import BrowserProfileSaveError

    sid = (body.session_id or "").strip()
    if not sid:
        raise HTTPException(
            status_code=400,
            detail={
                "ok": False,
                "code": "MISSING_SESSION_ID",
                "detail": "Save failed — missing session id.",
            },
        )
    try:
        mode = (body.persistence_mode or "use_once").strip().lower()
        profile = browser_session_store.save_profile_from_session(sid, persistence_mode=mode)
    except BrowserProfileSaveError as exc:
        raise HTTPException(status_code=exc.http_status, detail=exc.to_dict()) from exc
    except TimeoutError as exc:
        raise HTTPException(
            status_code=504,
            detail={
                "ok": False,
                "code": "SAVE_TIMEOUT",
                "detail": "Save failed — browser operation timed out.",
            },
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail={
                "ok": False,
                "code": "SESSION_NOT_FOUND",
                "detail": "Save failed — browser session not found.",
            },
        ) from exc
    diag = store_diagnostics()
    return {
        "ok": True,
        "profile": profile,
        "saved": True,
        "profile_store_path": diag["profile_store_path"],
        "profile_count": diag["profile_count"],
    }


@router.post("/browser/profiles/{profile_id}/forget")
def post_forget_browser_profile(profile_id: str) -> dict[str, Any]:
    if not browser_profile_store.forget(profile_id):
        raise HTTPException(status_code=404, detail="Browser profile not found")
    return {"forgotten": True, "profile_id": profile_id}


@router.post("/browser/profiles/{profile_id}/test")
def post_test_browser_profile(profile_id: str) -> dict[str, Any]:
    try:
        result = run_profile_session_check(profile_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Browser profile not found") from exc
    return {"result": result}


@router.post("/browser/jobs/propose")
def post_propose_browser_job(body: ProposeBrowserJobIn) -> dict[str, Any]:
    intent = infer_browser_intent_from_text(body.message)
    if intent is None:
        raise HTTPException(
            status_code=422,
            detail="Could not infer a browser job from message. Try browser status, navigation, or login notice phrasing.",
        )
    action_type, params = intent
    if action_type not in BROWSER_ACTION_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported browser action: {action_type}")
    try:
        action = propose_browser_job_record(
            action_type,
            params,
            source=body.source,
            session_id=body.session_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {"action": action.to_dict(), "browser_job_type": action_type}


@router.post("/browser/capture")
def post_browser_capture(body: BrowserCaptureIn) -> dict[str, Any]:
    capture_type = normalize_capture_type(body.capture_type)
    policy = evaluate_capture_request(
        url=body.url.strip(),
        capture_type=capture_type,
        user_request=body.user_request or f"capture {capture_type} of {body.url}",
        approved=body.approved,
    )
    if not policy.get("allowed"):
        return {
            "ok": False,
            "blocked": True,
            "policy": policy,
        }
    result = run_browser_evidence_capture(
        url=body.url.strip(),
        capture_type=capture_type,
        session_id=body.session_id,
        user_request=body.user_request,
        approved=body.approved,
    )
    return {"ok": result.get("ok", False), **result}


@router.get("/browser/artifacts")
def get_browser_artifacts(limit: int = 50) -> dict[str, Any]:
    items = list_artifacts(limit=min(max(limit, 1), 200))
    return {"artifacts": items, "count": len(items)}


@router.get("/browser/artifacts/{artifact_id}")
def get_browser_artifact_detail(artifact_id: str) -> dict[str, Any]:
    row = get_artifact(artifact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Browser artifact not found")
    return {"artifact": row}


@router.get("/browser/artifacts/{artifact_id}/file")
def get_browser_artifact_file(artifact_id: str) -> FileResponse:
    row = get_artifact(artifact_id)
    if row is None:
        raise HTTPException(status_code=404, detail="artifact_not_found")
    if not row.get("file_exists"):
        reason = "artifact_file_missing"
        if not row.get("file_path"):
            reason = "artifact_has_no_file_path"
        raise HTTPException(status_code=404, detail=reason)
    path = artifact_file_path(row)
    if path is None or not path.is_file() or path.stat().st_size <= 0:
        raise HTTPException(status_code=404, detail="artifact_file_missing_or_empty")
    media = str(row.get("media_type") or "application/octet-stream")
    return FileResponse(path, media_type=media, filename=path.name)


@router.get("/browser/evidence/audit")
def get_browser_evidence_audit(limit: int = 100) -> dict[str, Any]:
    path = _audit_path()
    if not path.is_file():
        return {"events": [], "count": 0}
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    events: list[dict[str, Any]] = []

    for line in reversed(lines[-limit:]):
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return {"events": events, "count": len(events)}
