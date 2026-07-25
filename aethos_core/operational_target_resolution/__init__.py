# SPDX-License-Identifier: Apache-2.0
"""Explicit operational target resolution (layered routing)."""

from aethos_core.operational_target_resolution.explicit_target_resolver import (
    ExplicitOperationalTarget,
    explicit_target_overrides_session_context,
    resolve_explicit_operational_target,
    should_route_explicit_provider_diagnostics,
)

__all__ = [
    "ExplicitOperationalTarget",
    "explicit_target_overrides_session_context",
    "resolve_explicit_operational_target",
    "should_route_explicit_provider_diagnostics",
]
