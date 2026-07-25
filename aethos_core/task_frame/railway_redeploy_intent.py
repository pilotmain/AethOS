# SPDX-License-Identifier: Apache-2.0
"""Session memory for in-progress Railway redeploy conversations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

_MEMORY: dict[str, "RailwayRedeployIntent"] = {}
DEFAULT_TTL_HOURS = 2

_REDEPLOY_RX = re.compile(
    r"\b("
    r"re-?deploy(?:ing|ment)?"
    r"|re[\s-]?trigger(?:\s+(?:the\s+)?deployment)?"
    r"|trigger(?:\s+(?:the\s+)?)?deployment"
    r"|latest\s+(?:git\s+)?changes"
    r"|new\s+changes\s+in\s+git"
    r")\b",
    re.I,
)
_RAILWAY_RX = re.compile(r"\b(?:railway|rail\s*way)\b", re.I)
_AETHOS_RX = re.compile(r"\baethos\b", re.I)
_ENV_ONLY_RX = re.compile(
    r"^\s*(?:let(?:'|)s\s+do\s+|use\s+|on\s+|do\s+)?(staging|stage|production|prod)\s*\.?\s*$",
    re.I,
)
_RETRIGGER_RX = re.compile(
    r"\b("
    r"(?:re[\s-]?trigger|trigger)\s+(?:the\s+)?deployment"
    r"|can you\s+(?:re[\s-]?trigger|trigger)"
    r"|please\s+(?:re[\s-]?trigger|trigger)"
    r")\b",
    re.I,
)


@dataclass
class RailwayRedeployIntent:
    session_id: str
    original_request: str
    operation: str = "redeploy"
    environment: str = ""
    project_hint: str = "pilotos"
    service_hints: list[str] = field(default_factory=list)
    created_at: str = ""
    expires_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "original_request": self.original_request,
            "operation": self.operation,
            "environment": self.environment,
            "project_hint": self.project_hint,
            "service_hints": list(self.service_hints),
            "created_at": self.created_at,
            "expires_at": self.expires_at,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> RailwayRedeployIntent:
        return cls(
            session_id=str(raw.get("session_id") or ""),
            original_request=str(raw.get("original_request") or ""),
            operation=str(raw.get("operation") or "redeploy"),
            environment=str(raw.get("environment") or ""),
            project_hint=str(raw.get("project_hint") or "pilotos"),
            service_hints=[str(item) for item in (raw.get("service_hints") or []) if str(item).strip()],
            created_at=str(raw.get("created_at") or ""),
            expires_at=str(raw.get("expires_at") or ""),
        )


def is_railway_redeploy_followup(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    if is_environment_only_reply(raw):
        return True
    if _RETRIGGER_RX.search(raw):
        return True
    if _REDEPLOY_RX.search(raw):
        return True
    return False


def is_environment_only_reply(text: str) -> bool:
    return bool(_ENV_ONLY_RX.match((text or "").strip()))


def parse_environment_only_reply(text: str) -> str:
    match = _ENV_ONLY_RX.match((text or "").strip())
    if not match:
        return ""
    from aethos_core.providers.railway.railway_inventory_target_picker import normalize_environment

    return normalize_environment(match.group(1))


def mentions_railway_redeploy_context(text: str) -> bool:
    raw = (text or "").strip()
    if not raw:
        return False
    has_railway = bool(_RAILWAY_RX.search(raw))
    has_aethos = bool(_AETHOS_RX.search(raw))
    has_redeploy = bool(_REDEPLOY_RX.search(raw) or _RETRIGGER_RX.search(raw))
    if has_redeploy and (has_railway or has_aethos):
        return True
    if _RETRIGGER_RX.search(raw):
        return True
    return False


def _store_dir() -> Path:
    root = Path(__file__).resolve().parents[2] / "data" / "railway_redeploy_intents"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _session_path(session_id: str) -> Path:
    safe = (session_id or "default").strip().replace("/", "_")[:128]
    return _store_dir() / f"{safe}.json"


def _expires_at(hours: int = DEFAULT_TTL_HOURS) -> str:
    return (datetime.now(UTC) + timedelta(hours=hours)).isoformat()


def save_railway_redeploy_intent(intent: RailwayRedeployIntent) -> RailwayRedeployIntent:
    intent.created_at = intent.created_at or datetime.now(UTC).isoformat()
    intent.expires_at = intent.expires_at or _expires_at()
    _MEMORY[intent.session_id] = intent
    _session_path(intent.session_id).write_text(json.dumps(intent.to_dict(), indent=2), encoding="utf-8")
    return intent


def get_railway_redeploy_intent(*, session_id: str) -> RailwayRedeployIntent | None:
    session_id = (session_id or "default").strip()
    cached = _MEMORY.get(session_id)
    if cached is None:
        path = _session_path(session_id)
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    cached = RailwayRedeployIntent.from_dict(raw)
                    _MEMORY[session_id] = cached
            except (OSError, json.JSONDecodeError):
                return None
    if cached is None:
        return None
    if cached.expires_at:
        try:
            deadline = datetime.fromisoformat(cached.expires_at.replace("Z", "+00:00"))
            if deadline.tzinfo is None:
                deadline = deadline.replace(tzinfo=UTC)
            if datetime.now(UTC) >= deadline:
                clear_railway_redeploy_intent(session_id=session_id)
                return None
        except ValueError:
            pass
    # §1 — tighter conversational TTL: an abandoned redeploy frame expires after a
    # few minutes so it can never hijack a later, unrelated turn.
    from aethos_core.task_frame.continuation_ttl import is_frame_conversationally_stale

    if is_frame_conversationally_stale(cached.created_at):
        clear_railway_redeploy_intent(session_id=session_id)
        return None
    return cached


def clear_railway_redeploy_intent(*, session_id: str) -> None:
    session_id = (session_id or "default").strip()
    _MEMORY.pop(session_id, None)
    path = _session_path(session_id)
    if path.is_file():
        path.unlink()


def clear_railway_redeploy_intents_for_tests() -> None:
    _MEMORY.clear()
    root = _store_dir()
    for path in root.glob("*.json"):
        path.unlink()
