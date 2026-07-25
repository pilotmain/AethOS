# SPDX-License-Identifier: Apache-2.0
"""Guard destructive test cleanup from wiping operator delivery data."""

from __future__ import annotations

import os


def tests_may_clear_persisted_data() -> bool:
    return os.environ.get("AETHOS_CERTIFICATION_MODE", "").lower() in {"1", "true", "yes"}
