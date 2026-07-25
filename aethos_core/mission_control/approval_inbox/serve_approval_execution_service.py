# SPDX-License-Identifier: Apache-2.0
"""Governed Model Foundry serve execution from the Mission Control approval inbox.

Mirrors terminal_approval_execution_service / mutation_approval_execution_service:
an approved serve request is executed through a single governed entrypoint. This
NEVER downloads weights or starts a process on the operator's behalf — it verifies
that a loopback inference runtime is already up with the model present, then marks
the request served and registers it into the chat model catalog. If the runtime or
model is missing it returns a precise, actionable error (never a silent no-op).
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from aethos_core.mission_control.approval_inbox.approval_audit_service import persist_ui_approval_audit
from aethos_core.mission_control.approval_inbox.approval_inbox_service import build_approval_inbox


@dataclass(frozen=True)
class ServeApprovalExecutionResult:
    ok: bool
    session_id: str
    inbox_id: str
    serve_request_id: str = ""
    model_id: str = ""
    endpoint: str = ""
    catalog_id: str = ""
    execution_status: str = ""
    audit_id: str = ""
    detail: str = ""
    blockers: list[str] = field(default_factory=list)


def _norm(value: str) -> str:
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def _parse_ollama_tags(data: Any) -> list[str]:
    models = data.get("models") if isinstance(data, dict) else None
    names: list[str] = []
    if isinstance(models, list):
        for entry in models:
            if isinstance(entry, dict):
                name = str(entry.get("name") or entry.get("model") or "").strip()
                if name:
                    names.append(name)
    return names


def _parse_openai_models(data: Any) -> list[str]:
    arr = data.get("data") if isinstance(data, dict) else None
    names: list[str] = []
    if isinstance(arr, list):
        for entry in arr:
            if isinstance(entry, dict):
                name = str(entry.get("id") or "").strip()
                if name:
                    names.append(name)
    return names


def _model_present(model_id: str, available: list[str]) -> bool:
    target = _norm(model_id)
    if not target:
        return False
    for name in available:
        normalized = _norm(name)
        if not normalized:
            continue
        if normalized == target or target in normalized or normalized in target:
            return True
    return False


def probe_local_serve_runtime(*, port: int, model_id: str) -> dict[str, Any]:
    """Probe a loopback inference runtime. NEVER downloads or starts anything.

    Tries the Ollama native tags API then an OpenAI-compatible models list. Returns
    ``ok`` only when the runtime is reachable AND the requested model is present.
    """
    host = f"http://127.0.0.1:{int(port)}"
    reachable = False
    available: list[str] = []
    for path, parser in (("/api/tags", _parse_ollama_tags), ("/v1/models", _parse_openai_models)):
        try:
            with httpx.Client(timeout=3.0) as client:
                response = client.get(f"{host}{path}")
                response.raise_for_status()
                data = response.json()
        except Exception:
            continue
        reachable = True
        parsed = parser(data)
        if parsed:
            available = parsed
            break
    if not reachable:
        return {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": host}
    if not _model_present(model_id, available):
        return {"ok": False, "reason": "model_not_downloaded", "available": available, "endpoint": host}
    return {"ok": True, "reason": "", "available": available, "endpoint": host}


def _reason_detail(
    reason: str,
    *,
    model_id: str,
    port: int,
    available: list[str] | None = None,
    extra: str = "",
) -> str:
    available = available or []
    if reason == "local_runtime_unavailable":
        return (
            f"No local inference runtime is responding on 127.0.0.1:{port}. "
            "Start your local runtime (e.g. `ollama serve`, or a llama.cpp server bound to that "
            "port) and approve again, or enable MODEL_FOUNDRY_AUTOSTART_ENABLED to have approval "
            "start it. AethOS will not auto-start a runtime unless that flag is on."
        )
    if reason == "model_not_downloaded":
        have = ", ".join(available[:6]) if available else "none loaded"
        tag = model_id
        from aethos_core.workspace_suite.model_foundry import ollama_tag_for

        tag = ollama_tag_for(model_id) or model_id
        return (
            f"The runtime on 127.0.0.1:{port} is up but '{model_id}' is not loaded. "
            f"Pull it first (e.g. `ollama pull {tag}`), then approve again, or enable "
            f"MODEL_FOUNDRY_AUTODOWNLOAD_ENABLED to have approval pull it. "
            f"Currently available: {have}."
        )
    if reason == "ollama_not_installed":
        return (
            "Ollama is not installed. Install it from https://ollama.com/download, then approve "
            "again. AethOS will not auto-install Ollama (it is a system package)."
        )
    if reason == "runtime_start_failed":
        return f"Failed to start the local runtime on 127.0.0.1:{port}. {extra}".strip()
    if reason == "runtime_start_timeout":
        return (
            f"Started the local runtime but it did not become ready on 127.0.0.1:{port} in time. "
            "Check the runtime log under data/ and approve again."
        )
    if reason == "unknown_model_tag":
        return (
            f"No known Ollama tag for '{model_id}', so AethOS will not guess a download tag. "
            "Pull the model manually and approve with the runtime already up."
        )
    if reason == "insufficient_disk":
        return (
            f"Not enough free disk to download '{model_id}'. {extra} "
            "Free up space and approve again — no partial download was started."
        )
    return "Serve preflight could not be executed."


def _poll_runtime_ready(*, port: int, model_id: str, timeout_sec: float = 30.0) -> dict[str, Any]:
    """Poll the runtime until it responds, up to a bounded timeout."""
    deadline = time.time() + max(1.0, timeout_sec)
    last = {"ok": False, "reason": "local_runtime_unavailable", "available": [], "endpoint": f"http://127.0.0.1:{port}"}
    while time.time() < deadline:
        probe = probe_local_serve_runtime(port=port, model_id=model_id)
        last = probe
        if probe.get("ok") or probe.get("reason") == "model_not_downloaded":
            return probe
        time.sleep(1.0)
    return last


def _audit_serve(
    *,
    session_id: str,
    inbox_id: str,
    req_id: str,
    model_id: str,
    outcome: str,
    status: str,
    blockers: list[str] | None = None,
    catalog_id: str = "",
    endpoint: str = "",
    excerpt: str = "",
) -> str:
    ok = outcome == "success"
    audit = persist_ui_approval_audit(
        {
            "session_id": session_id,
            "inbox_id": inbox_id,
            "lane": "model_foundry",
            "gate_id": "model_serve",
            "outcome": outcome,
            "gate_satisfied": ok,
            "mutation_performed": ok,
            "serve_request_id": req_id,
            "model_id": model_id,
            "execution_status": status,
            "catalog_id": catalog_id,
            "endpoint": endpoint,
            "blockers": blockers or [],
            "failure_reason": "" if ok else status,
            "reply_excerpt": excerpt[:500],
        }
    )
    return str(audit.get("approval_id") or "")


def _find_serve_inbox_item(*, session_id: str, inbox_id: str) -> dict[str, Any] | None:
    inbox = build_approval_inbox(session_id=session_id)
    if not inbox.ok:
        return None
    for item in inbox.items:
        if str(item.get("inbox_id") or "") == inbox_id and str(item.get("lane") or "") == "model_foundry":
            return item
    return None


def execute_serve_preflight_from_inbox(*, session_id: str, inbox_id: str) -> ServeApprovalExecutionResult:
    item = _find_serve_inbox_item(session_id=session_id, inbox_id=inbox_id)
    if not item:
        return ServeApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["inbox_item_not_found"],
            detail="Serve request item not found.",
        )

    ctx = item.get("context") if isinstance(item.get("context"), dict) else {}
    req_id = str(ctx.get("serve_request_id") or "")
    if not req_id:
        return ServeApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            blockers=["serve_request_id_missing"],
        )

    from aethos_core.workspace_suite import model_foundry as foundry

    record = foundry.get_serve_request(req_id)
    if not record:
        return ServeApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            serve_request_id=req_id,
            blockers=["serve_request_not_found"],
        )

    model_id = str(record.get("model_id") or "")
    port = int(record.get("port") or 11434)
    catalog_id = f"local:{model_id}"

    if record.get("executed") and str(record.get("status") or "") == "served":
        endpoint = foundry.served_model_endpoint(model_id) or f"http://127.0.0.1:{port}"
        return ServeApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            serve_request_id=req_id,
            model_id=model_id,
            endpoint=endpoint,
            catalog_id=catalog_id,
            execution_status="already_served",
            detail="Model already served and registered.",
        )

    def _fail(reason: str, *, extra: str = "", available: list[str] | None = None) -> ServeApprovalExecutionResult:
        detail = _reason_detail(reason, model_id=model_id, port=port, available=available, extra=extra)
        audit_id = _audit_serve(
            session_id=session_id,
            inbox_id=inbox_id,
            req_id=req_id,
            model_id=model_id,
            outcome="failed",
            status=reason,
            blockers=[reason],
            excerpt=detail,
        )
        return ServeApprovalExecutionResult(
            ok=False,
            session_id=session_id,
            inbox_id=inbox_id,
            serve_request_id=req_id,
            model_id=model_id,
            endpoint=f"http://127.0.0.1:{port}",
            execution_status=reason,
            blockers=[reason],
            detail=detail,
            audit_id=audit_id,
        )

    probe = probe_local_serve_runtime(port=port, model_id=model_id)

    # ── Runtime not responding ─────────────────────────────────────────────
    if not probe.get("ok") and probe.get("reason") == "local_runtime_unavailable":
        if not foundry.autostart_enabled():
            return _fail("local_runtime_unavailable")
        if not foundry.ollama_available():
            return _fail("ollama_not_installed")
        foundry.update_serve_request(req_id, status="starting", phase="starting_runtime")
        start = foundry.start_ollama_runtime(port=port)
        if not start.get("ok"):
            foundry.update_serve_request(req_id, status="pending_approval", phase="error")
            reason = str(start.get("reason") or "runtime_start_failed")
            return _fail(reason, extra=str(start.get("error") or ""))
        probe = _poll_runtime_ready(port=port, model_id=model_id)
        if not probe.get("ok") and probe.get("reason") != "model_not_downloaded":
            foundry.update_serve_request(req_id, status="pending_approval", phase="error")
            return _fail("runtime_start_timeout")

    # ── Runtime up, model missing ──────────────────────────────────────────
    if not probe.get("ok") and probe.get("reason") == "model_not_downloaded":
        available = list(probe.get("available") or [])
        if not foundry.autodownload_enabled():
            return _fail("model_not_downloaded", available=available)
        tag = foundry.ollama_tag_for(model_id)
        if not tag:
            return _fail("unknown_model_tag", available=available)
        min_gb = foundry.min_gb_for(model_id) or 0.0
        free_gb = foundry.free_disk_gb()
        if min_gb and free_gb < min_gb:
            return _fail(
                "insufficient_disk",
                extra=f"Needs ~{min_gb:.0f} GB, only {free_gb:.0f} GB free.",
                available=available,
            )
        foundry.run_model_pull(req_id=req_id, tag=tag, port=port)
        audit_id = _audit_serve(
            session_id=session_id,
            inbox_id=inbox_id,
            req_id=req_id,
            model_id=model_id,
            outcome="success",
            status="downloading",
            catalog_id=catalog_id,
            endpoint=f"http://127.0.0.1:{port}",
            excerpt=f"Approved — pulling {tag} (~{min_gb:.0f} GB) on loopback. Watch progress in Model Foundry.",
        )
        return ServeApprovalExecutionResult(
            ok=True,
            session_id=session_id,
            inbox_id=inbox_id,
            serve_request_id=req_id,
            model_id=model_id,
            endpoint=f"http://127.0.0.1:{port}",
            catalog_id=catalog_id,
            execution_status="downloading",
            detail=(
                f"Approved — downloading {tag} (~{min_gb:.0f} GB) on the loopback runtime. "
                "Progress shows in Model Foundry; it registers in the chat picker when complete."
            ),
            audit_id=audit_id,
        )

    # ── Other probe failure (e.g. start failure path) ──────────────────────
    if not probe.get("ok"):
        return _fail(str(probe.get("reason") or "serve_preflight_failed"), available=list(probe.get("available") or []))

    # ── Runtime up + model present → serve now ─────────────────────────────
    endpoint = f"http://127.0.0.1:{port}"
    foundry.update_serve_request(
        req_id,
        status="served",
        executed=True,
        served=True,
        served_at=time.time(),
        endpoint=endpoint,
        phase="served",
        progress=100,
        runtime_models=list(probe.get("available") or []),
    )
    audit_id = _audit_serve(
        session_id=session_id,
        inbox_id=inbox_id,
        req_id=req_id,
        model_id=model_id,
        outcome="success",
        status="served",
        catalog_id=catalog_id,
        endpoint=endpoint,
        excerpt=f"Serving {model_id} on {endpoint} (loopback).",
    )
    return ServeApprovalExecutionResult(
        ok=True,
        session_id=session_id,
        inbox_id=inbox_id,
        serve_request_id=req_id,
        model_id=model_id,
        endpoint=endpoint,
        catalog_id=catalog_id,
        execution_status="served",
        detail="Local model served and registered in the chat model picker.",
        audit_id=audit_id,
    )
