# SPDX-License-Identifier: Apache-2.0
"""Trust decay projection — operational trust evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_stability_forecasting.trust_decay_projection import project_trust_decay


def project_operational_trust_decay() -> dict[str, Any]:
    return project_trust_decay()
