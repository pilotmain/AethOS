# SPDX-License-Identifier: Apache-2.0

from aethos_core.providers.base.readonly_execution_adapter import ReadonlyExecutionAdapter
from aethos_core.providers.vercel.operations.readonly_execution import VercelReadonlyExecutionAdapter


def test_readonly_execution_adapter_contract_methods():
    required = {
        "get_deployments",
        "get_domains",
        "get_project_details",
        "get_deployment_logs",
    }
    assert required.issubset(set(ReadonlyExecutionAdapter.__abstractmethods__))


def test_vercel_adapter_exposes_all_contract_methods():
    adapter = VercelReadonlyExecutionAdapter("token")
    for name in ("get_deployments", "get_domains", "get_project_details", "get_deployment_logs"):
        assert callable(getattr(adapter, name))
