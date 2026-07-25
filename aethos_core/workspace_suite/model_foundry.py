# SPDX-License-Identifier: Apache-2.0
"""Workspace suite — Model Foundry tab (handoff §8).

Scans local hardware (readonly), recommends open models by VRAM-aware fit score,
and proposes serving a model. Local only: serving binds loopback by default and is
GOVERNED — create_serve_preflight records the request and never starts a server or
downloads weights on its own. Gated by MODEL_FOUNDRY_ENABLED, default off.
"""

from __future__ import annotations

import json
import os
import platform
import re
import secrets
import shutil
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Any

# Explicit foundry-catalog-id → Ollama pull tag map. Unknown ids return None so
# auto-download never guesses a tag. Keys match _MODEL_CATALOG ids exactly.
OLLAMA_TAGS: dict[str, str] = {
    "qwen2.5-0.5b": "qwen2.5:0.5b",
    "phi-3-mini": "phi3:mini",
    "llama-3.2-3b": "llama3.2:3b",
    "mistral-7b": "mistral:7b",
    "llama-3.1-8b": "llama3.1:8b",
    "qwen2.5-14b": "qwen2.5:14b",
    "gemma-2-27b": "gemma2:27b",
    "llama-3.1-70b": "llama3.1:70b",
}

_PCT_RE = re.compile(r"(\d{1,3})%")

# Curated open-model families with approximate quantized (Q4) memory footprints in GB.
# Generic open weights only — no source-project names. Footprints are conservative
# guidance for fit scoring, not exact requirements.
_MODEL_CATALOG: list[dict[str, Any]] = [
    {"id": "qwen2.5-0.5b", "label": "Qwen2.5 0.5B", "params_b": 0.5, "min_gb": 1, "quant": "Q4"},
    {"id": "phi-3-mini", "label": "Phi-3 Mini (3.8B)", "params_b": 3.8, "min_gb": 4, "quant": "Q4"},
    {"id": "llama-3.2-3b", "label": "Llama 3.2 3B", "params_b": 3.0, "min_gb": 3, "quant": "Q4"},
    {"id": "mistral-7b", "label": "Mistral 7B", "params_b": 7.0, "min_gb": 6, "quant": "Q4"},
    {"id": "llama-3.1-8b", "label": "Llama 3.1 8B", "params_b": 8.0, "min_gb": 7, "quant": "Q4"},
    {"id": "qwen2.5-14b", "label": "Qwen2.5 14B", "params_b": 14.0, "min_gb": 11, "quant": "Q4"},
    {"id": "gemma-2-27b", "label": "Gemma 2 27B", "params_b": 27.0, "min_gb": 20, "quant": "Q4"},
    {"id": "llama-3.1-70b", "label": "Llama 3.1 70B", "params_b": 70.0, "min_gb": 42, "quant": "Q4"},
]


def _store_root() -> Path:
    from aethos_core.config import get_settings

    raw = (
        getattr(get_settings(), "workspace_suite_store_dir", "data/workspace_suite")
        or "data/workspace_suite"
    ).strip()
    return Path(raw)


def _store_path() -> Path:
    return _store_root() / "model_foundry.json"


def _enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "model_foundry_enabled", False))


def _detect_total_ram_bytes(system: str) -> int:
    """Total physical RAM in bytes; 0 only when every method genuinely fails.

    psutil first (now a hard dependency), then OS-native fallbacks so a missing
    or broken psutil never silently reports 0 RAM (which made every model 0% no).
    """
    try:
        import psutil

        total = int(psutil.virtual_memory().total)
        if total > 0:
            return total
    except Exception:  # pragma: no cover - fall through to OS-native probes
        pass
    try:
        if system == "Darwin":
            out = subprocess.run(
                ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=3
            )
            if out.returncode == 0 and out.stdout.strip().isdigit():
                return int(out.stdout.strip())
        elif system == "Linux":
            for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    # MemTotal is reported in kB.
                    return int(line.split()[1]) * 1024
    except Exception:  # pragma: no cover - defensive
        pass
    return 0


def _detect_cpu_count(system: str) -> int:
    count = os.cpu_count() or 0
    if count > 0:
        return count
    try:
        if system == "Darwin":
            out = subprocess.run(
                ["sysctl", "-n", "hw.ncpu"], capture_output=True, text=True, timeout=3
            )
            if out.returncode == 0 and out.stdout.strip().isdigit():
                return int(out.stdout.strip())
    except Exception:  # pragma: no cover - defensive
        pass
    return 0


