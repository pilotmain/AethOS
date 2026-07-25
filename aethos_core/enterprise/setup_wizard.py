# SPDX-License-Identifier: Apache-2.0
"""First-run setup wizard state."""

from __future__ import annotations

import json
from time import time
from typing import Any

from aethos_core.enterprise.paths import enterprise_root

_STEPS = [
    {"id": "telegram", "title": "Connect Telegram", "doc": "docs/TELEGRAM_SETUP.md"},
    {"id": "tunnel", "title": "Configure tunnel", "doc": "docs/TELEGRAM_SETUP.md"},
    {"id": "providers", "title": "Add providers", "doc": "docs/PROVIDER_CREDENTIALS.md"},
    {"id": "research", "title": "Enable research", "doc": "docs/RESEARCH_SETUP.md"},
    {"id": "browser", "title": "Test browser evidence", "doc": "docs/GETTING_STARTED.md"},
    {"id": "workspace", "title": "Register workspace", "doc": "docs/LOCAL_DEVELOPMENT.md"},
    {"id": "operational_check", "title": "Run first operational check", "doc": "docs/DEMO_SCRIPT.md"},
]


def build_setup_wizard() -> dict[str, Any]:
    """Guide users through first-run setup — observational progress."""
    from aethos_core.channels.telegram.telegram_runtime import telegram_configured
    from aethos_core.config import get_settings
    from aethos_core.enterprise.doctor import run_doctor_checks
    from aethos_core.research.research_config import is_research_search_configured
    from aethos_core.runtime.browser_capability import get_browser_capability_status
    from aethos_core.runtime.tunnel.tunnel_manager import tunnel_status
    from aethos_core.runtime.workspace_diagnostics import get_workspace_diagnostics

    s = get_settings()
    ws = get_workspace_diagnostics()

    step_status = {
        "telegram": telegram_configured() if s.telegram_enabled else s.telegram_enabled is False,
        "tunnel": (not s.telegram_tunnel_enabled) or bool((tunnel_status() or {}).get("running")),
        "providers": s.use_real_llm and bool(s.anthropic_api_key.strip()),
        "research": is_research_search_configured() if s.web_research_enabled else not s.web_research_enabled,
        "browser": (
            (not s.browser_automation_enabled)
            or bool(get_browser_capability_status(probe_launch=False).get("execution_ready"))
        ),
        "workspace": bool(ws.get("canonical_path")),
        "operational_check": run_doctor_checks(probe_api=False).get("overall") != "FAIL",
    }

    steps = []
    completed = 0
    for step in _STEPS:
        done = bool(step_status.get(step["id"]))
        if done:
            completed += 1
        steps.append({**step, "completed": done, "status": "done" if done else "pending"})

    progress = round(completed / max(len(_STEPS), 1), 2)
    _save_progress(progress, completed)

    return {
        "ok": True,
        "steps": steps,
        "progress": progress,
        "completed_count": completed,
        "total_steps": len(_STEPS),
        "complete": completed == len(_STEPS),
        "next_step": next((s for s in steps if not s["completed"]), None),
    }


def _save_progress(progress: float, completed: int) -> None:
    path = enterprise_root() / "setup_progress.json"
    path.write_text(
        json.dumps({"progress": progress, "completed": completed, "at": time()}, indent=2),
        encoding="utf-8",
    )
