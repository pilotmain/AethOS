# SPDX-License-Identifier: Apache-2.0
"""Operator persona — first-run rapport profile (local-only personalization).

Stores what AethOS learns about the operator during first-run onboarding so it
can address them by name, respect their working hours, and match their tone.
Local JSON only — never sent to third parties.
"""

from __future__ import annotations

import json
from pathlib import Path
from time import time
from typing import Any

from aethos_core.config import get_settings

_VALID_TONES = ("warm", "concise", "direct", "playful")


def _store_path() -> Path:
    s = get_settings()
    base = Path(getattr(s, "operator_persona_store_dir", "data/operator_persona"))
    if not base.is_absolute():
        base = Path.cwd() / base
    base.mkdir(parents=True, exist_ok=True)
    return base / "persona.json"


def _empty() -> dict[str, Any]:
    return {
        "name": "",
        "timezone": "",
        "work_start_hour": None,
        "work_end_hour": None,
        "tone": "warm",
        "goals": [],
        "first_run_complete": False,
        "updated_at": None,
    }


def _tenant_persona_record() -> dict[str, Any] | None:
    from aethos_core.config import get_settings

    if not get_settings().multi_tenant_enabled:
        return None
    from aethos_core.tenancy.tenant_data_store import get_record

    data = get_record("operator_persona", "default")
    return data if isinstance(data, dict) else None


def get_persona() -> dict[str, Any]:
    tenant_row = _tenant_persona_record()
    if tenant_row is not None:
        base = _empty()
        base.update({k: v for k, v in tenant_row.items() if k in base})
        return base
    path = _store_path()
    if not path.is_file():
        return _empty()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    base = _empty()
    base.update({k: v for k, v in data.items() if k in base})
    return base


def _coerce_hour(value: Any) -> int | None:
    try:
        h = int(value)
    except (TypeError, ValueError):
        return None
    if 0 <= h <= 23:
        return h
    return None


def save_persona(
    *,
    name: str | None = None,
    timezone: str | None = None,
    work_start_hour: Any = None,
    work_end_hour: Any = None,
    tone: str | None = None,
    goals: list[str] | None = None,
    first_run_complete: bool | None = None,
) -> dict[str, Any]:
    persona = get_persona()
    if name is not None:
        persona["name"] = str(name).strip()[:80]
    if timezone is not None:
        persona["timezone"] = str(timezone).strip()[:64]
    if work_start_hour is not None:
        persona["work_start_hour"] = _coerce_hour(work_start_hour)
    if work_end_hour is not None:
        persona["work_end_hour"] = _coerce_hour(work_end_hour)
    if tone is not None:
        t = str(tone).strip().lower()
        persona["tone"] = t if t in _VALID_TONES else "warm"
    if goals is not None:
        persona["goals"] = [str(g).strip()[:140] for g in goals if str(g).strip()][:8]
    if first_run_complete is not None:
        persona["first_run_complete"] = bool(first_run_complete)
    persona["updated_at"] = time()
    from aethos_core.config import get_settings

    if get_settings().multi_tenant_enabled:
        from aethos_core.tenancy.tenant_data_store import set_record

        set_record("operator_persona", "default", persona)
    path = _store_path()
    path.write_text(json.dumps(persona, indent=2), encoding="utf-8")
    return persona


def persona_greeting_name() -> str:
    """First name for greetings, or empty string."""
    name = (get_persona().get("name") or "").strip()
    return name.split()[0] if name else ""


def reset_persona_for_tests() -> None:
    path = _store_path()
    if path.is_file():
        path.unlink()