def scan_hardware() -> dict[str, Any]:
    """Readonly local hardware scan. Apple Silicon uses unified memory for VRAM."""
    if not _enabled():
        return {"ok": False, "error": "model_foundry_disabled"}
    arch = platform.machine()
    system = platform.system()
    total_ram_bytes = _detect_total_ram_bytes(system)
    cpu_count = _detect_cpu_count(system)

    if total_ram_bytes <= 0:
        # Never report 0 as a real value or mark every model "no" — be honest that
        # detection failed so the UI can say so instead of showing a misleading list.
        return {
            "ok": True,
            "system": system,
            "arch": arch,
            "cpu_count": cpu_count,
            "detection_unavailable": True,
            "total_ram_gb": None,
            "unified_memory": system == "Darwin" and arch == "arm64",
            "usable_vram_gb": None,
        }

    total_ram_gb = round(total_ram_bytes / (1024**3), 1)
    unified = system == "Darwin" and arch == "arm64"
    # On unified-memory machines the GPU shares system RAM; treat ~70% as usable VRAM.
    usable_vram_gb = round(total_ram_gb * (0.7 if unified else 0.5), 1)
    return {
        "ok": True,
        "system": system,
        "arch": arch,
        "cpu_count": cpu_count,
        "detection_unavailable": False,
        "total_ram_gb": total_ram_gb,
        "unified_memory": unified,
        "usable_vram_gb": usable_vram_gb,
    }


def _fit_score(min_gb: float, usable_vram_gb: float) -> float:
    if usable_vram_gb <= 0:
        return 0.0
    if min_gb <= 0:
        return 1.0
    headroom = usable_vram_gb / min_gb
    if headroom >= 2.0:
        return 1.0
    if headroom >= 1.0:
        return round(0.6 + 0.4 * ((headroom - 1.0) / 1.0), 2)
    # Below requirement: degrade quickly.
    return round(max(0.0, headroom * 0.5), 2)


def recommend_models() -> dict[str, Any]:
    """Recommend open models by fit score against detected hardware (readonly)."""
    if not _enabled():
        return {"ok": False, "error": "model_foundry_disabled", "models": []}
    hw = scan_hardware()
    if hw.get("detection_unavailable"):
        # Don't render a misleading all-"no" fit list off a bogus 0 — say so.
        return {
            "ok": True,
            "hardware": hw,
            "detection_unavailable": True,
            "model_count": 0,
            "models": [],
        }
    usable = float(hw.get("usable_vram_gb") or 0.0)
    rows: list[dict[str, Any]] = []
    for model in _MODEL_CATALOG:
        score = _fit_score(float(model["min_gb"]), usable)
        rows.append(
            {
                **model,
                "fit_score": score,
                "fits": score >= 0.6,
                "verdict": "great" if score >= 0.9 else "ok" if score >= 0.6 else "tight" if score > 0 else "no",
            }
        )
    rows.sort(key=lambda r: (r["fits"], r["fit_score"], r["params_b"]), reverse=True)
    return {"ok": True, "hardware": hw, "model_count": len(rows), "models": rows}


def _label_for(model_id: str) -> str:
    for m in _MODEL_CATALOG:
        if m["id"] == model_id:
            return str(m["label"])
    return model_id


def _load_store() -> dict[str, Any]:
    path = _store_path()
    try:
        existing = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except (OSError, json.JSONDecodeError):
        existing = {}
    return existing if isinstance(existing, dict) else {}


def _save_store(data: dict[str, Any]) -> None:
    path = _store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = time.time()
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    tmp.replace(path)


