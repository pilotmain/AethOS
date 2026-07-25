# SPDX-License-Identifier: Apache-2.0
"""Immutable operational result snapshots."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from typing import Any


class ImmutableSnapshotError(RuntimeError):
    """Raised when a renderer attempts to mutate a frozen snapshot."""


@dataclass(frozen=True)
class ImmutableResultSnapshot:
    payload: dict[str, Any]
    payload_hash: str

    @classmethod
    def freeze(cls, payload: dict[str, Any]) -> ImmutableResultSnapshot:
        frozen = copy.deepcopy(payload)
        payload_hash = _hash_payload(frozen)
        return cls(payload=frozen, payload_hash=payload_hash)

    def view(self) -> dict[str, Any]:
        """Return a deep copy for read-only rendering."""
        return copy.deepcopy(self.payload)

    def guarded_view(self) -> _GuardedPayload:
        return _GuardedPayload(self.view(), self.payload_hash)


def _hash_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


class _GuardedPayload(dict):
    """Dict wrapper that rejects mutation during render."""

    def __init__(self, data: dict[str, Any], payload_hash: str) -> None:
        super().__init__(data)
        self._payload_hash = payload_hash
        self._frozen = copy.deepcopy(data)

    def __setitem__(self, key: Any, value: Any) -> None:
        raise ImmutableSnapshotError(f"Renderer attempted to mutate immutable snapshot (key={key!r})")

    def __delitem__(self, key: Any) -> None:
        raise ImmutableSnapshotError(f"Renderer attempted to delete from immutable snapshot (key={key!r})")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise ImmutableSnapshotError("Renderer attempted to update immutable snapshot")

    def pop(self, *args: Any, **kwargs: Any) -> Any:
        raise ImmutableSnapshotError("Renderer attempted to pop from immutable snapshot")

    def popitem(self) -> tuple[Any, Any]:
        raise ImmutableSnapshotError("Renderer attempted to popitem from immutable snapshot")

    def clear(self) -> None:
        raise ImmutableSnapshotError("Renderer attempted to clear immutable snapshot")

    def setdefault(self, key: Any, default: Any = None) -> Any:
        if key in self:
            return self[key]
        raise ImmutableSnapshotError(f"Renderer attempted setdefault on immutable snapshot (key={key!r})")

    def verify_unchanged(self) -> None:
        if _hash_payload(dict(self._frozen)) != self._payload_hash:
            raise ImmutableSnapshotError("Snapshot hash mismatch after render")
