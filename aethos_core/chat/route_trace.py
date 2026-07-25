# SPDX-License-Identifier: Apache-2.0
"""Route trace storage and internal routing diagnostics (canonical home post-§D2)."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_INTERNAL_SIGNAL_RX = re.compile(
    r"\b("
    r"route[_\s-]?trace|routing\s+(?:metadata|diagnostics|trace)|"
    r"api\s+meta|response\s+meta|"
    r"which\s+route\s+won|matched_module|blocked_routes|"
    r"internal\s+(?:routing\s+)?diagnostics|"
    r"route_id"
    r")\b",
    re.I,
)

_INTERNAL_META_LOGS_RX = re.compile(
    r"\b(check|show|get|inspect|read|what\s+is)\b.*\b(meta|route|routing)\b",
    re.I,
)

_EXPLICIT_PROVIDER_LOGS_RX = re.compile(
    r"\b(vercel|railway|github|deployment|service)\b.*\blogs?\b|"
    r"\blogs?\b.*\b(for|of|from)\b.*\b(vercel|railway|github|[a-z0-9][a-z0-9-]{1,62})\b|"
    r"\bcheck\s+vercel\s+logs?\b",
    re.I,
)

_TRACE_STORE: dict[str, dict[str, Any]] = {}


def _scoped_session_id(session_id: str) -> str:
    """Namespace route traces per tenant when multi-tenant is enabled."""
    sid = (session_id or "default").strip()[:128]
    from aethos_core.config import get_settings

    if get_settings().multi_tenant_enabled:
        from aethos_core.tenancy import get_current_tenant

        return f"{get_current_tenant()}::{sid}"
    return sid


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "internal_diagnostics"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = _scoped_session_id(session_id).replace("/", "_").replace(":", "_")[:160]
    return _store_dir() / f"{safe}_route_trace.json"


def is_internal_diagnostics_query(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False

    has_internal_signal = bool(_INTERNAL_SIGNAL_RX.search(raw))
    has_meta_route_ask = bool(_INTERNAL_META_LOGS_RX.search(raw)) and bool(
        re.search(r"route[_\s-]?trace|route_id|matched_module|blocked_routes|api\s+meta|response\s+meta", raw, re.I)
    )
    if not has_internal_signal and not has_meta_route_ask:
        return False

    if _EXPLICIT_PROVIDER_LOGS_RX.search(raw):
        if re.search(r"route[_\s-]?trace|api\s+meta|response\s+meta|route_id|matched_module", raw, re.I):
            return True
        return False

    return True


def save_last_route_trace(
    *,
    session_id: str,
    meta: dict[str, str] | dict[str, Any],
    intent: str = "",
) -> None:
    session_id = _scoped_session_id(session_id)
    payload = {
        "route_id": str(meta.get("route_id") or ""),
        "matched_module": str(meta.get("matched_module") or ""),
        "matched_target": str(meta.get("matched_target") or ""),
        "blocked_routes": str(meta.get("blocked_routes") or ""),
        "route_trace": str(meta.get("route_trace") or ""),
        "intent": intent or str(meta.get("intent") or ""),
        "recorded_at": datetime.now(UTC).isoformat(),
        "workflow_discovery_delegated": str(meta.get("workflow_discovery_delegated") or ""),
        "delegated_handler": str(meta.get("delegated_handler") or ""),
        "workflow_discovery_proposal_forced": str(meta.get("workflow_discovery_proposal_forced") or ""),
        "workflow_discovery_delegation_executed": str(meta.get("workflow_discovery_delegation_executed") or ""),
        "blocked_handlers": str(meta.get("blocked_handlers") or ""),
        "workflow_lane_stage": str(meta.get("workflow_lane_stage") or ""),
    }
    for extra_key in ("fallback_used", "recovered", "world_model_intent", "cognition_diagnostic_id"):
        if meta.get(extra_key) is not None:
            payload[extra_key] = str(meta.get(extra_key))
    from aethos_core.chat.route_timing import timing_for_route_trace

    payload.update(timing_for_route_trace())
    _TRACE_STORE[session_id] = payload
    try:
        _session_path(session_id).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    except OSError:
        pass


def get_last_route_trace(*, session_id: str = "default") -> dict[str, Any] | None:
    session_id = _scoped_session_id(session_id)
    cached = _TRACE_STORE.get(session_id)
    if cached is None:
        path = _session_path(session_id)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached = raw
                    _TRACE_STORE[session_id] = raw
            except (OSError, json.JSONDecodeError):
                return None
    if not cached:
        return None
    if not any(str(cached.get(key) or "") for key in ("route_id", "route_trace", "matched_module")):
        return None
    return dict(cached)


def clear_route_traces_for_tests() -> None:
    _TRACE_STORE.clear()
    root = _store_dir()
    for path in root.glob("*_route_trace.json"):
        path.unlink(missing_ok=True)


def compose_internal_route_trace_reply(
    text: str,
    *,
    session_id: str = "default",
) -> tuple[str, str, dict[str, str]] | None:
    if not is_internal_diagnostics_query(text):
        return None

    trace = get_last_route_trace(session_id=session_id)
    lines = [
        "I'll check AethOS internal routing diagnostics for the last response.",
        "",
    ]

    if trace:
        lines.append("Latest route trace:")
        if trace.get("route_id"):
            lines.append(f"- route_id: **{trace['route_id']}**")
        if trace.get("matched_module"):
            lines.append(f"- matched_module: `{trace['matched_module']}`")
        if trace.get("matched_target"):
            lines.append(f"- matched_target: **{trace['matched_target']}**")
        if trace.get("blocked_routes"):
            blocked = str(trace["blocked_routes"]).replace(",", ", ")
            lines.append(f"- blocked_routes: {blocked}")
        if trace.get("route_trace"):
            lines.append(f"- route_trace: `{trace['route_trace']}`")
        if trace.get("intent"):
            lines.append(f"- intent: `{trace['intent']}`")
        if trace.get("workflow_discovery_delegated"):
            lines.append(f"- workflow_discovery_delegated: **{trace['workflow_discovery_delegated']}**")
        if trace.get("delegated_handler"):
            lines.append(f"- delegated_handler: **{trace['delegated_handler']}**")
        if trace.get("workflow_discovery_proposal_forced"):
            lines.append(f"- workflow_discovery_proposal_forced: **{trace['workflow_discovery_proposal_forced']}**")
        if trace.get("workflow_discovery_delegation_executed"):
            lines.append(f"- workflow_discovery_delegation_executed: **{trace['workflow_discovery_delegation_executed']}**")
        if trace.get("blocked_handlers"):
            lines.append(f"- blocked_handlers: {trace['blocked_handlers']}")
        if trace.get("workflow_lane_stage"):
            lines.append(f"- workflow_lane_stage: **{trace['workflow_lane_stage']}**")
        if trace.get("recorded_at"):
            lines.append(f"- recorded_at: `{trace['recorded_at']}`")
    else:
        lines.extend(
            [
                "I don't have route_trace metadata attached to the last response in this session yet.",
                "",
                "Next step:",
                "Run an operational query first (for example **check all services in railway**, then "
                "**why is MongoDB failed?**), then ask again — or inspect API response meta for `route_trace`.",
            ]
        )

    meta = {
        "scope": "internal_diagnostics",
        "diagnostic_type": "route_trace",
        "has_trace": "true" if trace else "false",
    }
    return "\n".join(lines), "internal_route_trace_diagnostics", meta