def create_serve_preflight(*, model_id: str, port: int = 11434) -> dict[str, Any]:
    """Record a GOVERNED serve request and enqueue it for approval.

    Never starts a server or downloads weights. Binds loopback only by design.
    The persisted record is surfaced as a pending item in the Mission Control
    approval inbox (lane ``model_foundry``); the operator must approve/execute
    serving through the governed path — this function only persists the intent.
    """
    if not _enabled():
        return {"ok": False, "error": "model_foundry_disabled"}
    mid = (model_id or "").strip()
    known = {m["id"] for m in _MODEL_CATALOG}
    if mid not in known:
        return {"ok": False, "error": "unknown_model", "id": mid, "known": sorted(known)}
    norm_port = int(port) if 1024 <= int(port) <= 65535 else 11434
    store = _load_store()
    requests = dict(store.get("serve_requests") or {})
    # De-dupe: repeated Serve clicks for the same model + port should refresh the
    # existing un-executed pending request, not stack identical rows.
    for existing_id, existing in requests.items():
        if not isinstance(existing, dict):
            continue
        if (
            str(existing.get("model_id") or "") == mid
            and int(existing.get("port") or 11434) == norm_port
            and not existing.get("executed")
            and str(existing.get("status") or "") in {"pending_approval", "preflight"}
        ):
            existing["created_at"] = time.time()
            requests[existing_id] = existing
            store["serve_requests"] = requests
            _save_store(store)
            return {
                "ok": True,
                "serve_request": existing,
                "deduped": True,
                "note": "existing pending request refreshed — already awaiting approval in Mission Control → Approvals",
            }
    req_id = f"serve-{secrets.token_hex(5)}"
    record = {
        "id": req_id,
        "model_id": mid,
        "label": _label_for(mid),
        "bind": "127.0.0.1",  # loopback only
        "port": norm_port,
        "status": "pending_approval",  # never auto-served; awaits governed approval
        "executed": False,
        "served": False,
        "requires_approval": True,
        "created_at": time.time(),
    }
    requests[req_id] = record
    store["serve_requests"] = requests
    _save_store(store)
    return {
        "ok": True,
        "serve_request": record,
        "note": "recorded only — pending approval in Mission Control → Approvals; loopback bind",
    }


def list_serve_requests() -> list[dict[str, Any]]:
    """All serve records, newest first (unfiltered; readonly)."""
    requests = _load_store().get("serve_requests") or {}
    if not isinstance(requests, dict):
        return []
    rows = [r for r in requests.values() if isinstance(r, dict)]
    rows.sort(key=lambda r: float(r.get("created_at") or 0.0), reverse=True)
    return rows


def list_pending_serve_requests() -> list[dict[str, Any]]:
    """Serve records awaiting approval (gated by MODEL_FOUNDRY_ENABLED)."""
    if not _enabled():
        return []
    return [
        r
        for r in list_serve_requests()
        if not r.get("executed") and str(r.get("status") or "") in {"pending_approval", "preflight"}
    ]


def get_serve_request(req_id: str) -> dict[str, Any] | None:
    requests = _load_store().get("serve_requests") or {}
    row = requests.get(req_id) if isinstance(requests, dict) else None
    return row if isinstance(row, dict) else None


def update_serve_request(req_id: str, **updates: Any) -> dict[str, Any] | None:
    store = _load_store()
    requests = dict(store.get("serve_requests") or {})
    row = requests.get(req_id)
    if not isinstance(row, dict):
        return None
    merged = {**row, **updates}
    requests[req_id] = merged
    store["serve_requests"] = requests
    _save_store(store)
    return merged


def dismiss_serve_request(req_id: str) -> dict[str, Any]:
    """Remove a pending (un-executed) serve request — clears stacked rows.

    Only un-executed pending/preflight requests can be dismissed; served or
    executed records go through the governed ``stop_serve`` de-escalation instead.
    """
    store = _load_store()
    requests = dict(store.get("serve_requests") or {})
    row = requests.get(req_id)
    if not isinstance(row, dict):
        return {"ok": False, "error": "unknown_request", "id": req_id}
    if row.get("executed") or str(row.get("status") or "") not in {"pending_approval", "preflight"}:
        return {"ok": False, "error": "not_pending", "id": req_id, "status": row.get("status")}
    requests.pop(req_id, None)
    store["serve_requests"] = requests
    _save_store(store)
    return {"ok": True, "dismissed": req_id}


def list_served_models() -> list[dict[str, Any]]:
    """Executed + currently-served serve records (catalog registration source)."""
    if not _enabled():
        return []
    return [
        r
        for r in list_serve_requests()
        if r.get("executed") and str(r.get("status") or "") == "served"
    ]


def _model_key(value: str) -> str:
    """Alphanumeric-only key so `qwen2.5-14b` ↔ `qwen2.5:14b` ↔ `qwen2514b` all match."""
    return "".join(ch for ch in (value or "").lower() if ch.isalnum())


def _serve_record_matches(record: dict[str, Any], model_id: str) -> bool:
    """True when a serve record corresponds to the requested model regardless of id formatting.

    Matches the stored catalog id, the catalog→Ollama tag, and any runtime model names
    the runtime actually reported — so endpoint resolution is robust to id-format drift.
    """
    want = _model_key(model_id)
    if not want:
        return False
    keys: set[str] = set()
    stored = str(record.get("model_id") or "")
    if stored:
        keys.add(_model_key(stored))
        tag = ollama_tag_for(stored)
        if tag:
            keys.add(_model_key(tag))
    req_tag = ollama_tag_for(model_id)
    if req_tag:
        keys.add(_model_key(req_tag))
    for rm in record.get("runtime_models") or []:
        keys.add(_model_key(str(rm)))
    return want in keys


