# SPDX-License-Identifier: Apache-2.0
"""Runtime survivability projection — long-tail survivability."""

from __future__ import annotations

from typing import Any

from aethos_core.runtime_survivability_intelligence.runtime_survivability_projection import project_runtime_survivability


def project_long_tail_runtime_survivability() -> dict[str, Any]:
    return project_runtime_survivability()
