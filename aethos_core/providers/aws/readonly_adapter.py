# SPDX-License-Identifier: Apache-2.0
"""AWS readonly adapter — identity validation and inventory (no mutations)."""

from __future__ import annotations

from typing import Any


def run_aws_readonly_health_report(*, credential_id: str | None = None) -> dict[str, Any]:
    """Readonly health report — returns structured not-configured until boto3 wiring lands."""
    if not credential_id:
        return {
            "ok": False,
            "phase": "readonly_first",
            "detail": "AWS credential not configured.",
            "supported_readonly_ops": [
                "validate_identity",
                "list_regions",
                "list_ecs_services",
                "list_lambda_functions",
                "list_api_gateway_apis",
                "list_cloudwatch_log_groups",
            ],
        }
    return {
        "ok": False,
        "phase": "readonly_first",
        "detail": "AWS readonly boto3 adapters are scoped — credential detected but live inventory not wired in this build.",
        "credential_id": credential_id,
        "next": "See docs/AWS_READONLY_IMPLEMENTATION_PLAN.md",
    }