def served_model_endpoint(model_id: str) -> str | None:
    """Loopback endpoint for an actively-served model, if any (id-format tolerant)."""
    mid = (model_id or "").strip()
    if not mid:
        return None
    for r in list_served_models():
        if _serve_record_matches(r, mid):
            endpoint = str(r.get("endpoint") or "").strip()
            return endpoint or f"http://127.0.0.1:{int(r.get('port') or 11434)}"
    return None


def served_model_runtime_name(model_id: str) -> str | None:
    """The actual runtime model name (Ollama tag) for a served model, if known.

    A served Foundry catalog id (`qwen2.5-14b`) must be addressed on the Ollama
    OpenAI-compatible API by its runtime tag (`qwen2.5:14b`). Prefer a runtime model
    the runtime reported; fall back to the catalog→tag map, then the stored id.
    """
    mid = (model_id or "").strip()
    if not mid:
        return None
    want = _model_key(mid)
    for r in list_served_models():
        if not _serve_record_matches(r, mid):
            continue
        runtime = [str(x).strip() for x in (r.get("runtime_models") or []) if str(x).strip()]
        for rm in runtime:
            if _model_key(rm) == want:
                return rm
        tag = ollama_tag_for(str(r.get("model_id") or "")) or ollama_tag_for(mid)
        if tag:
            return tag
        if runtime:
            return runtime[0]
        return str(r.get("model_id") or "") or None
    return None


def stop_serve(*, req_id: str) -> dict[str, Any]:
    """Record a GOVERNED stop. De-escalation: removes the served catalog entry.

    AethOS does not manage the inference process itself — the operator stops the
    local runtime to free the port. This records the governed intent and removes
    the model from the chat picker immediately.
    """
    if not _enabled():
        return {"ok": False, "error": "model_foundry_disabled"}
    if not get_serve_request(req_id):
        return {"ok": False, "error": "serve_request_not_found", "id": req_id}
    updated = update_serve_request(
        req_id, status="stopped", executed=False, served=False, phase="stopped", stopped_at=time.time()
    )
    # Kill the managed runtime only when no other model is still served by it.
    runtime_stopped = False
    if not list_served_models():
        result = stop_managed_runtime()
        runtime_stopped = bool(result.get("stopped"))
    note = "Governed stop recorded; chat picker entry removed."
    note += (
        " Managed runtime process terminated."
        if runtime_stopped
        else " Stop the local runtime process to free the port."
    )
    return {"ok": True, "serve_request": updated, "runtime_stopped": runtime_stopped, "note": note}


def serve_status_payload() -> dict[str, Any]:
    """Live serve-request status for the Foundry panel (readonly)."""
    if not _enabled():
        return {"ok": False, "error": "model_foundry_disabled", "serve_requests": []}
    rows: list[dict[str, Any]] = []
    for r in list_serve_requests():
        rows.append(
            {
                "id": r.get("id"),
                "model_id": r.get("model_id"),
                "label": r.get("label") or _label_for(str(r.get("model_id") or "")),
                "status": r.get("status"),
                "phase": r.get("phase"),
                "progress": r.get("progress"),
                "error": r.get("error"),
                "executed": bool(r.get("executed")),
                "bind": r.get("bind"),
                "port": r.get("port"),
                "endpoint": r.get("endpoint"),
                "created_at": r.get("created_at"),
                "served_at": r.get("served_at"),
                "stopped_at": r.get("stopped_at"),
            }
        )
    return {
        "ok": True,
        "serve_requests": rows,
        "autostart_enabled": autostart_enabled(),
        "autodownload_enabled": autodownload_enabled(),
    }


def ollama_tag_for(model_id: str) -> str | None:
    """Foundry catalog id → Ollama pull tag. Unknown id → None (never guess)."""
    return OLLAMA_TAGS.get((model_id or "").strip())


def min_gb_for(model_id: str) -> float | None:
    for m in _MODEL_CATALOG:
        if m["id"] == model_id:
            return float(m["min_gb"])
    return None


def autostart_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "model_foundry_autostart_enabled", False))


def autodownload_enabled() -> bool:
    from aethos_core.config import get_settings

    return bool(getattr(get_settings(), "model_foundry_autodownload_enabled", False))


def ollama_available() -> bool:
    """True when the `ollama` binary is on PATH. AethOS never auto-installs it."""
    return shutil.which("ollama") is not None


