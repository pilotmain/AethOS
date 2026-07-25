# SPDX-License-Identifier: Apache-2.0
"""Failed-service investigation runtime."""

from __future__ import annotations

from aethos_core.failed_service_investigation.failed_service_router import (
    compose_failed_service_investigation_reply,
    failed_service_router_can_handle,
    should_block_generic_diagnostics,
    should_preempt_to_failed_service,
)
from aethos_core.failed_service_investigation.global_preemption import (
    detect_failed_service_reference,
    route_failed_service_intent,
)

__all__ = [
    "compose_failed_service_investigation_reply",
    "detect_failed_service_reference",
    "failed_service_router_can_handle",
    "route_failed_service_intent",
    "should_block_generic_diagnostics",
    "should_preempt_to_failed_service",
]
