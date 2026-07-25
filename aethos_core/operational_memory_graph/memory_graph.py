# SPDX-License-Identifier: Apache-2.0
"""Long-horizon operational memory graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aethos_core.operational_cognition.cognition_memory_bridge import CognitionMemoryContext, load_cognition_memory


@dataclass
class OperationalMemoryGraph:
    short_term: CognitionMemoryContext
    session: dict[str, Any] = field(default_factory=dict)
    infrastructure: dict[str, Any] = field(default_factory=dict)
    historical: list[dict[str, Any]] = field(default_factory=list)
    learned_repairs: list[dict[str, Any]] = field(default_factory=list)
    user_preferences: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "short_term": self.short_term.to_dict(),
            "session": dict(self.session),
            "infrastructure": dict(self.infrastructure),
            "historical": list(self.historical),
            "learned_repairs": list(self.learned_repairs),
            "user_preferences": dict(self.user_preferences),
        }


def load_operational_memory_graph(*, session_id: str = "default") -> OperationalMemoryGraph:
    short_term = load_cognition_memory(session_id=session_id)
    session: dict[str, Any] = {
        "session_id": session_id,
        "has_render_context": short_term.has_render_context,
        "last_output_format": short_term.last_output_format,
        "last_filter_mode": short_term.last_filter_mode,
    }
    infrastructure: dict[str, Any] = {}
    if short_term.has_provider_wide_health:
        infrastructure = {
            "provider": short_term.health_provider,
            "summary": dict(short_term.health_summary),
            "failed_service_count": short_term.failed_service_count,
        }

    from aethos_core.chat.route_trace import get_last_route_trace

    trace = get_last_route_trace(session_id=session_id)
    if trace:
        session["last_route_trace"] = trace

    return OperationalMemoryGraph(
        short_term=short_term,
        session=session,
        infrastructure=infrastructure,
        user_preferences={
            "verbosity": "adaptive",
            "output_format": short_term.last_output_format or "summary",
            "filter_mode": short_term.last_filter_mode or "all",
        },
    )
