# SPDX-License-Identifier: Apache-2.0
"""Trust controls — transparent, deletable operator memory."""

from __future__ import annotations

from typing import Any


def get_trust_controls(*, session_id: str = "default") -> dict[str, Any]:
    """What AethOS remembers and how the operator can control it."""
    from aethos_core.human_centered.continuity_memory import get_continuity_transparency
    from aethos_core.personal_intelligence.personal_runtime import get_personal_intelligence_status

    continuity = get_continuity_transparency(session_id=session_id)
    personal = get_personal_intelligence_status(session_id=session_id)

    return {
        "ok": True,
        "phase": "10.1.2",
        "continuity_memory": continuity,
        "personal_intelligence": {
            "opted_in": personal.get("opted_in"),
            "governance": personal.get("governance"),
        },
        "controls": {
            "delete_continuity_memory": True,
            "delete_personal_intelligence": True,
            "view_explainability": True,
            "no_hidden_retention": True,
        },
        "principle": "All personal and continuity memory is opt-in explainable, deletable, and locally controllable.",
        "autonomous_execution_blocked": True,
    }


def delete_all_operator_memory(*, session_id: str = "default") -> dict[str, Any]:
    """Delete continuity + personal memory — operator controlled."""
    from aethos_core.conversation.conversation_runtime import _session_path, _goals_path
    from aethos_core.conversation.operational_memory import delete_operational_memory
    from aethos_core.human_centered.continuity_memory import delete_continuity_memory
    from aethos_core.personal_intelligence.personal_runtime import delete_personal_intelligence

    delete_continuity_memory(session_id=session_id)
    delete_personal_intelligence(session_id=session_id)
    delete_operational_memory(session_id=session_id)
    for p in (_session_path(session_id), _goals_path(session_id)):
        if p.is_file():
            p.unlink()
    return {
        "ok": True,
        "deleted": ["continuity_memory", "personal_intelligence", "operational_memory", "conversation_threads"],
        "session_id": session_id,
    }
