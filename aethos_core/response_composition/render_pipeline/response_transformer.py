# SPDX-License-Identifier: Apache-2.0
"""Transform immutable snapshots into renderer-ready views."""

from __future__ import annotations

from typing import Any

from aethos_core.response_composition.render_pipeline.filter_engine import FilterMode, apply_filter
from aethos_core.response_composition.render_pipeline.immutable_result_snapshot import ImmutableResultSnapshot


def transform_snapshot(
    snapshot: ImmutableResultSnapshot,
    *,
    filter_mode: FilterMode = "all",
) -> dict[str, Any]:
    return apply_filter(snapshot.view(), filter_mode)
