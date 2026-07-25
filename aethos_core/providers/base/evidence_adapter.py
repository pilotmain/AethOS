# SPDX-License-Identifier: Apache-2.0
"""Evidence item contract — shared shape for execution artifacts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceItem:
    source: str
    type: str
    confidence: str = "possible"
    message: str = ""
    tier: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "source": self.source,
            "type": self.type,
            "confidence": self.confidence,
            "message": self.message,
        }
        if self.tier:
            out["tier"] = self.tier
        out.update(self.extra)
        return out

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> EvidenceItem:
        known = {"source", "type", "confidence", "message", "tier"}
        extra = {k: v for k, v in raw.items() if k not in known}
        return cls(
            source=str(raw.get("source") or "unknown"),
            type=str(raw.get("type") or "signal"),
            confidence=str(raw.get("confidence") or "possible"),
            message=str(raw.get("message") or ""),
            tier=str(raw["tier"]) if raw.get("tier") else None,
            extra=extra,
        )
