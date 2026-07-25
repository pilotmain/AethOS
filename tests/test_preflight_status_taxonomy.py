# SPDX-License-Identifier: Apache-2.0

from aethos_core.operations.local_preflight import build_local_preflight
from aethos_core.operations.operation_models import OperationPreflight
from aethos_core.operations.preflight_status import derive_preflight_status


def test_local_preflight_ready_for_approval():
    pf = build_local_preflight(operation_type="local_workspace_fix", user_request="check local")
    pf.preflight_status = derive_preflight_status(pf)
    assert pf.preflight_status == "ready_for_approval"


def test_env_preflight_needs_information():
    pf = OperationPreflight(
        provider="vercel",
        operation_type="set_env_var",
        target_name="quotepilot",
        target_status="resolved",
        missing_information=["exact_env_value_confirmation", "environment_target"],
    )
    assert derive_preflight_status(pf) == "needs_information"


def test_logs_preflight_readonly_diagnostic():
    pf = OperationPreflight(
        provider="vercel",
        operation_type="check_logs",
        target_name="quotepilot",
        target_status="resolved",
    )
    assert derive_preflight_status(pf) == "ready_for_readonly_diagnostic"
