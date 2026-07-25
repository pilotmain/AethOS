# SPDX-License-Identifier: Apache-2.0
"""Ephemeral browser evidence capture session timeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import time
from typing import Any


@dataclass
class BrowserEvidenceSession:
    session_id: str
    source_url: str
    capture_type: str
    started_at: float = field(default_factory=time)
    events: list[dict[str, Any]] = field(default_factory=list)
    artifact_ids: list[str] = field(default_factory=list)

    def record(self, event: str, *, detail: str | None = None) -> None:
        self.events.append({"at": time(), "event": event, "detail": detail})

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "source_url": self.source_url,
            "capture_type": self.capture_type,
            "started_at": self.started_at,
            "events": list(self.events),
            "artifact_ids": list(self.artifact_ids),
        }
