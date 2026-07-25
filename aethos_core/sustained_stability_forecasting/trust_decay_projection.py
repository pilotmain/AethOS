# SPDX-License-Identifier: Apache-2.0
"""Trust decay projection — operational trust evolution."""

from __future__ import annotations

from typing import Any

from aethos_core.sustained_trust_evolution.fragility_decay import assess_fragility_decay


def project_trust_decay() -> dict[str, Any]:
    return assess_fragility_decay()
