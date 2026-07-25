# SPDX-License-Identifier: Apache-2.0
"""Store retry preflight offer after binding correction."""

from __future__ import annotations

from aethos_core.task_frame.pending_action import offer_retry_preflight_action


def offer_retry_after_binding_update(
    *,
    session_id: str,
    provider: str,
    project: str,
    environment: str,
    service: str,
    operation: str = "restart",
    source_binding: str | None = None,
) -> None:
    offer_retry_preflight_action(
        session_id=session_id,
        provider=provider,
        project=project,
        environment=environment,
        service=service,
        operation=operation,
        source_binding=source_binding,
    )
