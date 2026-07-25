# SPDX-License-Identifier: Apache-2.0
"""FIX 128 — cross-lane correlation identifiers."""

from __future__ import annotations

import hashlib


def derive_correlation_id(*, session_id: str, plan_id: str = "") -> str:
    raw = f"mcv1:{session_id}:{plan_id}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"mc-{digest}"
