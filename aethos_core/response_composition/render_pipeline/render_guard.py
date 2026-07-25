# SPDX-License-Identifier: Apache-2.0
"""Guard renderers against mutation and impure side effects."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aethos_core.response_composition.render_pipeline.immutable_result_snapshot import (
    ImmutableSnapshotError,
    _GuardedPayload,
)


def guarded_render(
    renderer: Callable[..., str],
    payload: dict[str, Any],
    *,
    payload_hash: str,
    **kwargs: Any,
) -> str:
    guarded = _GuardedPayload(payload, payload_hash)
    output = renderer(payload=guarded, **kwargs)
    guarded.verify_unchanged()
    if not isinstance(output, str):
        raise ImmutableSnapshotError(f"Renderer returned non-string output: {type(output)!r}")
    return output
