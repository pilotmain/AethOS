# SPDX-License-Identifier: Apache-2.0
"""Canonical operational runtime state."""

from aethos_core.operational_state.narrative import compose_narrative_continuity_reply
from aethos_core.operational_state.state import OperationalState, load_operational_state, update_operational_state

__all__ = [
    "OperationalState",
    "compose_narrative_continuity_reply",
    "load_operational_state",
    "update_operational_state",
]
