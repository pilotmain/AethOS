# SPDX-License-Identifier: Apache-2.0
"""Emergency kill switch — blocks all live Railway greenfield mutations when active."""

from __future__ import annotations


def is_railway_mutation_kill_switch_active() -> bool:
    """
    When True, live mutation adapters must not call Railway APIs.

    Set `RAILWAY_GREENFIELD_MUTATION_KILL_SWITCH=true` for emergency stop.
    MC may also set runtime overrides via governance_override_store.
    """
    from aethos_core.governance.governance_override_store import effective_bool_flag

    return effective_bool_flag("railway_greenfield_mutation_kill_switch")