def free_disk_gb(path: str | None = None) -> float:
    target = Path(path or _store_root())
    target.mkdir(parents=True, exist_ok=True)
    try:
        usage = shutil.disk_usage(str(target))
        return round(usage.free / (1024**3), 1)
    except OSError:
        return 0.0


def _runtime_log_path(port: int) -> Path:
    return _store_root() / f"ollama-{int(port)}.log"


def _ollama_env(port: int) -> dict[str, str]:
    return {**os.environ, "OLLAMA_HOST": f"127.0.0.1:{int(port)}"}


def get_managed_runtime() -> dict[str, Any] | None:
    runtime = _load_store().get("runtime")
    return runtime if isinstance(runtime, dict) else None


def start_ollama_runtime(*, port: int = 11434) -> dict[str, Any]:
    """Start a loopback-bound Ollama runtime as a managed background process.

    Never installs Ollama. Returns a structured result; records the PID in the
    foundry store for lifecycle/stop. Loopback only via OLLAMA_HOST.
    """
    if not _enabled():
        return {"ok": False, "reason": "model_foundry_disabled"}
    if not ollama_available():
        return {"ok": False, "reason": "ollama_not_installed"}
    log = _runtime_log_path(port)
    log.parent.mkdir(parents=True, exist_ok=True)
    try:
        log_handle = open(log, "ab")  # noqa: SIM115 - handed to the child process
        try:
            proc = subprocess.Popen(  # noqa: S603,S607 - fixed argv, loopback only
                ["ollama", "serve"],
                stdout=log_handle,
                stderr=log_handle,
                env=_ollama_env(port),
                start_new_session=True,
            )
        finally:
            log_handle.close()
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"ok": False, "reason": "runtime_start_failed", "error": str(exc)}
    store = _load_store()
    store["runtime"] = {
        "pid": proc.pid,
        "port": int(port),
        "started_at": time.time(),
        "log": str(log),
        "managed": True,
    }
    _save_store(store)
    return {"ok": True, "pid": proc.pid, "port": int(port), "log": str(log)}


def stop_managed_runtime() -> dict[str, Any]:
    """Terminate the managed runtime process (if any) by its stored PID."""
    runtime = get_managed_runtime()
    if not runtime:
        return {"ok": True, "stopped": False}
    pid = int(runtime.get("pid") or 0)
    stopped = False
    if pid > 0:
        try:
            os.kill(pid, signal.SIGTERM)
            stopped = True
        except ProcessLookupError:
            stopped = False
        except OSError:
            stopped = False
    store = _load_store()
    store.pop("runtime", None)
    _save_store(store)
    return {"ok": True, "stopped": stopped, "pid": pid}


def run_model_pull(*, req_id: str, tag: str, port: int = 11434, sync: bool = False) -> dict[str, Any]:
    """Pull a model via `ollama pull <tag>`, streaming % progress into the record.

    Sets the record to ``downloading`` immediately so it leaves the approval inbox;
    on success flips it to ``served`` (which registers the chat catalog entry); on
    failure returns it to ``pending_approval`` with an error so the operator retries.
    """
    update_serve_request(req_id, status="downloading", phase="downloading", progress=0, error=None)

    def _worker() -> None:
        try:
            proc = subprocess.Popen(  # noqa: S603,S607 - fixed argv, loopback only
                ["ollama", "pull", tag],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=_ollama_env(port),
                text=True,
                bufsize=1,
            )
        except Exception as exc:  # pragma: no cover - environment dependent
            update_serve_request(
                req_id, status="pending_approval", phase="error", error=f"pull_start_failed: {exc}"
            )
            return
        last = -1
        if proc.stdout is not None:
            for line in proc.stdout:
                matches = _PCT_RE.findall(line)
                if matches:
                    pct = int(matches[-1])
                    if 0 <= pct <= 100 and pct != last:
                        last = pct
                        update_serve_request(req_id, phase="downloading", progress=pct)
        code = proc.wait()
        if code == 0:
            update_serve_request(
                req_id,
                status="served",
                executed=True,
                served=True,
                served_at=time.time(),
                endpoint=f"http://127.0.0.1:{int(port)}",
                phase="served",
                progress=100,
                error=None,
            )
        else:
            update_serve_request(
                req_id, status="pending_approval", phase="error", error=f"pull_exit_{code}"
            )

    if sync:
        _worker()
    else:
        threading.Thread(target=_worker, daemon=True).start()
    return {"ok": True, "tag": tag, "async": not sync}


def clear_foundry_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
