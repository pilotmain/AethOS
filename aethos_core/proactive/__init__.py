# SPDX-License-Identifier: Apache-2.0
"""Proactive suggestions — AethOS notices things and proposes next actions (gated)."""

from aethos_core.proactive.suggestions import (
    dismiss_suggestion,
    generate_suggestions,
    latest_suggestions,
    run_proactive_scan,
)

__all__ = [
    "dismiss_suggestion",
    "generate_suggestions",
    "latest_suggestions",
    "run_proactive_scan",
]
